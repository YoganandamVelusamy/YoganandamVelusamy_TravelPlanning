from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SearchFiltersModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    destination: str | None = None
    travel_type: str | None = None
    min_rating: float | None = Field(default=None, ge=0, le=5)
    max_rating: float | None = Field(default=None, ge=0, le=5)

    @model_validator(mode="after")
    def validate_rating_range(self) -> SearchFiltersModel:
        if self.min_rating is not None and self.max_rating is not None and self.min_rating > self.max_rating:
            raise ValueError("min_rating cannot exceed max_rating")
        return self


class SearchRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=5, ge=1, le=50)
    filters: SearchFiltersModel = Field(default_factory=SearchFiltersModel)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        if not value:
            raise ValueError("query must not be blank")
        return value


class RecommendationRequest(SearchRequest):
    pass


class FeedbackRequest(BaseModel):
    experience_id: str = Field(min_length=1, max_length=100)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(default="", max_length=1000)

    @field_validator("experience_id")
    @classmethod
    def validate_experience_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("experience_id must not be blank")
        return value


class EvidenceResponse(BaseModel):
    experience_id: str
    destination: str
    categories_visited: list[str]
    overall_rating: float
    review_text: str
    travel_type: str
    visit_date: date
    score: float
    keyword_rank: int | None
    semantic_rank: int | None
    synthetic_enrichment: bool


class SearchResponse(BaseModel):
    query: str
    count: int
    results: list[EvidenceResponse]


class DestinationResponse(BaseModel):
    destination: str
    average_rating: float
    evidence_count: int
    evidence_ids: list[str]


class ActivityResponse(BaseModel):
    category: str
    average_rating: float
    evidence_count: int


class PreferencesResponse(BaseModel):
    interests: list[str]
    destination: str | None
    travel_type: str | None
    duration_days: int | None
    budget_amount: float | None
    confidence: float


class RecommendationResponseModel(BaseModel):
    query: str
    preferences: PreferencesResponse
    destinations: list[DestinationResponse]
    activities: list[ActivityResponse]
    evidence: list[EvidenceResponse]
    limitations: list[str]


class ItineraryRequest(RecommendationRequest):
    days: int | None = Field(default=None, ge=1, le=30)
    budget: float | None = Field(default=None, gt=0)


class ItineraryResponse(BaseModel):
    status: str
    days_requested: int | None
    budget_requested: float | None
    recommendations: RecommendationResponseModel
    limitations: list[str]


class FeedbackResponse(BaseModel):
    feedback_id: int
    status: str = "recorded"