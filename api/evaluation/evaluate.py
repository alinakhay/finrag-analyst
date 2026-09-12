import json
from pathlib import Path

from app.market import MarketAnalysisService
from app.models import MarketAnalyzeRequest

GOLD_PATH = Path(__file__).with_name("market_questions.json")


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 3) if values else 0.0


def run() -> dict[str, float | int]:
    cases = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    service = MarketAnalysisService()
    hits: list[int] = []
    reciprocal_ranks: list[float] = []
    direction_hits: list[int] = []
    evidence_precision: list[float] = []
    citation_validity: list[int] = []
    abstention_hits: list[int] = []

    for case in cases:
        result = service.analyze(
            MarketAnalyzeRequest(
                asset_id=case["asset_id"],
                question=case["question"],
            )
        )
        ids = [event.id for event in result.evidence]
        expected_id = case["expected_event_id"]
        if expected_id is None:
            abstention_hits.append(
                int(result.citation_validation.abstained and not result.evidence)
            )
            continue

        hits.append(int(expected_id in ids[:2]))
        reciprocal_ranks.append(
            1 / (ids.index(expected_id) + 1) if expected_id in ids else 0
        )
        evidence_precision.append(int(expected_id in ids) / len(ids) if ids else 0)
        citation_validity.append(
            int(
                result.citation_validation.valid
                and not result.citation_validation.abstained
            )
        )
        observed_direction = (
            "positive"
            if result.metrics.cumulative_abnormal_return > 0
            else "negative"
        )
        direction_hits.append(int(observed_direction == case["expected_direction"]))

    return {
        "cases": len(cases),
        "answerable_cases": len(hits),
        "no_answer_cases": len(abstention_hits),
        "event_recall_at_2": _mean(hits),
        "mean_reciprocal_rank": _mean(reciprocal_ranks),
        "evidence_precision": _mean(evidence_precision),
        "impact_direction_accuracy": _mean(direction_hits),
        "citation_validity": _mean(citation_validity),
        "safe_abstention_accuracy": _mean(abstention_hits),
    }


def passes_release_gate(metrics: dict[str, float | int]) -> bool:
    return all(
        metrics[name] >= threshold
        for name, threshold in {
            "event_recall_at_2": 1.0,
            "mean_reciprocal_rank": 0.85,
            "citation_validity": 1.0,
            "safe_abstention_accuracy": 1.0,
        }.items()
    )


if __name__ == "__main__":
    metrics = run()
    print(json.dumps(metrics, indent=2))
    if not passes_release_gate(metrics):
        raise SystemExit("Evaluation release gate failed")
