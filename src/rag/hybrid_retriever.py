from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from src.utils.data_loader import TravelExperience
from src.rag.vector_index import VectorIndex


class TextEmbedder(Protocol):
    def encode(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        import truststore

        truststore.inject_into_ssl()
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, normalize_embeddings=True)
        return vectors.tolist()


class TfidfEmbedder:
    def __init__(self) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._vectorizer = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            max_features=512,
            stop_words="english",
        )
        self._fitted = False

    def encode(self, texts: list[str]) -> list[list[float]]:
        if not self._fitted:
            vectors = self._vectorizer.fit_transform(texts)
            self._fitted = True
        else:
            vectors = self._vectorizer.transform(texts)
        return vectors.toarray().tolist()


@dataclass(frozen=True)
class SearchFilters:
    destination: str | None = None
    travel_type: str | None = None
    min_rating: float | None = None
    max_rating: float | None = None


@dataclass(frozen=True)
class SearchResult:
    experience: TravelExperience
    score: float
    keyword_rank: int | None
    semantic_rank: int | None


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.casefold())


def _document(experience: TravelExperience) -> str:
    categories = ", ".join(experience.categories_visited)
    return " ".join(
        (
            experience.destination,
            experience.travel_type,
            categories,
            experience.review_text,
        )
    )


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / (left_norm * right_norm)


class HybridRetriever:
    def __init__(
        self,
        experiences: list[TravelExperience],
        embedder: TextEmbedder,
        vector_index: VectorIndex | None = None,
    ) -> None:
        if not experiences:
            raise ValueError("At least one travel experience is required")
        self._experiences = experiences
        self._embedder = embedder
        self._documents = [_document(experience) for experience in experiences]
        self._document_tokens = [_tokens(document) for document in self._documents]
        document_vectors = embedder.encode(self._documents)
        if len(document_vectors) != len(experiences):
            raise ValueError("Embedder returned an unexpected number of document vectors")
        self._vector_index = vector_index
        if vector_index is not None:
            vector_index.synchronize(experiences, self._documents, document_vectors)
            self._document_vectors: list[list[float]] | None = None
        else:
            self._document_vectors = document_vectors

    @staticmethod
    def _matches(experience: TravelExperience, filters: SearchFilters) -> bool:
        if filters.destination and experience.destination.casefold() != filters.destination.casefold():
            return False
        if filters.travel_type and experience.travel_type.casefold() != filters.travel_type.casefold():
            return False
        if filters.min_rating is not None and experience.overall_rating < filters.min_rating:
            return False
        if filters.max_rating is not None and experience.overall_rating > filters.max_rating:
            return False
        return True

    def _bm25_scores(self, query_tokens: list[str], candidates: list[int]) -> dict[int, float]:
        if not query_tokens or not candidates:
            return {}
        candidate_tokens = {index: self._document_tokens[index] for index in candidates}
        average_length = sum(map(len, candidate_tokens.values())) / len(candidate_tokens)
        if average_length == 0:
            return {index: 0.0 for index in candidates}

        document_frequency: Counter[str] = Counter()
        term_frequencies = {index: Counter(tokens) for index, tokens in candidate_tokens.items()}
        for frequencies in term_frequencies.values():
            document_frequency.update(frequencies.keys())

        scores: dict[int, float] = {}
        for index, frequencies in term_frequencies.items():
            length = len(candidate_tokens[index])
            score = 0.0
            for term in query_tokens:
                frequency = frequencies[term]
                if not frequency:
                    continue
                inverse_frequency = math.log1p(
                    (len(candidates) - document_frequency[term] + 0.5)
                    / (document_frequency[term] + 0.5)
                )
                denominator = frequency + 1.5 * (1.0 - 0.75 + 0.75 * length / average_length)
                score += inverse_frequency * frequency * 2.5 / denominator
            scores[index] = score
        return scores

    def search(
        self,
        query: str,
        *,
        filters: SearchFilters | None = None,
        limit: int = 5,
    ) -> list[SearchResult]:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("Query must not be empty")
        if limit < 1 or limit > 50:
            raise ValueError("Limit must be between 1 and 50")

        active_filters = filters or SearchFilters()
        candidates = [
            index
            for index, experience in enumerate(self._experiences)
            if self._matches(experience, active_filters)
        ]
        if not candidates:
            return []

        query_tokens = _tokens(normalized_query)
        keyword_scores = self._bm25_scores(query_tokens, candidates)
        keyword_order = sorted(candidates, key=lambda index: (-keyword_scores[index], index))
        query_vector = self._embedder.encode([normalized_query])[0]
        if self._vector_index is None:
            if self._document_vectors is None:
                raise RuntimeError("In-memory document vectors are unavailable")
            semantic_order = sorted(
                candidates,
                key=lambda index: (-_cosine_similarity(query_vector, self._document_vectors[index]), index),
            )
        else:
            semantic_order = [
                index
                for index, _ in self._vector_index.search(
                    query_vector,
                    active_filters,
                    limit=min(len(candidates), max(limit * 10, limit)),
                )
                if index in candidates
            ]

        keyword_ranks = {index: rank for rank, index in enumerate(keyword_order, start=1)}
        semantic_ranks = {index: rank for rank, index in enumerate(semantic_order, start=1)}
        ranked_candidates = {
            index for index in keyword_order if keyword_scores[index] > 0
        } | set(semantic_order)

        def fused_score(index: int) -> float:
            keyword_contribution = (
                1.0 / (60 + keyword_ranks[index])
                if keyword_scores[index] > 0
                else 0.0
            )
            semantic_rank = semantic_ranks.get(index)
            semantic_contribution = 1.0 / (60 + semantic_rank) if semantic_rank is not None else 0.0
            return keyword_contribution + semantic_contribution

        fused_order = sorted(
            ranked_candidates,
            key=lambda index: (-fused_score(index), index),
        )
        return [
            SearchResult(
                experience=self._experiences[index],
                score=fused_score(index),
                keyword_rank=keyword_ranks[index] if keyword_scores[index] > 0 else None,
                semantic_rank=semantic_ranks.get(index),
            )
            for index in fused_order[:limit]
        ]