from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, replace

from src.agents.preference_agent import PreferenceProfile, classify_preferences
from src.rag.hybrid_retriever import HybridRetriever, SearchFilters, SearchResult
from src.utils.data_loader import CATEGORY_FIELDS, TravelExperience


@dataclass(frozen=True)
class DestinationRecommendation:
    destination: str
    average_rating: float
    evidence_count: int
    evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class ActivityRecommendation:
    category: str
    average_rating: float
    evidence_count: int


@dataclass(frozen=True)
class RecommendationResponse:
    preferences: PreferenceProfile
    destinations: tuple[DestinationRecommendation, ...]
    activities: tuple[ActivityRecommendation, ...]
    evidence: tuple[SearchResult, ...]
    limitations: tuple[str, ...]


class RecommendationService:
    def __init__(self, experiences: list[TravelExperience], retriever: HybridRetriever) -> None:
        self._experiences = experiences
        self._retriever = retriever
        self._destinations = sorted({experience.destination for experience in experiences})

    @property
    def record_count(self) -> int:
        return len(self._experiences)

    def search(
        self,
        query: str,
        *,
        filters: SearchFilters | None = None,
        limit: int = 5,
    ) -> list[SearchResult]:
        return self._retriever.search(query, filters=filters, limit=limit)

    def recommend(
        self,
        query: str,
        *,
        filters: SearchFilters | None = None,
        limit: int = 5,
    ) -> RecommendationResponse:
        preferences = classify_preferences(query, self._destinations)
        active_filters = filters or SearchFilters()
        if preferences.destination and active_filters.destination is None:
            active_filters = replace(active_filters, destination=preferences.destination)
        if preferences.travel_type and active_filters.travel_type is None:
            active_filters = replace(active_filters, travel_type=preferences.travel_type)

        evidence = self._retriever.search(query, filters=active_filters, limit=min(50, max(limit * 5, limit)))
        destination_rows: dict[str, list[SearchResult]] = defaultdict(list)
        activity_values: dict[str, list[float]] = defaultdict(list)
        for result in evidence:
            destination_rows[result.experience.destination].append(result)
            for category in result.experience.categories_visited:
                rating = result.experience.activity_ratings.get(category, 0.0)
                if rating > 0:
                    activity_values[category].append(rating)

        destinations = tuple(
            DestinationRecommendation(
                destination=destination,
                average_rating=round(
                    sum(row.experience.overall_rating for row in rows) / len(rows), 2
                ),
                evidence_count=len(rows),
                evidence_ids=tuple(row.experience.experience_id for row in rows),
            )
            for destination, rows in sorted(
                destination_rows.items(),
                key=lambda item: (
                    -sum(row.experience.overall_rating for row in item[1]) / len(item[1]),
                    -len(item[1]),
                    item[0],
                ),
            )[:limit]
        )

        selected_categories = preferences.interests or CATEGORY_FIELDS
        activities = tuple(
            ActivityRecommendation(
                category=category,
                average_rating=round(sum(activity_values[category]) / len(activity_values[category]), 2),
                evidence_count=len(activity_values[category]),
            )
            for category in sorted(
                (category for category in selected_categories if activity_values.get(category)),
                key=lambda category: (-sum(activity_values[category]) / len(activity_values[category]), category),
            )[:limit]
        )

        limitations = ["Enriched review text and trip metadata are synthetic sample data, not verified traveler reviews."]
        if preferences.budget_amount is not None:
            limitations.append("Budget feasibility cannot be verified because the dataset contains no prices.")
        if preferences.duration_days is not None:
            limitations.append("Duration feasibility cannot be verified because the dataset contains no activity durations.")
        return RecommendationResponse(
            preferences=preferences,
            destinations=destinations,
            activities=activities,
            evidence=tuple(evidence[:limit]),
            limitations=tuple(limitations),
        )