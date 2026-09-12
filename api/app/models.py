from typing import Literal

from pydantic import BaseModel, Field


class TraceStep(BaseModel):
    name: str
    detail: str
    duration_ms: int


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


class CitationValidation(BaseModel):
    valid: bool
    cited_ids: list[str]
    unsupported_ids: list[str]
    uncited_claim_count: int = Field(ge=0)
    abstained: bool
    reason: str


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
    citation_validation: CitationValidation


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    market_assets: int
    model_provider: str
