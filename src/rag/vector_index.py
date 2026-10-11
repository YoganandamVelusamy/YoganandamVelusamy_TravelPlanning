from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from src.utils.data_loader import TravelExperience

if TYPE_CHECKING:
    from src.rag.hybrid_retriever import SearchFilters


class VectorIndex(Protocol):
    def synchronize(
        self,
        experiences: list[TravelExperience],
        documents: list[str],
        embeddings: list[list[float]],
    ) -> None: ...

    def search(
        self,
        query_embedding: list[float],
        filters: SearchFilters,
        limit: int,
    ) -> list[tuple[int, float]]: ...


class ChromaVectorIndex:
    def __init__(self, persist_directory: Path | str, collection_name: str = "travel_experiences") -> None:
        import chromadb

        self._client = chromadb.PersistentClient(path=str(persist_directory))
        self._collection_name = collection_name
        self._collection = None

    @staticmethod
    def _fingerprint(documents: list[str], experiences: list[TravelExperience]) -> str:
        content = "\n".join(
            f"{experience.experience_id}|{experience.destination}|{experience.travel_type}|"
            f"{experience.overall_rating}|{document}"
            for experience, document in zip(experiences, documents, strict=True)
        )
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def synchronize(
        self,
        experiences: list[TravelExperience],
        documents: list[str],
        embeddings: list[list[float]],
    ) -> None:
        fingerprint = self._fingerprint(documents, experiences)
        try:
            collection = self._client.get_collection(self._collection_name)
        except Exception:
            collection = None

        if collection is not None and (collection.metadata or {}).get("corpus_fingerprint") != fingerprint:
            self._client.delete_collection(self._collection_name)
            collection = None

        if collection is None:
            collection = self._client.create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine", "corpus_fingerprint": fingerprint},
            )

        if collection.count() != len(experiences):
            self._client.delete_collection(self._collection_name)
            collection = self._client.create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine", "corpus_fingerprint": fingerprint},
            )
        if collection.count() == 0:
            batch_size = 128
            for start in range(0, len(experiences), batch_size):
                end = start + batch_size
                batch_experiences = experiences[start:end]
                collection.add(
                    ids=[f"experience-{index}" for index in range(start, min(end, len(experiences)))],
                    embeddings=embeddings[start:end],
                    documents=documents[start:end],
                    metadatas=[
                        {
                            "corpus_index": index,
                            "destination": experience.destination,
                            "travel_type": experience.travel_type,
                            "overall_rating": experience.overall_rating,
                        }
                        for index, experience in enumerate(batch_experiences, start=start)
                    ],
                )
        self._collection = collection

    def search(
        self,
        query_embedding: list[float],
        filters: SearchFilters,
        limit: int,
    ) -> list[tuple[int, float]]:
        if self._collection is None:
            raise RuntimeError("Vector index must be synchronized before search")

        conditions: list[dict[str, object]] = []
        if filters.destination:
            conditions.append({"destination": {"$eq": filters.destination}})
        if filters.travel_type:
            conditions.append({"travel_type": {"$eq": filters.travel_type}})
        if filters.min_rating is not None:
            conditions.append({"overall_rating": {"$gte": filters.min_rating}})
        if filters.max_rating is not None:
            conditions.append({"overall_rating": {"$lte": filters.max_rating}})
        where = None
        if len(conditions) == 1:
            where = conditions[0]
        elif conditions:
            where = {"$and": conditions}

        count = self._collection.count()
        if count == 0:
            return []
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(limit, count),
            where=where,
            include=["metadatas", "distances"],
        )
        metadata_rows = results["metadatas"][0]
        distance_rows = results["distances"][0]
        return [
            (int(metadata["corpus_index"]), 1.0 - float(distance))
            for metadata, distance in zip(metadata_rows, distance_rows, strict=True)
        ]