import tempfile
import unittest
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from src.main import create_app
from src.rag.hybrid_retriever import HybridRetriever
from src.services.feedback_store import FeedbackStore
from src.services.recommendation_service import RecommendationService
from src.utils.data_loader import TravelExperience


class FakeEmbedder:
    def encode(self, texts: list[str]) -> list[list[float]]:
        return [[float("beach" in text.casefold()), float("food" in text.casefold())] for text in texts]


def test_service() -> RecommendationService:
    experience = TravelExperience(
        experience_id="case-1",
        destination="Nice, France",
        categories_visited=("beaches", "restaurants"),
        overall_rating=4.2,
        review_text="Loved the beach and local food.",
        travel_type="Couple",
        visit_date=date(2025, 1, 1),
        activity_ratings={"beaches": 4.8, "restaurants": 4.4},
    )
    retriever = HybridRetriever([experience], FakeEmbedder())
    return RecommendationService([experience], retriever)


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        feedback = FeedbackStore(Path(self.temp_dir.name) / "feedback.sqlite3")
        self.client = TestClient(create_app(test_service(), feedback))
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)
        self.temp_dir.cleanup()

    def test_health_search_and_recommendations(self) -> None:
        self.assertEqual(self.client.get("/health").json()["dataset_records"], 1)

        search_response = self.client.post(
            "/api/v1/search",
            json={"query": "beach trip", "limit": 3},
        )
        self.assertEqual(search_response.status_code, 200)
        self.assertEqual(search_response.json()["results"][0]["destination"], "Nice, France")
        self.assertTrue(search_response.json()["results"][0]["synthetic_enrichment"])

        recommendation_response = self.client.post(
            "/api/v1/recommendations",
            json={"query": "beach holiday with local food", "limit": 3},
        )
        self.assertEqual(recommendation_response.status_code, 200)
        self.assertEqual(recommendation_response.json()["activities"][0]["category"], "beaches")

    def test_itinerary_and_feedback_endpoints(self) -> None:
        itinerary_response = self.client.post(
            "/api/v1/itinerary/feasibility",
            json={"query": "beach break", "days": 5, "budget": 900},
        )
        self.assertEqual(itinerary_response.status_code, 200)
        self.assertEqual(itinerary_response.json()["status"], "insufficient_data")

        feedback_response = self.client.post(
            "/api/v1/feedback",
            json={"experience_id": "case-1", "rating": 5, "comment": "Useful"},
        )
        self.assertEqual(feedback_response.status_code, 201)
        self.assertEqual(feedback_response.json()["status"], "recorded")

    def test_invalid_filter_range_is_rejected(self) -> None:
        response = self.client.post(
            "/api/v1/search",
            json={"query": "beach", "filters": {"min_rating": 4, "max_rating": 2}},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()