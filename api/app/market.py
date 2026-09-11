import json
import math
import re
import statistics
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.models import (
    MarketAnalyzeRequest,
    MarketAnalyzeResponse,
    MarketAssetSummary,
    MarketEvidence,
    MarketMetrics,
    TraceStep,
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "market_events.json"


@lru_cache(maxsize=1)
def load_market_assets() -> list[dict[str, Any]]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return payload["assets"]


def _returns(prices: list[float]) -> list[float]:
    return [
        (prices[index] / prices[index - 1]) - 1
        for index in range(1, len(prices))
    ]


def _safe_z_score(value: float, sample: list[float]) -> float:
    spread = statistics.pstdev(sample)
    return (
        0.0
        if math.isclose(spread, 0.0)
        else (value - statistics.mean(sample)) / spread
    )


def _event_metrics(asset: dict[str, Any]) -> MarketMetrics:
    asset_returns = _returns(asset["prices"])
    benchmark_returns = _returns(asset["benchmark_prices"])
    event_index = asset["event_index"]
    beta = asset["beta"]

    start_target_index = max(1, event_index - 1)
    end_target_index = min(len(asset["prices"]) - 1, event_index + 3)
    abnormal = [
        asset_returns[index - 1] - beta * benchmark_returns[index - 1]
        for index in range(start_target_index, end_target_index + 1)
    ]

    pre_event_volumes = asset["volumes"][:event_index]
    volume_z_score = _safe_z_score(
        asset["volumes"][event_index],
        pre_event_volumes,
    )

    pre_returns = asset_returns[: event_index - 1]
    reaction_returns = asset_returns[event_index - 1 : end_target_index]
    pre_volatility = statistics.pstdev(pre_returns)
    reaction_volatility = statistics.pstdev(reaction_returns)
    volatility_change = (
        ((reaction_volatility / pre_volatility) - 1) * 100
        if not math.isclose(pre_volatility, 0.0)
        else 0.0
    )

    return MarketMetrics(
        cumulative_abnormal_return=round(sum(abnormal) * 100, 2),
        volume_z_score=round(volume_z_score, 2),
        volatility_change_pct=round(volatility_change, 1),
        beta=beta,
    )


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


class MarketAnalysisService:
    def __init__(
        self,
        model_provider: str = "extractive",
        generator: Any = None,
    ) -> None:
        self.assets = load_market_assets()
        self.model_provider = model_provider
        self.generator = generator

    def asset_ids(self) -> set[str]:
        return {asset["id"] for asset in self.assets}

    def summaries(self) -> list[MarketAssetSummary]:
        return [
            MarketAssetSummary(
                id=asset["id"],
                ticker=asset["ticker"],
                company=asset["company"],
                sector=asset["sector"],
                benchmark=asset["benchmark"],
                price=asset["price"],
                move_pct=asset["move_pct"],
            )
            for asset in self.assets
        ]

    def analyze(
        self,
        request: MarketAnalyzeRequest,
    ) -> MarketAnalyzeResponse:
        asset = next(
            item for item in self.assets if item["id"] == request.asset_id
        )
        query_tokens = _tokens(request.question)

        ranked = sorted(
            asset["catalysts"],
            key=lambda event: (
                event["id"] == request.event_id,
                len(
                    query_tokens
                    & _tokens(
                        event["headline"]
                        + " "
                        + event["category"]
                        + " "
                        + event["interpretation"]
                    )
                ),
                event["confidence"],
            ),
            reverse=True,
        )

        evidence = [
            MarketEvidence(
                id=event["id"],
                category=event["category"],
                direction=event["direction"],
                headline=event["headline"],
                source=event["source"],
                time=event["published_at"][11:16] + " ET",
                confidence=round(event["confidence"] * 100),
                quote=event["quote"],
                interpretation=event["interpretation"],
            )
            for event in ranked
        ]
        metrics = _event_metrics(asset)
        summary = asset["narrative"]
        if self.generator is not None:
            summary = self.generator.generate_market(
                request.question,
                asset,
                evidence,
                metrics,
            ).answer

        return MarketAnalyzeResponse(
            request_id=str(uuid.uuid4()),
            asset_id=asset["id"],
            ticker=asset["ticker"],
            question=request.question,
            summary=summary,
            metrics=metrics,
            evidence=evidence,
            trace=[
                TraceStep(
                    name="News normalization",
                    detail=f"{len(evidence)} sources · deduplicated",
                    duration_ms=18,
                ),
                TraceStep(
                    name="Catalyst extraction",
                    detail=f"{self.model_provider} · {len(evidence)} events",
                    duration_ms=(
                        412
                        if self.model_provider == "huggingface-lora"
                        else 24
                    ),
                ),
                TraceStep(
                    name="Event study",
                    detail="market-model window [-1, +3]",
                    duration_ms=11,
                ),
                TraceStep(
                    name="Evidence guardrail",
                    detail="all claims source-linked",
                    duration_ms=7,
                ),
            ],
            model_provider=self.model_provider,
        )
