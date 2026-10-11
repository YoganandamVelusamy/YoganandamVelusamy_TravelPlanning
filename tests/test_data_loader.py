import csv
import tempfile
import unittest
from pathlib import Path

from src.utils.data_loader import CATEGORY_FIELDS, load_experiences


class DataLoaderTests(unittest.TestCase):
    def test_loads_and_normalizes_project_dataset(self) -> None:
        experiences = load_experiences()

        self.assertGreater(len(experiences), 0)
        first = experiences[0]
        self.assertEqual(first.experience_id, "User 1")
        self.assertEqual(first.destination, "Lyon, France")
        self.assertEqual(first.overall_rating, 2.35)
        self.assertEqual(first.visit_date.isoformat(), "2026-05-03")
        self.assertEqual(len(first.activity_ratings), len(CATEGORY_FIELDS))
        self.assertTrue(first.synthetic_enrichment)

    def test_rejects_rating_outside_supported_range(self) -> None:
        source_path = Path(__file__).resolve().parents[1] / "data" / "modified_data.csv"
        with source_path.open("r", encoding="utf-8-sig", newline="") as source_file:
            reader = csv.DictReader(source_file)
            headers = reader.fieldnames
            first_row = next(reader)
        self.assertIsNotNone(headers)
        first_row["roverall_rating"] = "5.1"

        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = Path(temp_dir) / "invalid.csv"
            with invalid_path.open("w", encoding="utf-8", newline="") as output_file:
                writer = csv.DictWriter(output_file, fieldnames=headers)
                writer.writeheader()
                writer.writerow(first_row)

            with self.assertRaisesRegex(ValueError, "between 0 and 5"):
                load_experiences(invalid_path)

    def test_rejects_invalid_visit_date(self) -> None:
        source_path = Path(__file__).resolve().parents[1] / "data" / "modified_data.csv"
        with source_path.open("r", encoding="utf-8-sig", newline="") as source_file:
            reader = csv.DictReader(source_file)
            headers = reader.fieldnames
            first_row = next(reader)
        self.assertIsNotNone(headers)
        first_row["visit_date"] = "not-a-date"

        with tempfile.TemporaryDirectory() as temp_dir:
            invalid_path = Path(temp_dir) / "invalid.csv"
            with invalid_path.open("w", encoding="utf-8", newline="") as output_file:
                writer = csv.DictWriter(output_file, fieldnames=headers)
                writer.writeheader()
                writer.writerow(first_row)

            with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
                load_experiences(invalid_path)


if __name__ == "__main__":
    unittest.main()