import unittest

from src.rag.hybrid_retriever import HybridRetriever, SearchFilters, TfidfEmbedder
from src.utils.data_loader import TravelExperience


class FakeEmbedder:
    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            normalized = text.casefold()
            vectors.append(
                [
                    float("beach" in normalized or "beaches" in normalized),
                    float("museum" in normalized or "museums" in normalized),
                ]
            )
        return vectors


class TruncatedVectorIndex:
    def synchronize(self, experiences, documents, embeddings) -> None:
        return None

    def search(self, query_embedding, filters, limit):
        return [(0, 1.0)]


def experience(
    experience_id: str,
    destination: str,
    review_text: str,
    travel_type: str = "Solo",
    rating: float = 4.0,
) -> TravelExperience:
    return TravelExperience(
        experience_id=experience_id,
        destination=destination,
        categories_visited=("beaches",),
        overall_rating=rating,
        review_text=review_text,
        travel_type=travel_type,
        visit_date=__import__("datetime").date(2025, 1, 1),
        activity_ratings={"beaches": rating},
    )


class HybridRetrieverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.retriever = HybridRetriever(
            [
                experience("case-1", "Nice, France", "Beautiful beaches and fresh seafood."),
                experience("case-2", "Paris, France", "Excellent museums and historic galleries."),
                experience("case-3", "Split, Croatia", "Sunny coast with quiet beaches.", "Couple", 4.5),
            ],
            FakeEmbedder(),
        )

    def test_hybrid_search_returns_relevant_evidence(self) -> None:
        results = self.retriever.search("beach holiday", limit=2)

        self.assertEqual({result.experience.experience_id for result in results}, {"case-1", "case-3"})
        self.assertTrue(all(result.semantic_rank is not None for result in results))

    def test_metadata_filters_apply_before_ranking(self) -> None:
        results = self.retriever.search(
            "beaches",
            filters=SearchFilters(travel_type="Couple", min_rating=4.5),
        )

        self.assertEqual([result.experience.experience_id for result in results], ["case-3"])

    def test_empty_query_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Query must not be empty"):
            self.retriever.search("   ")

    def test_tfidf_backend_encodes_documents_then_queries(self) -> None:
        embedder = TfidfEmbedder()
        document_vectors = embedder.encode(["beach and local food", "museum and history"])
        query_vectors = embedder.encode(["beach food"])

        self.assertEqual(len(document_vectors), 2)
        self.assertEqual(len(query_vectors), 1)
        self.assertEqual(len(document_vectors[0]), len(query_vectors[0]))

    def test_rrf_keeps_keyword_results_missing_from_vector_top_k(self) -> None:
        retriever = HybridRetriever(
            [
                experience("case-beach", "Nice, France", "Sunny coastline"),
                experience("case-museum", "Paris, France", "Excellent museum exhibits"),
            ],
            FakeEmbedder(),
            TruncatedVectorIndex(),
        )

        results = retriever.search("museum exhibits", limit=2)

        keyword_only = next(result for result in results if result.experience.experience_id == "case-museum")
        self.assertIsNone(keyword_only.semantic_rank)
        self.assertTrue(any(result.experience.experience_id == "case-beach" for result in results))


if __name__ == "__main__":
    unittest.main()