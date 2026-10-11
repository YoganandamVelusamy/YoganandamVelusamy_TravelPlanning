from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path


CATEGORY_FIELDS = (
    "churches",
    "resorts",
    "beaches",
    "parks",
    "theatres",
    "museums",
    "malls",
    "zoos",
    "restaurants",
    "pubs/bars",
    "local services",
    "burger/pizza shops",
    "hotels/other lodgings",
    "juice bars",
    "art galleries",
    "dance clubs",
    "swimming pools",
    "gyms",
    "bakeries",
    "beauty & spas",
    "cafes",
    "view points",
    "monuments",
    "gardens",
)

REQUIRED_FIELDS = (
    "User",
    "destination",
    "category_visited",
    "roverall_rating",
    "review_text",
    "travel_type",
    "visit_date",
    *CATEGORY_FIELDS,
)


@dataclass(frozen=True)
class TravelExperience:
    experience_id: str
    destination: str
    categories_visited: tuple[str, ...]
    overall_rating: float
    review_text: str
    travel_type: str
    visit_date: date
    activity_ratings: dict[str, float]
    source: str = "modified_data.csv"
    synthetic_enrichment: bool = True


def default_data_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "modified_data.csv"


def _parse_rating(value: str, field: str, row_number: int) -> float:
    try:
        rating = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Row {row_number}: {field} must be numeric") from error
    if not 0.0 <= rating <= 5.0:
        raise ValueError(f"Row {row_number}: {field} must be between 0 and 5")
    return rating


def load_experiences(path: Path | str | None = None) -> list[TravelExperience]:
    """Load enriched travel rows and normalize them without modifying the source CSV."""
    csv_path = Path(path) if path is not None else default_data_path()
    if not csv_path.is_file():
        raise FileNotFoundError(f"Travel dataset not found: {csv_path}")

    experiences: list[TravelExperience] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as source_file:
        reader = csv.DictReader(source_file)
        headers = set(reader.fieldnames or ())
        missing_fields = sorted(set(REQUIRED_FIELDS) - headers)
        if missing_fields:
            raise ValueError(f"Dataset is missing required columns: {', '.join(missing_fields)}")

        for row_number, row in enumerate(reader, start=2):
            if not row.get("User", "").strip():
                raise ValueError(f"Row {row_number}: User must not be empty")

            destination = row["destination"].strip()
            review_text = row["review_text"].strip()
            travel_type = row["travel_type"].strip()
            if not destination or not review_text or not travel_type:
                raise ValueError(f"Row {row_number}: destination, review_text, and travel_type are required")

            try:
                visit_date = date.fromisoformat(row["visit_date"].strip())
            except ValueError as error:
                raise ValueError(f"Row {row_number}: visit_date must use YYYY-MM-DD format") from error

            activity_ratings = {
                field: _parse_rating(row[field], field, row_number)
                for field in CATEGORY_FIELDS
            }
            categories_visited = tuple(
                category.strip()
                for category in row["category_visited"].split(",")
                if category.strip()
            )
            experiences.append(
                TravelExperience(
                    experience_id=row["User"].strip(),
                    destination=destination,
                    categories_visited=categories_visited,
                    overall_rating=_parse_rating(row["roverall_rating"], "overall_rating", row_number),
                    review_text=review_text,
                    travel_type=travel_type,
                    visit_date=visit_date,
                    activity_ratings=activity_ratings,
                )
            )

    return experiences