import json
from pathlib import Path

from app.market import MarketAnalysisService
from app.models import MarketAnalyzeRequest

GOLD_PATH = Path(__file__).with_name("market_questions.json")


def run() -> dict[str, float]:
    cases = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    service = MarketAnalysisService()
    hits: list[int] = []
    reciprocal_ranks: list[float] = []
    direction_hits: list[int] = []

    for case in cases:
        result = service.analyze(
            MarketAnalyzeRequest(
                asset_id=case["asset_id"],
                question=case["question"],
            )
        )
        ids = [event.id for event in result.evidence]
        expected_id = case["expected_event_id"]
        hits.append(int(expected_id in ids[:2]))
        reciprocal_ranks.append(
            1 / (ids.index(expected_id) + 1) if expected_id in ids else 0
        )
        observed_direction = (
            "positive"
            if result.metrics.cumulative_abnormal_return > 0
            else "negative"
        )
        direction_hits.append(int(observed_direction == case["expected_direction"]))

    return {
        "cases": len(cases),
        "event_recall_at_2": round(sum(hits) / len(hits), 3),
        "mean_reciprocal_rank": round(sum(reciprocal_ranks) / len(cases), 3),
        "impact_direction_accuracy": round(
            sum(direction_hits) / len(direction_hits), 3
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
