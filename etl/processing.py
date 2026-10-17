from __future__ import annotations

import unicodedata
from datetime import datetime, timezone
from typing import Any


class RowValidationError(ValueError):
    def __init__(self, rule_code: str, reason: str) -> None:
        super().__init__(reason)
        self.rule_code = rule_code


ORDER_STATUSES = {
    "pending": "pending",
    "pendiente": "pending",
    "paid": "paid",
    "pagado": "paid",
    "pagada": "paid",
    "shipped": "shipped",
    "enviado": "shipped",
    "enviada": "shipped",
    "delivered": "delivered",
    "entregado": "delivered",
    "entregada": "delivered",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "cancelado": "cancelled",
    "cancelada": "cancelled",
}
SHIPMENT_STATUSES = {
    "pending": "pending",
    "pendiente": "pending",
    "shipped": "shipped",
    "enviado": "shipped",
    "enviada": "shipped",
    "delivered": "delivered",
    "entregado": "delivered",
    "entregada": "delivered",
    "cancelled": "cancelled",
    "canceled": "cancelled",
    "cancelado": "cancelled",
    "cancelada": "cancelled",
}
REGIONS = {
    "metropolitana de santiago": "Región Metropolitana",
    "region metropolitana": "Región Metropolitana",
    "rm": "Región Metropolitana",
}


def _ascii_lower(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    return without_accents.lower()


def _text(value: Any) -> str:
    return str(value).strip()


def _region(value: Any) -> tuple[str, bool]:
    text = _text(value)
    canonical = REGIONS.get(_ascii_lower(text), text)
    return canonical, canonical != str(value)


def _timestamp(value: Any, *, optional: bool = False) -> tuple[datetime | None, bool]:
    text = _text(value)
    if not text:
        if optional:
            return None, False
        raise RowValidationError("DATE_INVALID", "Falta una fecha obligatoria.")

    parsed: datetime | None = None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        for date_format in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
            try:
                parsed = datetime.strptime(text, date_format)
                break
            except ValueError:
                continue
    if parsed is None:
        raise RowValidationError("DATE_INVALID", f"Fecha inválida: {text!r}.")

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    normalized = parsed.astimezone(timezone.utc)
    return normalized, normalized.isoformat(timespec="seconds") != text


def _integer(value: Any, label: str, *, positive: bool = False) -> int:
    try:
        number = int(_text(value))
    except (TypeError, ValueError) as error:
        raise RowValidationError(
            "INVALID_NUMBER", f"{label} debe ser un entero."
        ) from error
    if number < (1 if positive else 0):
        raise RowValidationError("AMOUNT_NEG", f"{label} debe ser mayor que cero.")
    return number


def _boolean(value: Any, label: str) -> bool:
    text = _text(value).lower()
    if text in {"true", "1", "yes", "si", "sí"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    raise RowValidationError("INVALID_BOOLEAN", f"{label} debe ser verdadero o falso.")


def _status(value: Any, mapping: dict[str, str]) -> tuple[str, bool]:
    text = _text(value)
    status = mapping.get(_ascii_lower(text))
    if status is None:
        raise RowValidationError("STATUS_MAP", f"Estado desconocido: {text!r}.")
    return status, status != text


def transform_record(entity: str, raw: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Normalize one source row; return the clean row and number of corrections."""
    row = {key: _text(value) for key, value in raw.items()}
    corrected = 0

    if entity == "clientes":
        region, changed = _region(row["region"])
        created_at, date_changed = _timestamp(row["created_at"])
        corrected += int(changed) + int(date_changed)
        row.update(
            external_id=row["external_id"].strip(),
            name=row["name"].strip(),
            email=row["email"].strip() or None,
            region=region,
            comuna=row["comuna"].strip(),
            created_at=created_at,
        )
    elif entity == "productos":
        sku = row["sku"].strip().upper()
        corrected += int(sku != row["sku"])
        row.update(
            sku=sku,
            unit_cost=_integer(row["unit_cost"], "unit_cost"),
            unit_price=_integer(row["unit_price"], "unit_price"),
            active=_boolean(row["active"], "active"),
            name=row["name"].strip(),
            category=row["category"].strip(),
        )
    elif entity == "bodegas":
        region, changed = _region(row["region"])
        corrected += int(changed)
        row.update(
            code=row["code"].strip().upper(),
            name=row["name"].strip(),
            region=region,
        )
    elif entity == "transportistas":
        row["name"] = row["name"].strip()
    elif entity == "pedidos":
        status, status_changed = _status(row["status"], ORDER_STATUSES)
        created_at, date_changed = _timestamp(row["created_at"])
        paid_at, paid_date_changed = _timestamp(row["paid_at"], optional=True)
        region, region_changed = _region(row["destination_region"])
        corrected += sum((status_changed, date_changed, paid_date_changed, region_changed))
        row.update(
            status=status,
            created_at=created_at,
            paid_at=paid_at,
            destination_region=region,
            external_id=row["external_id"].strip(),
            customer_external_id=row["customer_external_id"].strip(),
        )
    elif entity == "items":
        sku = row["sku"].strip().upper()
        corrected += int(sku != row["sku"])
        row.update(
            external_id=row["external_id"].strip(),
            order_external_id=row["order_external_id"].strip(),
            warehouse_code=row["warehouse_code"].strip().upper(),
            sku=sku,
            quantity=_integer(row["quantity"], "quantity", positive=True),
            unit_price=_integer(row["unit_price"], "unit_price"),
            unit_cost=_integer(row["unit_cost"], "unit_cost"),
        )
    elif entity == "despachos":
        status, status_changed = _status(row["status"], SHIPMENT_STATUSES)
        shipped_at, shipped_changed = _timestamp(row["shipped_at"], optional=True)
        promised_at, promised_changed = _timestamp(row["promised_at"])
        delivered_at, delivered_changed = _timestamp(
            row["delivered_at"], optional=True
        )
        if shipped_at and delivered_at and delivered_at < shipped_at:
            raise RowValidationError(
                "DATE_ORDER", "La entrega ocurre antes del despacho."
            )
        corrected += sum(
            (status_changed, shipped_changed, promised_changed, delivered_changed)
        )
        row.update(
            order_external_id=row["order_external_id"].strip(),
            warehouse_code=row["warehouse_code"].strip().upper(),
            carrier_name=row["carrier_name"].strip(),
            status=status,
            shipped_at=shipped_at,
            promised_at=promised_at,
            delivered_at=delivered_at,
        )
    elif entity == "devoluciones":
        created_at, date_changed = _timestamp(row["created_at"])
        corrected += int(date_changed)
        row.update(
            external_id=row["external_id"].strip(),
            order_item_external_id=row["order_item_external_id"].strip(),
            reason=row["reason"].strip(),
            quantity=_integer(row["quantity"], "quantity", positive=True),
            refund_amount=_integer(row["refund_amount"], "refund_amount"),
            created_at=created_at,
        )
    else:
        raise ValueError(f"Entidad ETL no soportada: {entity}")

    return row, corrected
