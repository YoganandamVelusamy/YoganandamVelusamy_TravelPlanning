from __future__ import annotations

import re
from dataclasses import dataclass

from src.utils.data_loader import CATEGORY_FIELDS


CATEGORY_ALIASES = {
    "beaches": ("beach", "beaches", "coast", "coastal", "seaside", "island"),
    "restaurants": ("food", "local food", "cuisine", "restaurant", "restaurants", "dining"),
    "cafes": ("cafe", "cafes", "coffee"),
    "museums": ("museum", "museums", "history", "historical"),
    "monuments": ("monument", "monuments", "landmark", "landmarks"),
    "view points": ("viewpoint", "view points", "scenic view", "sightseeing"),
    "parks": ("park", "parks", "nature", "green space", "outdoors"),
    "theatres": ("theatre", "theatres", "theater", "shows", "performances"),
    "art galleries": ("art gallery", "art galleries", "gallery", "galleries", "art"),
    "pubs/bars": ("pub", "pubs", "bar", "bars", "nightlife"),
    "dance clubs": ("club", "clubs", "dancing", "dance", "nightclub"),
    "zoos": ("zoo", "zoos", "wildlife"),
    "gardens": ("garden", "gardens", "botanical"),
    "resorts": ("resort", "resorts", "spa resort"),
    "hotels/other lodgings": ("hotel", "hotels", "accommodation", "lodging"),
    "beauty & spas": ("spa", "spas", "wellness"),
}


def _contains_phrase(text: str, phrase: str) -> bool:
    pattern = re.escape(phrase).replace(r"\ ", r"\s+")
    return re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", text) is not None


@dataclass(frozen=True)
class PreferenceProfile:
    interests: tuple[str, ...]
    destination: str | None
    travel_type: str | None
    duration_days: int | None
    budget_amount: float | None
    confidence: float


def classify_preferences(query: str, destinations: list[str]) -> PreferenceProfile:
    normalized_query = query.casefold()
    interests = tuple(
        category
        for category in CATEGORY_FIELDS
        if any(
            _contains_phrase(normalized_query, alias)
            for alias in CATEGORY_ALIASES.get(category, (category,))
        )
    )
    destination = next(
        (
            value
            for value in sorted(destinations, key=len, reverse=True)
            if _contains_phrase(normalized_query, value.casefold())
        ),
        None,
    )

    travel_type = next(
        (
            kind
            for kind, aliases in (
                ("Family", ("family", "kids", "children")),
                ("Couple", ("couple", "romantic", "partner")),
                ("Friends", ("friends", "group trip", "group")),
                ("Solo", ("solo", "alone", "by myself")),
                ("Business", ("business", "work trip", "work travel")),
            )
            if any(_contains_phrase(normalized_query, alias) for alias in aliases)
        ),
        None,
    )
    duration_match = re.search(r"\b(\d{1,2})\s*[- ]?\s*(?:day|days|night|nights)\b", normalized_query)
    duration_days = int(duration_match.group(1)) if duration_match else None
    budget_match = re.search(
        r"(?:[$€£]\s*(\d+(?:\.\d+)?)|\bbudget\s*(?:of|is|:)?\s*[$€£]?\s*(\d+(?:\.\d+)?))",
        normalized_query,
    )
    budget_amount = None
    if budget_match:
        budget_amount = float(next(group for group in budget_match.groups() if group is not None))

    signals = sum(
        (
            bool(interests),
            destination is not None,
            travel_type is not None,
            duration_days is not None,
            budget_amount is not None,
        )
    )
    confidence = min(1.0, 0.35 + 0.13 * signals) if signals else 0.2
    return PreferenceProfile(
        interests=interests,
        destination=destination,
        travel_type=travel_type,
        duration_days=duration_days,
        budget_amount=budget_amount,
        confidence=round(confidence, 2),
    )