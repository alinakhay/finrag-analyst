import json
from pathlib import Path

from app.corpus import load_corpus
from app.retrieval import BM25Retriever

GOLD_PATH = Path(__file__).with_name("gold_questions.json")


def run() -> dict[str, float]:
    cases = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    retriever = BM25Retriever(load_corpus())
    recalls: list[int] = []
    reciprocal_ranks: list[float] = []
    for case in cases:
        results = retriever.search(case["question"], case["filing_id"], top_k=3)
        ids = [result.chunk.id for result in results]
        recalls.append(int(case["expected_chunk_id"] in ids))
        reciprocal_ranks.append(
            1 / (ids.index(case["expected_chunk_id"]) + 1)
            if case["expected_chunk_id"] in ids else 0
        )
    return {
        "cases": len(cases),
        "recall_at_3": round(sum(recalls) / len(recalls), 3),
        "mean_reciprocal_rank": round(sum(reciprocal_ranks) / len(reciprocal_ranks), 3),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

