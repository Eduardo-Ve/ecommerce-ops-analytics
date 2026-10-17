from datetime import datetime, timezone

from django.test import SimpleTestCase

from etl.processing import RowValidationError, transform_record


class TransformRecordTests(SimpleTestCase):
    def test_order_status_and_mixed_date_are_normalized(self) -> None:
        row, corrected = transform_record(
            "pedidos",
            {
                "external_id": "ORD-1",
                "customer_external_id": "CUS-1",
                "status": "Entregado ",
                "created_at": "17/10/2025 10:30:00",
                "paid_at": "",
                "destination_region": "Metropolitana de Santiago",
            },
        )

        self.assertEqual(row["status"], "delivered")
        self.assertEqual(row["destination_region"], "Región Metropolitana")
        self.assertEqual(
            row["created_at"],
            datetime(2025, 10, 17, 10, 30, tzinfo=timezone.utc),
        )
        self.assertEqual(corrected, 3)

    def test_invalid_date_is_rejected(self) -> None:
        with self.assertRaisesRegex(RowValidationError, "Fecha inválida"):
            transform_record(
                "pedidos",
                {
                    "external_id": "ORD-1",
                    "customer_external_id": "CUS-1",
                    "status": "paid",
                    "created_at": "2025-13-40 25:61:00",
                    "paid_at": "",
                    "destination_region": "Región Metropolitana",
                },
            )

    def test_negative_quantity_is_rejected(self) -> None:
        with self.assertRaisesRegex(RowValidationError, "mayor que cero"):
            transform_record(
                "items",
                {
                    "external_id": "ORD-1-L1",
                    "order_external_id": "ORD-1",
                    "sku": "SKU-00001",
                    "warehouse_code": "WH-SCL",
                    "quantity": "-1",
                    "unit_price": "100",
                    "unit_cost": "50",
                },
            )

    def test_sku_is_trimmed_and_uppercased(self) -> None:
        row, corrected = transform_record(
            "items",
            {
                "external_id": "ORD-1-L1",
                "order_external_id": "ORD-1",
                "sku": " sku-00001 ",
                "warehouse_code": "WH-SCL",
                "quantity": "2",
                "unit_price": "100",
                "unit_cost": "50",
            },
        )

        self.assertEqual(row["sku"], "SKU-00001")
        self.assertEqual(corrected, 1)

    def test_shipment_date_order_is_rejected(self) -> None:
        with self.assertRaises(RowValidationError) as context:
            transform_record(
                "despachos",
                {
                    "order_external_id": "ORD-1",
                    "warehouse_code": "WH-SCL",
                    "carrier_name": "Chilexpress",
                    "shipped_at": "2025-10-10T00:00:00+00:00",
                    "promised_at": "2025-10-17T00:00:00+00:00",
                    "delivered_at": "2025-10-09T00:00:00+00:00",
                    "status": "delivered",
                },
            )

        self.assertEqual(context.exception.rule_code, "DATE_ORDER")
