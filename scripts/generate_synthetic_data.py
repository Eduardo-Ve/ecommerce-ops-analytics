#!/usr/bin/env python
"""Generate reproducible synthetic CSVs for the e-commerce ETL."""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from faker import Faker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "raw"
DEFAULT_SEED = 20251006
START_DATE = datetime(2024, 10, 1, tzinfo=timezone.utc)
END_DATE = datetime(2025, 9, 30, 23, 59, tzinfo=timezone.utc)
DIRTY_RATE = 0.01

REGIONS = [
    ("Región Metropolitana", ["Santiago", "Puente Alto", "Maipú"]),
    ("Valparaíso", ["Valparaíso", "Viña del Mar", "Quilpué"]),
    ("Biobío", ["Concepción", "Talcahuano", "Los Ángeles"]),
    ("Antofagasta", ["Antofagasta", "Calama"]),
    ("La Araucanía", ["Temuco", "Villarrica"]),
    ("Los Lagos", ["Puerto Montt", "Osorno"]),
]
CATEGORIES = [
    "Electrónica",
    "Hogar",
    "Deportes",
    "Belleza",
    "Juguetes",
    "Accesorios",
]
ORDER_STATUSES = ["pending", "paid", "shipped", "delivered", "cancelled"]
REASONS = ["producto_defectuoso", "talla_incorrecta", "no_cumple_expectativas"]


def timestamp(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def random_date(rng: random.Random) -> datetime:
    seconds = int((END_DATE - START_DATE).total_seconds())
    return START_DATE + timedelta(seconds=rng.randint(0, seconds))


def mixed_date(value: datetime) -> str:
    return value.strftime("%d/%m/%Y %H:%M:%S")


def make_dirty_catalog_entry(
    dataset: str, source_row: int, record_key: str, rule_code: str, reason: str
) -> dict[str, Any]:
    return {
        "dataset": dataset,
        "source_row": source_row,
        "record_key": record_key,
        "rule_code": rule_code,
        "reason": reason,
    }


def generate_data(orders_count: int, seed: int) -> dict[str, pd.DataFrame]:
    rng = random.Random(seed)
    fake = Faker("es_CL")
    fake.seed_instance(seed)
    dirty_catalog: list[dict[str, Any]] = []

    def annotate(
        dataset: str, index: int, key: str, rule_code: str, reason: str
    ) -> None:
        dirty_catalog.append(
            make_dirty_catalog_entry(
                dataset, index + 2, key, rule_code, reason
            )
        )

    customer_count = max(500, orders_count // 3)
    customers = []
    customer_regions: dict[str, tuple[str, str]] = {}
    for number in range(1, customer_count + 1):
        external_id = f"CUS-{number:06d}"
        region, comunas = rng.choice(REGIONS)
        customer_regions[external_id] = (region, rng.choice(comunas))
        customers.append(
            {
                "external_id": external_id,
                "name": fake.name(),
                "email": fake.email(),
                "region": region,
                "comuna": customer_regions[external_id][1],
                "created_at": timestamp(random_date(rng)),
            }
        )
    customers_df = pd.DataFrame(customers)

    products = []
    for number in range(1, 351):
        cost = rng.randrange(2_000, 180_000, 500)
        products.append(
            {
                "sku": f"SKU-{number:05d}",
                "name": f"{fake.word().capitalize()} {fake.word().capitalize()}",
                "category": rng.choice(CATEGORIES),
                "unit_cost": cost,
                "unit_price": cost + rng.randrange(1_000, 120_000, 500),
                "active": True,
            }
        )
    products_df = pd.DataFrame(products)

    warehouses = pd.DataFrame(
        [
            {"code": "WH-SCL", "name": "Bodega Santiago", "region": "Región Metropolitana"},
            {"code": "WH-VAP", "name": "Bodega Valparaíso", "region": "Valparaíso"},
            {"code": "WH-CCP", "name": "Bodega Concepción", "region": "Biobío"},
        ]
    )
    carriers = pd.DataFrame(
        [{"name": name} for name in ["Chilexpress", "Starken", "Blue Express"]]
    )

    product_by_sku = products_df.set_index("sku").to_dict("index")
    order_rows: list[dict[str, Any]] = []
    item_rows: list[dict[str, Any]] = []
    shipment_rows: list[dict[str, Any]] = []
    return_rows: list[dict[str, Any]] = []
    order_dates: dict[str, datetime] = {}
    order_statuses: dict[str, str] = {}
    items_by_order: dict[str, list[dict[str, Any]]] = {}
    order_warehouses: dict[str, set[str]] = {}

    for number in range(1, orders_count + 1):
        order_id = f"ORD-{number:06d}"
        customer_id = f"CUS-{rng.randint(1, customer_count):06d}"
        created_at = random_date(rng)
        status = rng.choices(
            ORDER_STATUSES, weights=[10, 15, 15, 55, 5], k=1
        )[0]
        region, _ = customer_regions[customer_id]
        order_dates[order_id] = created_at
        order_statuses[order_id] = status
        order_rows.append(
            {
                "external_id": order_id,
                "customer_external_id": customer_id,
                "status": status,
                "created_at": timestamp(created_at),
                "paid_at": timestamp(created_at + timedelta(hours=rng.randint(1, 48)))
                if status in {"paid", "shipped", "delivered"}
                else "",
                "destination_region": region,
            }
        )

        item_count = rng.choices([1, 2, 3, 4], weights=[45, 35, 15, 5], k=1)[0]
        items_by_order[order_id] = []
        order_warehouses[order_id] = set()
        for line_number in range(1, item_count + 1):
            sku = f"SKU-{rng.randint(1, 350):05d}"
            product = product_by_sku[sku]
            warehouse_code = rng.choice(["WH-SCL", "WH-VAP", "WH-CCP"])
            item = {
                "external_id": f"{order_id}-L{line_number}",
                "order_external_id": order_id,
                "sku": sku,
                "warehouse_code": warehouse_code,
                "quantity": rng.randint(1, 5),
                "unit_price": product["unit_price"],
                "unit_cost": product["unit_cost"],
            }
            items_by_order[order_id].append(item)
            order_warehouses[order_id].add(warehouse_code)
            item_rows.append(item.copy())

    orders_df = pd.DataFrame(order_rows)
    order_items_df = pd.DataFrame(item_rows)

    for order_id, warehouse_codes in order_warehouses.items():
        status = order_statuses[order_id]
        created_at = order_dates[order_id]
        for warehouse_code in sorted(warehouse_codes):
            shipped_at = (
                created_at + timedelta(days=rng.randint(1, 4))
                if status in {"shipped", "delivered"}
                else None
            )
            delivered_at = (
                shipped_at + timedelta(days=rng.randint(1, 8))
                if status == "delivered" and shipped_at
                else None
            )
            shipment_rows.append(
                {
                    "order_external_id": order_id,
                    "warehouse_code": warehouse_code,
                    "carrier_name": rng.choice(carriers["name"].tolist()),
                    "shipped_at": timestamp(shipped_at) if shipped_at else "",
                    "promised_at": timestamp(created_at + timedelta(days=7)),
                    "delivered_at": timestamp(delivered_at) if delivered_at else "",
                    "status": {
                        "pending": "pending",
                        "paid": "pending",
                        "shipped": "shipped",
                        "delivered": "delivered",
                        "cancelled": "cancelled",
                    }[status],
                }
            )
    shipments_df = pd.DataFrame(shipment_rows)

    for order_id, items in items_by_order.items():
        if order_statuses[order_id] != "delivered":
            continue
        for item in items:
            if rng.random() < 0.035:
                quantity = rng.randint(1, item["quantity"])
                return_rows.append(
                    {
                        "external_id": f"RET-{item['external_id']}",
                        "order_item_external_id": item["external_id"],
                        "quantity": quantity,
                        "reason": rng.choice(REASONS),
                        "refund_amount": item["unit_price"] * quantity,
                        "created_at": timestamp(
                            order_dates[order_id] + timedelta(days=rng.randint(10, 90))
                        ),
                    }
                )
    returns_df = pd.DataFrame(
        return_rows,
        columns=[
            "external_id",
            "order_item_external_id",
            "quantity",
            "reason",
            "refund_amount",
            "created_at",
        ],
    )

    dirty_order_count = max(1, round(orders_count * DIRTY_RATE))
    order_indices = rng.sample(range(orders_count), k=dirty_order_count)
    for index in order_indices:
        order = orders_df.iloc[index]
        field_choice = rng.choice(["status", "date", "region"])
        if field_choice == "status":
            orders_df.at[index, "status"] = rng.choice(
                ["ENTREGADO", "Entregado ", "PAGADO"]
            )
            annotate(
                "pedidos",
                index,
                order["external_id"],
                "STATUS_MAP",
                "Estado con variante textual o etiqueta no normalizada.",
            )
        elif field_choice == "date":
            orders_df.at[index, "created_at"] = "2025-13-40 25:61:00"
            annotate(
                "pedidos",
                index,
                order["external_id"],
                "DATE_FMT",
                "Fecha inválida: día, mes y hora fuera de rango.",
            )
        else:
            orders_df.at[index, "destination_region"] = "Metropolitana de Santiago"
            annotate(
                "pedidos",
                index,
                order["external_id"],
                "REGION_FMT",
                "Región equivalente escrita con una variante.",
            )

    mixed_date_count = max(1, round(orders_count * DIRTY_RATE))
    for index in rng.sample(range(orders_count), k=mixed_date_count):
        if orders_df.at[index, "created_at"] == "2025-13-40 25:61:00":
            continue
        order_id = orders_df.at[index, "external_id"]
        orders_df.at[index, "created_at"] = mixed_date(order_dates[order_id])
        annotate(
            "pedidos",
            index,
            order_id,
            "DATE_FMT",
            "Fecha válida en formato día/mes/año distinto al formato ISO.",
        )

    duplicate_order_index = rng.randrange(orders_count)
    duplicate_order = orders_df.iloc[duplicate_order_index].copy()
    orders_df = pd.concat(
        [orders_df, duplicate_order.to_frame().T], ignore_index=True
    )
    annotate(
        "pedidos",
        len(orders_df) - 1,
        duplicate_order["external_id"],
        "DUP_ORDER",
        "Fila duplicada de pedido; el ETL debe conservar la última.",
    )

    dirty_item_count = max(1, round(len(order_items_df) * DIRTY_RATE))
    for index in rng.sample(range(len(order_items_df)), k=dirty_item_count):
        item = order_items_df.iloc[index]
        fault = rng.choice(["unknown_sku", "negative_quantity", "sku_format"])
        if fault == "unknown_sku":
            order_items_df.at[index, "sku"] = "SKU-INEXISTENTE-99999"
            annotate(
                "items",
                index,
                item["external_id"],
                "SKU_UNKNOWN",
                "El SKU de la línea no existe en el maestro de productos.",
            )
        elif fault == "negative_quantity":
            order_items_df.at[index, "quantity"] = -abs(int(item["quantity"]))
            annotate(
                "items",
                index,
                item["external_id"],
                "AMOUNT_NEG",
                "Cantidad negativa en la línea de pedido.",
            )
        else:
            order_items_df.at[index, "sku"] = f" {str(item['sku']).lower()} "
            annotate(
                "items",
                index,
                item["external_id"],
                "SKU_FMT",
                "SKU con minúsculas y espacios que debe normalizarse.",
            )

    order_status_dirty_count = max(1, round(orders_count * DIRTY_RATE))
    for index in rng.sample(range(orders_count), k=order_status_dirty_count):
        orders_df.at[index, "status"] = rng.choice(
            ["ENTREGADO", "Entregado ", "PAGADO"]
        )
        order_id = orders_df.at[index, "external_id"]
        annotate(
            "pedidos",
            index,
            order_id,
            "STATUS_MAP",
            "Estado con mayúsculas o espacios que debe mapearse.",
        )

    shipment_status_dirty_count = max(1, round(len(shipments_df) * DIRTY_RATE))
    for index in rng.sample(range(len(shipments_df)), k=shipment_status_dirty_count):
        shipments_df.at[index, "status"] = rng.choice(["ENTREGADO", "Enviado "])
        row = shipments_df.iloc[index]
        annotate(
            "despachos",
            index,
            f"{row['order_external_id']}|{row['warehouse_code']}",
            "STATUS_MAP",
            "Estado de despacho con variante textual.",
        )

    shipment_date_indices = [
        index for index, row in shipments_df.iterrows() if row["shipped_at"]
    ]
    if shipment_date_indices:
        date_order_index = rng.choice(shipment_date_indices)
        shipped_at = datetime.fromisoformat(
            str(shipments_df.at[date_order_index, "shipped_at"])
        )
        shipments_df.at[date_order_index, "delivered_at"] = timestamp(
            shipped_at - timedelta(days=1)
        )
        row = shipments_df.iloc[date_order_index]
        annotate(
            "despachos",
            date_order_index,
            f"{row['order_external_id']}|{row['warehouse_code']}",
            "DATE_ORDER",
            "Fecha de entrega anterior a la fecha de envío.",
        )

    catalog_df = pd.DataFrame(
        dirty_catalog,
        columns=["dataset", "source_row", "record_key", "rule_code", "reason"],
    )
    return {
        "clientes": customers_df,
        "productos": products_df,
        "bodegas": warehouses,
        "transportistas": carriers,
        "pedidos": orders_df,
        "items": order_items_df,
        "despachos": shipments_df,
        "devoluciones": returns_df,
        "catalogo_suciedad": catalog_df,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--orders",
        type=int,
        default=3_000,
        help="cantidad base de pedidos (por defecto: 3000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"semilla aleatoria reproducible (por defecto: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"directorio de salida (por defecto: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()
    if args.orders < 1:
        parser.error("--orders debe ser mayor que cero")
    return args


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    datasets = generate_data(args.orders, args.seed)
    for name, frame in datasets.items():
        frame.to_csv(args.output / f"{name}.csv", index=False)
    print(
        f"Generados {len(datasets) - 1} archivos de entidad y el catálogo "
        f"de suciedad en {args.output.resolve()} (semilla={args.seed})."
    )
    print(f"Pedidos: {len(datasets['pedidos'])} (incluye un duplicado deliberado).")


if __name__ == "__main__":
    main()
