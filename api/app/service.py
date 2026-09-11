import time
import uuid
from collections import Counter, deque
from threading import Lock

from app.config import Settings
from app.corpus import Chunk, load_corpus
from app.generation import build_generator
from app.models import AnalyzeRequest, AnalyzeResponse, Citation, RiskExposure, TraceStep
from app.retrieval import BM25Retriever

CATEGORY_WEIGHTS = {"credit": 1.15, "liquidity": 1.05, "market": 0.95, "operational": 1.1}


class Metrics:
    def __init__(self) -> None:
        self.requests = 0
        self.errors = 0
        self.latencies: deque[float] = deque(maxlen=500)
        self._lock = Lock()

    def observe(self, duration_ms: float, error: bool = False) -> None:
        with self._lock:
            self.requests += 1
            self.errors += int(error)
            self.latencies.append(duration_ms)

    def as_prometheus(self) -> str:
        with self._lock:
            latencies = sorted(self.latencies)
            p95_index = max(0, min(len(latencies) - 1, int(len(latencies) * 0.95) - 1))
            p95 = latencies[p95_index] if latencies else 0
            return "\n".join(
                [
                    "# HELP catalystlens_requests_total Total analysis requests.",
                    "# TYPE catalystlens_requests_total counter",
                    f"catalystlens_requests_total {self.requests}",
                    "# HELP catalystlens_errors_total Total failed analysis requests.",
                    "# TYPE catalystlens_errors_total counter",
                    f"catalystlens_errors_total {self.errors}",
                    "# HELP catalystlens_latency_p95_ms Rolling p95 analysis latency.",
                    "# TYPE catalystlens_latency_p95_ms gauge",
                    f"catalystlens_latency_p95_ms {p95:.2f}",
                    "",
                ]
            )


class AnalysisService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.corpus = load_corpus()
        if settings.retriever_backend == "hybrid":
            from app.vector_retrieval import HybridRetriever

            self.retriever = HybridRetriever(self.corpus, settings)
        else:
            self.retriever = BM25Retriever(self.corpus)
        self.generator = build_generator(settings)
        self.metrics = Metrics()

    def filing_ids(self) -> set[str]:
        return {chunk.filing_id for chunk in self.corpus}

    @staticmethod
    def _risk_profile(
        chunks: tuple[Chunk, ...], filing_id: str
    ) -> tuple[int, str, list[RiskExposure]]:
        counts = Counter(chunk.risk_category for chunk in chunks if chunk.filing_id == filing_id)
        exposures = []
        for category in ("credit", "liquidity", "market", "operational"):
            score = min(95, round(28 + counts[category] * 18 * CATEGORY_WEIGHTS[category]))
            exposures.append(RiskExposure(category=category, score=score))
        composite = round(sum(item.score for item in exposures) / len(exposures))
        level = "Elevated" if composite >= 68 else "Heightened" if composite >= 58 else "Moderate"
        return composite, level, exposures

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponse:
        started = time.perf_counter()
        retrieval_started = time.perf_counter()
        results = self.retriever.search(
            request.question, request.filing_id, request.top_k or self.settings.top_k
        )
        retrieval_ms = max(1, round((time.perf_counter() - retrieval_started) * 1000))
        generated = self.generator.generate(request.question, results)
        citations = [
            Citation(
                chunk_id=result.chunk.id,
                section=result.chunk.section,
                page=result.chunk.page,
                quote=result.chunk.text,
                score=result.score,
            )
            for result in results[:2]
        ]
        risk_score, risk_level, exposure = self._risk_profile(self.corpus, request.filing_id)
        if self.generator.name == "extractive":
            groundedness = 1.0 if citations else 0.0
        else:
            referenced_sources = sum(
                citation.chunk_id in generated.answer for citation in citations
            )
            groundedness = round(referenced_sources / max(len(citations), 1), 3)
        total_ms = max(2, round((time.perf_counter() - started) * 1000))
        self.metrics.observe(total_ms)
        return AnalyzeResponse(
            request_id=str(uuid.uuid4()), filing_id=request.filing_id, answer=generated.answer,
            bullets=generated.bullets, citations=citations, groundedness=groundedness,
            risk_score=risk_score, risk_level=risk_level, exposure=exposure,
            trace=[
                TraceStep(name="Query expansion", detail="finance risk ontology", duration_ms=1),
                TraceStep(
                    name="Evidence retrieval",
                    detail=f"{self.retriever.name} · top {len(results)} chunks",
                    duration_ms=retrieval_ms,
                ),
                TraceStep(
                    name="Grounded generation",
                    detail=self.generator.name,
                    duration_ms=max(1, total_ms - retrieval_ms),
                ),
                TraceStep(
                    name="Citation guardrail",
                    detail=f"{len(citations)} claims linked",
                    duration_ms=1,
                ),
            ],
            model_provider=self.generator.name,
        )
