from __future__ import annotations

import os
import hashlib
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from dotenv import load_dotenv

from src.api.routes import router
from src.rag.hybrid_retriever import HybridRetriever, SentenceTransformerEmbedder, TfidfEmbedder
from src.rag.vector_index import ChromaVectorIndex
from src.services.feedback_store import FeedbackStore, default_feedback_path
from src.services.recommendation_service import RecommendationService
from src.utils.data_loader import default_data_path, load_experiences

load_dotenv()


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    if not hasattr(application.state, "recommendation_service"):
        dataset_path = Path(os.getenv("TRAVEL_DATA_PATH", str(default_data_path())))
        experiences = load_experiences(dataset_path)
        embedding_backend = os.getenv("EMBEDDING_BACKEND", "sentence-transformers").casefold()
        if embedding_backend == "sentence-transformers":
            embedding_model = os.getenv(
                "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
            )
            embedder = SentenceTransformerEmbedder(embedding_model)
        elif embedding_backend == "tfidf":
            embedder = TfidfEmbedder()
        else:
            raise ValueError("EMBEDDING_BACKEND must be 'sentence-transformers' or 'tfidf'")
        vector_path = Path(os.getenv("VECTOR_DB_PATH", "data/vector_db"))
        model_identity = (
            os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            if embedding_backend == "sentence-transformers"
            else "tfidf-v2-512"
        )
        collection_suffix = hashlib.sha256(model_identity.encode("utf-8")).hexdigest()[:12]
        vector_index = ChromaVectorIndex(vector_path, f"travel_exp_{collection_suffix}")
        retriever = HybridRetriever(experiences, embedder, vector_index)
        application.state.recommendation_service = RecommendationService(experiences, retriever)
        application.state.embedding_backend = embedding_backend
    if not hasattr(application.state, "feedback_store"):
        application.state.feedback_store = FeedbackStore(
            os.getenv("FEEDBACK_DB_PATH", str(default_feedback_path()))
        )
    application.state.dataset_count = application.state.recommendation_service.record_count
    yield


def create_app(
    recommendation_service: RecommendationService | None = None,
    feedback_store: FeedbackStore | None = None,
) -> FastAPI:
    application = FastAPI(
        title="AI-Powered Travel Planning Assistant",
        description="Hybrid retrieval and evidence-grounded travel recommendations.",
        version="0.1.0",
        lifespan=lifespan,
    )
    if recommendation_service is not None:
        application.state.recommendation_service = recommendation_service
    if feedback_store is not None:
        application.state.feedback_store = feedback_store
    application.include_router(router, prefix="/api/v1")

    @application.get("/health")
    def health() -> dict[str, str | int]:
        count = getattr(application.state, "dataset_count", 0)
        backend = getattr(application.state, "embedding_backend", "not_ready")
        return {"status": "ok", "dataset_records": count, "embedding_backend": backend}

    return application


app = create_app()