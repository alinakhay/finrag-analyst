import re
from dataclasses import dataclass

from app.models import CitationValidation, MarketEvidence

CITATION_PATTERN = re.compile(r"\[([a-z0-9][a-z0-9-]*)\]", re.IGNORECASE)
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
ABSTENTION = (
    "I cannot attribute this move from the available evidence. "
    "A human analyst should review additional sources."
)


@dataclass(frozen=True)
class GuardedSummary:
    text: str
    validation: CitationValidation


def safe_abstention(reason: str, *, validation_failed: bool = False) -> GuardedSummary:
    return GuardedSummary(
        text=ABSTENTION,
        validation=CitationValidation(
            valid=not validation_failed,
            cited_ids=[],
            unsupported_ids=[],
            uncited_claim_count=0,
            abstained=True,
            reason=reason,
        ),
    )


def validate_cited_summary(answer: str, evidence: list[MarketEvidence]) -> GuardedSummary:
    """Require each answer sentence to cite only evidence returned for this request."""
    allowed_ids = {item.id for item in evidence}
    cited_ids = list(dict.fromkeys(CITATION_PATTERN.findall(answer)))
    unsupported_ids = sorted(set(cited_ids) - allowed_ids)
    sentences = [
        sentence.strip()
        for sentence in SENTENCE_PATTERN.split(answer)
        if sentence.strip()
    ]
    uncited_claim_count = sum(not CITATION_PATTERN.search(sentence) for sentence in sentences)
    valid = bool(cited_ids) and not unsupported_ids and uncited_claim_count == 0

    if not valid:
        reasons = []
        if not cited_ids:
            reasons.append("no evidence IDs were cited")
        if unsupported_ids:
            reasons.append("unsupported evidence IDs were cited")
        if uncited_claim_count:
            reasons.append(f"{uncited_claim_count} sentence(s) had no citation")
        return GuardedSummary(
            text=ABSTENTION,
            validation=CitationValidation(
                valid=False,
                cited_ids=cited_ids,
                unsupported_ids=unsupported_ids,
                uncited_claim_count=uncited_claim_count,
                abstained=True,
                reason="; ".join(reasons),
            ),
        )

    return GuardedSummary(
        text=answer,
        validation=CitationValidation(
            valid=True,
            cited_ids=cited_ids,
            unsupported_ids=[],
            uncited_claim_count=0,
            abstained=False,
            reason="Every sentence cites an evidence ID returned for this request.",
        ),
    )
