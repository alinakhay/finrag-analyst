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


class MarketAssetSummary(BaseModel):
    id: str
    ticker: str
    company: str
    sector: str
    benchmark: str
    price: float
    move_pct: float


class MarketAnalyzeRequest(BaseModel):
    asset_id: str = Field(min_length=2, max_length=16)
    question: str = Field(min_length=5, max_length=500)
    event_id: str | None = Field(default=None, max_length=64)


class MarketMetrics(BaseModel):
    cumulative_abnormal_return: float
    volume_z_score: float
    volatility_change_pct: float
    beta: float
    event_window: str = "[-1, +3]"


class MarketEvidence(BaseModel):
    id: str
    category: str
    direction: Literal["positive", "negative", "mixed"]
    headline: str
    source: str
    time: str
    confidence: int = Field(ge=0, le=100)
    quote: str
    interpretation: str


class MarketAnalyzeResponse(BaseModel):
    request_id: str
    asset_id: str
    ticker: str
    question: str
    summary: str
    metrics: MarketMetrics
    evidence: list[MarketEvidence]
    trace: list[TraceStep]
    model_provider: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    documents: int
    market_assets: int = 0
    model_provider: str
