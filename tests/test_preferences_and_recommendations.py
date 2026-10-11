import unittest
from datetime import date

from src.agents.preference_agent import classify_preferences
from src.rag.hybrid_retriever import HybridRetriever
from src.services.recommendation_service import RecommendationService
from src.utils.data_loader import TravelExperience


class FakeEmbedder:
    def encode(self, texts: list[str]) -> list[list[float]]:
        return [[float("beach" in text.casefold()), float("food" in text.casefold())] for text in texts]


def sample_experience() -> TravelExperience:
    return TravelExperience(
        experience_id="case-1",
        destination="Nice, France",
        categories_visited=("beaches", "restaurants"),
        overall_rating=4.2,
        review_text="Loved the beach and local food.",
        travel_type="Couple",
        visit_date=date(2025, 1, 1),
        activity_ratings={"beaches": 4.8, "restaurants": 4.4},
    )


class PreferenceAndRecommendationTests(unittest.TestCase):
    def test_classifies_interests_and_trip_constraints(self) -> None:
        profile = classify_preferences("5-day romantic beach trip under $900", ["Nice, France"])

        self.assertEqual(profile.interests, ("beaches",))
        self.assertEqual(profile.travel_type, "Couple")
        self.assertEqual(profile.duration_days, 5)
        self.assertEqual(profile.budget_amount, 900.0)
        self.assertGreater(profile.confidence, 0.5)

    def test_does_not_match_category_inside_an_unrelated_word(self) -> None:
        profile = classify_preferences("A relaxing city party weekend", [])

        self.assertNotIn("art galleries", profile.interests)

    def test_recommendations_disclose_missing_feasibility_data(self) -> None:
        experience = sample_experience()
        retriever = HybridRetriever([experience], FakeEmbedder())
        service = RecommendationService([experience], retriever)

        result = service.recommend("5-day beach trip under $900", limit=3)

        self.assertEqual(result.destinations[0].destination, "Nice, France")
        self.assertEqual(result.activities[0].category, "beaches")
        self.assertTrue(any("no prices" in item for item in result.limitations))
        self.assertTrue(any("no activity durations" in item for item in result.limitations))


if __name__ == "__main__":
    unittest.main()