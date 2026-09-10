import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.corpus import load_corpus
from app.models import AnalyzeRequest, AnalyzeResponse, FilingSummary, HealthResponse
from app.service import AnalysisService

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(message)s")
logger = logging.getLogger("finrag")
service = AnalysisService(settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    load_corpus()
    logger.info(json.dumps({"event": "startup", "documents": len(service.filing_ids())}))
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Evidence-grounded financial filing analysis with traceable citations.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(json.dumps({"event": "request_failed", "request_id": request_id}))
        raise
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(json.dumps({
        "event": "request_complete", "request_id": request_id, "method": request.method,
        "path": request.url.path, "status": response.status_code, "duration_ms": duration_ms,
    }))
    return response


@app.get("/health", response_model=HealthResponse, tags=["operations"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok", version=settings.app_version, documents=len(service.filing_ids()),
        model_provider=service.generator.name,
    )


@app.get("/api/v1/filings", response_model=list[FilingSummary], tags=["analysis"])
def filings() -> list[FilingSummary]:
    unique = {}
    for chunk in service.corpus:
        unique.setdefault(chunk.filing_id, FilingSummary(
            id=chunk.filing_id, company=chunk.company, form=chunk.form,
            fiscal_year=chunk.fiscal_year, sector=chunk.sector,
        ))
    return list(unique.values())


@app.post("/api/v1/analyze", response_model=AnalyzeResponse, tags=["analysis"])
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    if payload.filing_id not in service.filing_ids():
        service.metrics.observe(0, error=True)
        raise HTTPException(status_code=404, detail="Filing not found")
    return service.analyze(payload)


@app.get("/metrics", include_in_schema=False, tags=["operations"])
def metrics() -> Response:
    return Response(service.metrics.as_prometheus(), media_type="text/plain; version=0.0.4")
