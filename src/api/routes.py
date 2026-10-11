from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Request

from src.api.schemas import (
    ActivityResponse,
    DestinationResponse,
    EvidenceResponse,
    FeedbackRequest,
    FeedbackResponse,
    ItineraryRequest,
    ItineraryResponse,
    PreferencesResponse,
    RecommendationRequest,
    RecommendationResponseModel,
    SearchRequest,
    SearchResponse,
)
from src.rag.hybrid_retriever import SearchFilters, SearchResult
from src.services.feedback_store import FeedbackStore
from src.services.recommendation_service import RecommendationService


router = APIRouter()


def _service(request: Request) -> RecommendationService:
    service = getattr(request.app.state, "recommendation_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Travel recommendation service is not ready")
    return service


def _feedback_store(request: Request) -> FeedbackStore:
    store = getattr(request.app.state, "feedback_store", None)
    if store is None:
        raise HTTPException(status_code=503, detail="Feedback store is not ready")
    return store


def _filters(request_filters: object) -> SearchFilters:
    return SearchFilters(**request_filters.model_dump())


def _evidence(result: SearchResult) -> EvidenceResponse:
    experience = result.experience
    return EvidenceResponse(
        experience_id=experience.experience_id,
        destination=experience.destination,
        categories_visited=list(experience.categories_visited),
        overall_rating=experience.overall_rating,
        review_text=experience.review_text,
        travel_type=experience.travel_type,
        visit_date=experience.visit_date,
        score=result.score,
        keyword_rank=result.keyword_rank,
        semantic_rank=result.semantic_rank,
        synthetic_enrichment=experience.synthetic_enrichment,
    )


def _recommendations(query: str, request: RecommendationRequest, service: RecommendationService) -> RecommendationResponseModel:
    result = service.recommend(query, filters=_filters(request.filters), limit=request.limit)
    return RecommendationResponseModel(
        query=query,
        preferences=PreferencesResponse(**asdict(result.preferences)),
        destinations=[
            DestinationResponse(
                destination=row.destination,
                average_rating=row.average_rating,
                evidence_count=row.evidence_count,
                evidence_ids=list(row.evidence_ids),
            )
            for row in result.destinations
        ],
        activities=[ActivityResponse(**asdict(row)) for row in result.activities],
        evidence=[_evidence(row) for row in result.evidence],
        limitations=list(result.limitations),
    )


@router.post("/search", response_model=SearchResponse)
def search(body: SearchRequest, request: Request) -> SearchResponse:
    service = _service(request)
    results = service.search(body.query, filters=_filters(body.filters), limit=body.limit)
    return SearchResponse(query=body.query, count=len(results), results=[_evidence(row) for row in results])


@router.post("/recommendations", response_model=RecommendationResponseModel)
def recommendations(body: RecommendationRequest, request: Request) -> RecommendationResponseModel:
    return _recommendations(body.query, body, _service(request))


@router.post("/itinerary/feasibility", response_model=ItineraryResponse)
def itinerary_feasibility(body: ItineraryRequest, request: Request) -> ItineraryResponse:
    result = _recommendations(body.query, body, _service(request))
    days = body.days if body.days is not None else result.preferences.duration_days
    budget = body.budget if body.budget is not None else result.preferences.budget_amount
    limitations = list(result.limitations)
    if body.days is not None and result.preferences.duration_days is None:
        limitations.append("Duration feasibility cannot be verified because the dataset contains no activity durations.")
    if body.budget is not None and result.preferences.budget_amount is None:
        limitations.append("Budget feasibility cannot be verified because the dataset contains no prices.")
    return ItineraryResponse(
        status="insufficient_data" if days is not None or budget is not None else "historical_evidence_only",
        days_requested=days,
        budget_requested=budget,
        recommendations=result,
        limitations=list(dict.fromkeys(limitations)),
    )


@router.post("/feedback", response_model=FeedbackResponse, status_code=201)
def feedback(body: FeedbackRequest, request: Request) -> FeedbackResponse:
    feedback_id = _feedback_store(request).save(body.experience_id, body.rating, body.comment)
    return FeedbackResponse(feedback_id=feedback_id)