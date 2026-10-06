import unittest

from scripts.generate_synthetic_data import generate_data


class SyntheticDataGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.datasets = generate_data(3_000, 20251006)
        cls.catalog = cls.datasets["catalogo_suciedad"]

    def test_same_seed_produces_identical_dataframes(self) -> None:
        repeated = generate_data(3_000, 20251006)
        self.assertEqual(set(self.datasets), set(repeated))
        for name, frame in self.datasets.items():
            with self.subTest(dataset=name):
                self.assertTrue(frame.equals(repeated[name]))

    def test_every_dirty_rule_has_a_catalog_entry(self) -> None:
        expected_codes = {
            "DUP_ORDER",
            "SKU_FMT",
            "SKU_UNKNOWN",
            "STATUS_MAP",
            "DATE_FMT",
            "DATE_ORDER",
            "AMOUNT_NEG",
            "REGION_FMT",
        }
        self.assertTrue(expected_codes.issubset(set(self.catalog["rule_code"])))

    def test_catalog_points_to_dirty_entity_rows(self) -> None:
        entities = {
            "pedidos": self.datasets["pedidos"],
            "items": self.datasets["items"],
            "despachos": self.datasets["despachos"],
        }
        for entry in self.catalog.itertuples(index=False):
            frame = entities[entry.dataset]
            row_index = int(entry.source_row) - 2
            with self.subTest(rule_code=entry.rule_code, source_row=entry.source_row):
                self.assertGreaterEqual(row_index, 0)
                self.assertLess(row_index, len(frame))

                if entry.rule_code == "DUP_ORDER":
                    self.assertGreater(
                        (frame["external_id"] == entry.record_key).sum(), 1
                    )
                elif entry.rule_code == "SKU_FMT":
                    sku = frame.iloc[row_index]["sku"]
                    self.assertEqual(sku, sku.lower())
                    self.assertNotEqual(sku, sku.strip().lower())
                elif entry.rule_code == "SKU_UNKNOWN":
                    self.assertEqual(
                        frame.iloc[row_index]["sku"], "SKU-INEXISTENTE-99999"
                    )
                elif entry.rule_code == "AMOUNT_NEG":
                    self.assertLess(int(frame.iloc[row_index]["quantity"]), 0)
                elif entry.rule_code == "DATE_FMT":
                    created_at = frame.iloc[row_index]["created_at"]
                    self.assertTrue(
                        created_at == "2025-13-40 25:61:00" or "/" in created_at
                    )
                elif entry.rule_code == "REGION_FMT":
                    self.assertEqual(
                        frame.iloc[row_index]["destination_region"],
                        "Metropolitana de Santiago",
                    )
                elif entry.rule_code == "DATE_ORDER":
                    row = frame.iloc[row_index]
                    self.assertLess(row["delivered_at"], row["shipped_at"])
                elif entry.rule_code == "STATUS_MAP":
                    self.assertNotIn(
                        frame.iloc[row_index]["status"],
                        {"pending", "paid", "shipped", "delivered", "cancelled"},
                    )

    def test_default_scale_has_thousands_of_orders(self) -> None:
        self.assertEqual(len(self.datasets["pedidos"]), 3_001)
        self.assertGreater(len(self.datasets["items"]), 3_000)
        self.assertGreater(len(self.datasets["despachos"]), 3_000)


if __name__ == "__main__":
    unittest.main()
