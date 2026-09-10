import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    id: str
    filing_id: str
    company: str
    form: str
    fiscal_year: int
    sector: str
    section: str
    page: int
    text: str
    risk_category: str


DATA_PATH = Path(__file__).parent.parent / "data" / "filings.json"


@lru_cache
def load_corpus() -> tuple[Chunk, ...]:
    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return tuple(Chunk(**item) for item in payload)

