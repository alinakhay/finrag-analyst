import json
import math
import re
import statistics
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.generation import ExtractiveGenerator
from app.grounding import safe_abstention, validate_cited_summary
from app.models import (
    MarketAnalyzeRequest,
    MarketAnalyzeResponse,
    MarketAssetSummary,
    MarketEvidence,
    MarketMetrics,
    TraceStep,
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "market_events.json"
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "did",
    "do",
    "does",
    "for",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "the",
    "there",
    "to",
    "was",
    "were",
    "what",
    "which",
    "with",
}


@lru_cache(maxsize=1)
def load_market_assets() -> list[dict[str, Any]]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    assets = payload["assets"]
    for asset in assets:
        series_lengths = {
            len(asset["prices"]),
            len(asset["benchmark_prices"]),
            len(asset["volumes"]),
            len(asset["labels"]),
        }
        if len(series_lengths) != 1 or next(iter(series_lengths)) < 6:
            raise ValueError(f"Asset {asset['id']!r} has misaligned or insufficient series")
        if not 2 <= asset["event_index"] < len(asset["prices"]):
            raise ValueError(f"Asset {asset['id']!r} has an invalid event_index")
        evidence_ids = [event["id"] for event in asset["catalysts"]]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError(f"Asset {asset['id']!r} has duplicate evidence IDs")
        claim_ids = {
            evidence_id
            for claim in asset["narrative_claims"]
            for evidence_id in claim["evidence_ids"]
        }
        unknown_claim_ids = claim_ids - set(evidence_ids)
        if unknown_claim_ids:
            raise ValueError(
                f"Asset {asset['id']!r} claims cite unknown evidence IDs: "
                f"{sorted(unknown_claim_ids)}"
            )
    return assets


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
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOPWORDS


class MarketAnalysisService:
    def __init__(
        self,
        model_provider: str = "extractive",
        generator: Any = None,
        top_k: int = 2,
    ) -> None:
        self.assets = load_market_assets()
        self.model_provider = model_provider
        self.generator = generator or ExtractiveGenerator()
        self.top_k = top_k

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
        query_tokens = _tokens(request.question) - _tokens(
            f"{asset['id']} {asset['ticker']} {asset['company']}"
        )

        event_ids = {event["id"] for event in asset["catalysts"]}
        if request.event_id is not None and request.event_id not in event_ids:
            raise ValueError(f"Event {request.event_id!r} does not belong to {asset['id']!r}")

        scored = [
            (
                event,
                len(
                    query_tokens
                    & _tokens(
                        event["headline"]
                        + " "
                        + event["category"]
                        + " "
                        + event["quote"]
                        + " "
                        + event["interpretation"]
                    )
                ),
            )
            for event in asset["catalysts"]
        ]
        eligible = [
            (event, score)
            for event, score in scored
            if score > 0 or event["id"] == request.event_id
        ]

        ranked = sorted(
            eligible,
            key=lambda item: (
                item[0]["id"] == request.event_id,
                item[1],
                item[0]["confidence"],
            ),
            reverse=True,
        )[: self.top_k]

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
            for event, _score in ranked
        ]
        metrics = _event_metrics(asset)
        if evidence:
            generated = self.generator.generate_market(
                request.question,
                asset,
                evidence,
                metrics,
            )
            guarded = validate_cited_summary(generated.answer, evidence)
        else:
            guarded = safe_abstention("No relevant event passed the lexical retrieval threshold.")

        if guarded.validation.abstained:
            guardrail_detail = f"abstained · {guarded.validation.reason}"
        else:
            guardrail_detail = (
                f"verified evidence IDs · {len(guarded.validation.cited_ids)} cited"
            )

        return MarketAnalyzeResponse(
            request_id=str(uuid.uuid4()),
            asset_id=asset["id"],
            ticker=asset["ticker"],
            question=request.question,
            summary=guarded.text,
            metrics=metrics,
            evidence=evidence,
            trace=[
                TraceStep(
                    name="Fixture loading",
                    detail=f"{len(asset['catalysts'])} validated synthetic records",
                    duration_ms=18,
                ),
                TraceStep(
                    name="Catalyst retrieval",
                    detail=f"lexical baseline · {len(evidence)} relevant events",
                    duration_ms=24,
                ),
                TraceStep(
                    name="Event study",
                    detail="market-model window [-1, +3]",
                    duration_ms=11,
                ),
                TraceStep(
                    name="Citation-ID guardrail",
                    detail=guardrail_detail,
                    duration_ms=7,
                ),
            ],
            model_provider=self.model_provider,
            citation_validation=guarded.validation,
        )
