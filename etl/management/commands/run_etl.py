from __future__ import annotations

import hashlib
import io
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import (
    Carrier,
    Customer,
    OrderItem,
    Product,
    ProductReturn,
    SalesOrder,
    Shipment,
    Warehouse,
)
from etl.models import EtlReject, EtlRun, EtlSourceFile, EtlStagingRow
from etl.processing import RowValidationError, transform_record


SOURCE_COLUMNS = {
    "clientes": {"external_id", "name", "email", "region", "comuna", "created_at"},
    "productos": {"sku", "name", "category", "unit_cost", "unit_price", "active"},
    "bodegas": {"code", "name", "region"},
    "transportistas": {"name"},
    "pedidos": {
        "external_id",
        "customer_external_id",
        "status",
        "created_at",
        "paid_at",
        "destination_region",
    },
    "items": {
        "external_id",
        "order_external_id",
        "sku",
        "warehouse_code",
        "quantity",
        "unit_price",
        "unit_cost",
    },
    "despachos": {
        "order_external_id",
        "warehouse_code",
        "carrier_name",
        "shipped_at",
        "promised_at",
        "delivered_at",
        "status",
    },
    "devoluciones": {
        "external_id",
        "order_item_external_id",
        "quantity",
        "reason",
        "refund_amount",
        "created_at",
    },
}
SOURCE_KEYS = {
    "clientes": ("external_id",),
    "productos": ("sku",),
    "bodegas": ("code",),
    "transportistas": ("name",),
    "pedidos": ("external_id",),
    "items": ("external_id",),
    "despachos": ("order_external_id", "warehouse_code"),
    "devoluciones": ("external_id",),
}


def _source_key(entity: str, raw: dict[str, Any]) -> tuple[str, ...] | None:
    key = tuple(str(raw.get(field, "")).strip() for field in SOURCE_KEYS[entity])
    if entity in {"productos", "bodegas"}:
        key = tuple(value.upper() for value in key)
    elif entity == "despachos":
        key = (key[0], key[1].upper())
    return key if all(key) else None


def _bulk_upsert(
    model: type,
    objects: list[Any],
    key_fields: list[str],
    update_fields: list[str],
) -> None:
    if objects:
        if not update_fields:
            model.objects.bulk_create(objects, batch_size=500, ignore_conflicts=True)
            return
        model.objects.bulk_create(
            objects,
            batch_size=500,
            update_conflicts=True,
            unique_fields=key_fields,
            update_fields=update_fields,
        )


def _validation_context(entity: str) -> dict[str, Any]:
    if entity == "pedidos":
        return {"customers": set(Customer.objects.values_list("external_id", flat=True))}
    if entity == "items":
        return {
            "products": set(Product.objects.values_list("sku", flat=True)),
            "warehouses": set(Warehouse.objects.values_list("code", flat=True)),
            "orders": set(SalesOrder.objects.values_list("external_id", flat=True)),
        }
    if entity == "despachos":
        return {
            "warehouses": set(Warehouse.objects.values_list("code", flat=True)),
            "carriers": set(Carrier.objects.values_list("name", flat=True)),
            "orders": set(SalesOrder.objects.values_list("external_id", flat=True)),
        }
    if entity == "devoluciones":
        returned_quantities: dict[int, int] = defaultdict(int)
        for item_id, quantity in ProductReturn.objects.values_list(
            "order_item_id", "quantity"
        ):
            returned_quantities[item_id] += quantity
        return {
            "items": OrderItem.objects.in_bulk(field_name="external_id"),
            "returns": ProductReturn.objects.in_bulk(field_name="external_id"),
            "returned_quantities": returned_quantities,
        }
    return {}


def _validate_record(entity: str, row: dict[str, Any], context: dict[str, Any]) -> None:
    if entity == "pedidos":
        if row["customer_external_id"] not in context["customers"]:
            raise RowValidationError(
                "MISSING_REFERENCE",
                f"Cliente inexistente: {row['customer_external_id']!r}.",
            )
    elif entity == "items":
        if row["sku"] not in context["products"]:
            raise RowValidationError("SKU_UNKNOWN", f"SKU inexistente: {row['sku']!r}.")
        if (
            row["order_external_id"] not in context["orders"]
            or row["warehouse_code"] not in context["warehouses"]
        ):
            raise RowValidationError(
                "MISSING_REFERENCE",
                f"Pedido o bodega inexistente en ítem {row['external_id']!r}.",
            )
    elif entity == "despachos":
        if (
            row["order_external_id"] not in context["orders"]
            or row["warehouse_code"] not in context["warehouses"]
            or row["carrier_name"] not in context["carriers"]
        ):
            raise RowValidationError(
                "MISSING_REFERENCE",
                "Pedido, bodega o transportista inexistente en el despacho.",
            )
    elif entity == "devoluciones":
        item = context["items"].get(row["order_item_external_id"])
        if item is None:
            raise RowValidationError(
                "MISSING_REFERENCE",
                f"Ítem inexistente: {row['order_item_external_id']!r}.",
            )
        old_return = context["returns"].get(row["external_id"])
        quantities = context["returned_quantities"]
        if old_return:
            quantities[old_return.order_item_id] -= old_return.quantity
        if quantities[item.pk] + row["quantity"] > item.quantity:
            if old_return:
                quantities[old_return.order_item_id] += old_return.quantity
            raise RowValidationError(
                "RETURN_EXCEEDS_SOLD",
                f"La devolución {row['external_id']!r} supera la cantidad vendida.",
            )
        quantities[item.pk] += row["quantity"]


def _load_records(entity: str, records: list[dict[str, Any]]) -> int:
    if entity == "clientes":
        objects = [Customer(**row) for row in records]
        _bulk_upsert(
            Customer,
            objects,
            ["external_id"],
            ["name", "email", "region", "comuna", "created_at"],
        )
    elif entity == "productos":
        objects = [Product(**row) for row in records]
        _bulk_upsert(
            Product,
            objects,
            ["sku"],
            ["name", "category", "unit_cost", "unit_price", "active"],
        )
    elif entity == "bodegas":
        objects = [Warehouse(**row) for row in records]
        _bulk_upsert(Warehouse, objects, ["code"], ["name", "region"])
    elif entity == "transportistas":
        objects = [Carrier(**row) for row in records]
        _bulk_upsert(Carrier, objects, ["name"], ["name"])
    elif entity == "pedidos":
        customers = Customer.objects.in_bulk(field_name="external_id")
        objects = []
        for row in records:
            customer = customers.get(row["customer_external_id"].strip())
            if customer is None:
                raise RowValidationError(
                    "MISSING_REFERENCE",
                    f"Cliente inexistente: {row['customer_external_id']!r}.",
                )
            objects.append(
                SalesOrder(
                    external_id=row["external_id"],
                    customer=customer,
                    status=row["status"],
                    created_at=row["created_at"],
                    paid_at=row["paid_at"],
                    destination_region=row["destination_region"],
                )
            )
        _bulk_upsert(
            SalesOrder,
            objects,
            ["external_id"],
            ["customer", "status", "created_at", "paid_at", "destination_region"],
        )
    elif entity == "items":
        products = Product.objects.in_bulk(field_name="sku")
        warehouses = Warehouse.objects.in_bulk(field_name="code")
        orders = SalesOrder.objects.in_bulk(field_name="external_id")
        objects = []
        for row in records:
            product = products.get(row["sku"])
            if product is None:
                raise RowValidationError(
                    "SKU_UNKNOWN", f"SKU inexistente: {row['sku']!r}."
                )
            warehouse = warehouses.get(row["warehouse_code"].strip())
            order = orders.get(row["order_external_id"].strip())
            if warehouse is None or order is None:
                raise RowValidationError(
                    "MISSING_REFERENCE",
                    f"Pedido o bodega inexistente en ítem {row['external_id']!r}.",
                )
            objects.append(
                OrderItem(
                    external_id=row["external_id"].strip(),
                    order=order,
                    product=product,
                    warehouse=warehouse,
                    quantity=row["quantity"],
                    unit_price=row["unit_price"],
                    unit_cost=row["unit_cost"],
                )
            )
        _bulk_upsert(
            OrderItem,
            objects,
            ["external_id"],
            ["order", "product", "warehouse", "quantity", "unit_price", "unit_cost"],
        )
    elif entity == "despachos":
        warehouses = Warehouse.objects.in_bulk(field_name="code")
        carriers = Carrier.objects.in_bulk(field_name="name")
        orders = SalesOrder.objects.in_bulk(field_name="external_id")
        objects = []
        for row in records:
            order = orders.get(row["order_external_id"].strip())
            warehouse = warehouses.get(row["warehouse_code"].strip())
            carrier = carriers.get(row["carrier_name"].strip())
            if order is None or warehouse is None or carrier is None:
                raise RowValidationError(
                    "MISSING_REFERENCE",
                    "Pedido, bodega o transportista inexistente en el despacho.",
                )
            objects.append(
                Shipment(
                    order=order,
                    warehouse=warehouse,
                    carrier=carrier,
                    shipped_at=row["shipped_at"],
                    promised_at=row["promised_at"],
                    delivered_at=row["delivered_at"],
                    status=row["status"],
                )
            )
        _bulk_upsert(
            Shipment,
            objects,
            ["order", "warehouse"],
            ["carrier", "shipped_at", "promised_at", "delivered_at", "status"],
        )
    elif entity == "devoluciones":
        items = OrderItem.objects.in_bulk(field_name="external_id")
        existing_returns = ProductReturn.objects.in_bulk(field_name="external_id")
        returned_quantities: dict[int, int] = defaultdict(int)
        for item_id, quantity in ProductReturn.objects.values_list(
            "order_item_id", "quantity"
        ):
            returned_quantities[item_id] += quantity

        objects = []
        for row in records:
            item = items.get(row["order_item_external_id"].strip())
            if item is None:
                raise RowValidationError(
                    "MISSING_REFERENCE",
                    f"Ítem inexistente: {row['order_item_external_id']!r}.",
                )
            old_return = existing_returns.get(row["external_id"])
            if old_return:
                returned_quantities[old_return.order_item_id] -= old_return.quantity
            if returned_quantities[item.pk] + row["quantity"] > item.quantity:
                if old_return:
                    returned_quantities[old_return.order_item_id] += old_return.quantity
                raise RowValidationError(
                    "RETURN_EXCEEDS_SOLD",
                    f"La devolución {row['external_id']!r} supera la cantidad vendida.",
                )
            returned_quantities[item.pk] += row["quantity"]
            objects.append(
                ProductReturn(
                    external_id=row["external_id"].strip(),
                    order_item=item,
                    quantity=row["quantity"],
                    reason=row["reason"].strip(),
                    refund_amount=row["refund_amount"],
                    created_at=row["created_at"],
                )
            )
        _bulk_upsert(
            ProductReturn,
            objects,
            ["external_id"],
            ["order_item", "quantity", "reason", "refund_amount", "created_at"],
        )
    else:
        raise ValueError(f"Entidad ETL no soportada: {entity}")
    return len(records)


class Command(BaseCommand):
    help = "Valida y carga los CSV de data/raw de forma idempotente."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--input",
            type=Path,
            default=settings.BASE_DIR / "data" / "raw",
            help="Directorio con los CSV generados.",
        )

    def handle(self, *args, **options) -> None:
        input_dir: Path = options["input"]
        run = EtlRun.objects.create(status=EtlRun.Status.RUNNING)
        try:
            for entity in SOURCE_COLUMNS:
                self._process_file(run, input_dir / f"{entity}.csv", entity)
        except Exception as error:
            run.status = EtlRun.Status.FAILED
            run.finished_at = timezone.now()
            run.save(update_fields=["status", "finished_at"])
            if isinstance(error, CommandError):
                raise
            raise CommandError(f"ETL fallido: {error}") from error

        run.finished_at = timezone.now()
        run.status = (
            EtlRun.Status.WARNINGS
            if run.rows_corrected or run.rows_rejected
            else EtlRun.Status.SUCCESS
        )
        run.save(
            update_fields=[
                "finished_at",
                "status",
                "rows_read",
                "rows_loaded",
                "rows_corrected",
                "rows_rejected",
            ]
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"ETL {run.pk}: {run.status}; leídas={run.rows_read}, "
                f"cargadas={run.rows_loaded}, corregidas={run.rows_corrected}, "
                f"rechazadas={run.rows_rejected}."
            )
        )

    def _process_file(self, run: EtlRun, path: Path, entity: str) -> None:
        if not path.is_file():
            raise CommandError(f"No se encontró el archivo fuente: {path}")
        contents = path.read_bytes()
        file_hash = hashlib.sha256(contents).hexdigest()
        if EtlSourceFile.objects.filter(
            file_hash=file_hash, status=EtlSourceFile.Status.LOADED
        ).exists():
            self.stdout.write(f"Sin cambios, se omite {path.name}.")
            return

        try:
            frame = pd.read_csv(
                io.BytesIO(contents), dtype=str, keep_default_na=False
            )
        except (pd.errors.ParserError, pd.errors.EmptyDataError) as error:
            raise CommandError(f"CSV inválido ({path.name}): {error}") from error
        missing_columns = SOURCE_COLUMNS[entity] - set(frame.columns)
        if missing_columns:
            raise CommandError(
                f"{path.name} no contiene columnas requeridas: "
                f"{', '.join(sorted(missing_columns))}."
            )

        source_file = EtlSourceFile.objects.create(
            run=run,
            filename=path.name,
            file_hash=file_hash,
            entity=entity,
            rows=len(frame),
            status=EtlSourceFile.Status.PENDING,
        )
        run.rows_read += len(frame)

        try:
            with transaction.atomic():
                raw_rows = frame.to_dict(orient="records")
                EtlStagingRow.objects.bulk_create(
                    [
                        EtlStagingRow(
                            source_file=source_file,
                            entity=entity,
                            row_number=row_number,
                            raw_data={key: str(value) for key, value in row.items()},
                        )
                        for row_number, row in enumerate(raw_rows, start=2)
                    ],
                    batch_size=1000,
                )

                if entity == "pedidos":
                    last_rows: dict[str, int] = {}
                    for index, row in enumerate(raw_rows):
                        last_rows[row.get("external_id", "").strip()] = index
                    keep = set(last_rows.values())
                    run.rows_corrected += len(raw_rows) - len(keep)
                else:
                    keep = set(range(len(raw_rows)))

                accepted: list[tuple[dict[str, Any], dict[str, Any], int, int]] = []
                rejects: list[EtlReject] = []
                seen_keys: set[tuple[str, ...]] = set()
                for index, raw in enumerate(raw_rows):
                    if index not in keep:
                        continue
                    row_number = index + 2
                    source_key = _source_key(entity, raw)
                    if source_key is None:
                        rejects.append(
                            EtlReject(
                                run=run,
                                source_file=source_file,
                                entity=entity,
                                row_number=row_number,
                                rule_code="MISSING_KEY",
                                reason="Falta una clave de identificación obligatoria.",
                                raw_data={key: str(value) for key, value in raw.items()},
                            )
                        )
                        continue
                    if entity != "pedidos" and source_key in seen_keys:
                        rejects.append(
                            EtlReject(
                                run=run,
                                source_file=source_file,
                                entity=entity,
                                row_number=row_number,
                                rule_code="DUPLICATE_KEY",
                                reason="La clave del registro aparece más de una vez.",
                                raw_data={key: str(value) for key, value in raw.items()},
                            )
                        )
                        continue
                    seen_keys.add(source_key)
                    try:
                        clean, corrected = transform_record(entity, raw)
                        accepted.append((clean, raw, row_number, corrected))
                    except RowValidationError as error:
                        rejects.append(
                            EtlReject(
                                run=run,
                                source_file=source_file,
                                entity=entity,
                                row_number=row_number,
                                rule_code=error.rule_code,
                                reason=str(error),
                                raw_data={key: str(value) for key, value in raw.items()},
                            )
                        )

                context = _validation_context(entity)
                valid_records: list[dict[str, Any]] = []
                for row, raw, row_number, corrected in accepted:
                    try:
                        _validate_record(entity, row, context)
                        valid_records.append(row)
                        run.rows_corrected += corrected
                    except RowValidationError as error:
                        rejects.append(
                            EtlReject(
                                run=run,
                                source_file=source_file,
                                entity=entity,
                                row_number=row_number,
                                rule_code=error.rule_code,
                                reason=str(error),
                                raw_data={key: str(value) for key, value in raw.items()},
                            )
                        )

                loaded = _load_records(entity, valid_records)
                if rejects:
                    EtlReject.objects.bulk_create(rejects, batch_size=500)
                source_file.status = EtlSourceFile.Status.LOADED
                source_file.save(update_fields=["status"])
                run.rows_loaded += loaded
                run.rows_rejected += len(rejects)
                run.save(
                    update_fields=[
                        "rows_read",
                        "rows_loaded",
                        "rows_corrected",
                        "rows_rejected",
                    ]
                )
        except Exception:
            source_file.status = EtlSourceFile.Status.FAILED
            source_file.save(update_fields=["status"])
            raise
