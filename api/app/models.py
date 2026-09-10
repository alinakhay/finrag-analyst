from typing import Literal

from pydantic import BaseModel, Field


class FilingSummary(BaseModel):
    id: str
    company: str
    form: str
    fiscal_year: int
    sector: str


class AnalyzeRequest(BaseModel):
    filing_id: str = Field(min_length=2, max_length=64)
    question: str = Field(min_length=5, max_length=500)
    top_k: int | None = Field(default=None, ge=1, le=8)


class Citation(BaseModel):
    chunk_id: str
    section: str
    page: int
    quote: str
    score: float = Field(ge=0, le=1)


class RiskExposure(BaseModel):
    category: Literal["credit", "liquidity", "market", "operational"]
    score: int = Field(ge=0, le=100)


class TraceStep(BaseModel):
    name: str
    detail: str
    duration_ms: int


class AnalyzeResponse(BaseModel):
    request_id: str
    filing_id: str
    answer: str
    bullets: list[str]
    citations: list[Citation]
    groundedness: float = Field(ge=0, le=1)
    risk_score: int = Field(ge=0, le=100)
    risk_level: str
    exposure: list[RiskExposure]
    trace: list[TraceStep]
    model_provider: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    documents: int
    model_provider: str

