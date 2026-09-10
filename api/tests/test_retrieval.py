from app.corpus import load_corpus
from app.retrieval import BM25Retriever


def test_credit_query_ranks_credit_disclosure_first() -> None:
    results = BM25Retriever(load_corpus()).search(
        "How did non-performing credit and the loan allowance change?", "meridian", top_k=3
    )
    assert results[0].chunk.id == "meridian-credit-01"


def test_retrieval_never_crosses_filing_boundary() -> None:
    results = BM25Retriever(load_corpus()).search("operational fraud risk", "helix", top_k=8)
    assert results
    assert all(result.chunk.filing_id == "helix" for result in results)

