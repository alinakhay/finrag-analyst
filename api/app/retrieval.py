import math
import re
from collections import Counter
from dataclasses import dataclass

from app.corpus import Chunk

TOKEN_RE = re.compile(r"[a-z0-9]+")
DOMAIN_EXPANSIONS = {
    "credit": {"loans", "borrowers", "allowance", "delinquency", "non-performing", "cre"},
    "liquidity": {"cash", "funding", "deposits", "redemptions", "buffer"},
    "market": {"rates", "valuation", "aum", "fees", "outflows", "equity"},
    "operational": {"fraud", "cyber", "processor", "outage", "incident", "controls"},
    "regulatory": {"compliance", "jurisdiction", "rules", "capital", "regulators"},
}


def tokenize(text: str) -> list[str]:
    tokens = TOKEN_RE.findall(text.lower())
    expanded = list(tokens)
    for token in tokens:
        expanded.extend(DOMAIN_EXPANSIONS.get(token, ()))
    return expanded


@dataclass(frozen=True)
class SearchResult:
    chunk: Chunk
    score: float


class BM25Retriever:
    """Small, dependency-free retriever used by the zero-config demo and tests."""

    name = "local-bm25"

    def __init__(self, chunks: tuple[Chunk, ...], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.documents = [tokenize(chunk.text + " " + chunk.section) for chunk in chunks]
        self.counts = [Counter(document) for document in self.documents]
        self.average_length = sum(map(len, self.documents)) / max(len(self.documents), 1)
        self.document_frequency = Counter(
            token for document in self.documents for token in set(document)
        )

    def _idf(self, token: str) -> float:
        count = self.document_frequency[token]
        return math.log(1 + (len(self.documents) - count + 0.5) / (count + 0.5))

    def search(self, query: str, filing_id: str, top_k: int = 3) -> list[SearchResult]:
        query_tokens = tokenize(query)
        scored: list[tuple[Chunk, float]] = []
        for chunk, tokens, counts in zip(self.chunks, self.documents, self.counts, strict=True):
            if chunk.filing_id != filing_id:
                continue
            score = 0.0
            for token in query_tokens:
                frequency = counts[token]
                if not frequency:
                    continue
                norm = frequency + self.k1 * (
                    1 - self.b + self.b * len(tokens) / self.average_length
                )
                score += self._idf(token) * (frequency * (self.k1 + 1)) / norm
            scored.append((chunk, score))
        ranked = sorted(scored, key=lambda item: item[1], reverse=True)[:top_k]
        ceiling = max((score for _, score in ranked), default=1.0) or 1.0
        return [
            SearchResult(chunk=chunk, score=round(score / ceiling, 3))
            for chunk, score in ranked
        ]
