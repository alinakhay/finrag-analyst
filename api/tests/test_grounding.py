from app.generation import GeneratedAnswer
from app.grounding import ABSTENTION, validate_cited_summary
from app.market import MarketAnalysisService
from app.models import MarketAnalyzeRequest, MarketEvidence
from evaluation.evaluate import passes_release_gate, run


def _evidence() -> list[MarketEvidence]:
    return [
        MarketEvidence(
            id="event-one",
            category="Guidance",
            direction="positive",
            headline="Revenue guidance increased",
            source="Issuer release",
            time="08:00 ET",
            confidence=90,
            quote="Revenue guidance increased by ten percent.",
            interpretation="A positive earnings revision.",
        )
    ]


def test_citation_validator_accepts_supported_ids() -> None:
    result = validate_cited_summary("Guidance increased [event-one].", _evidence())

    assert result.validation.valid is True
    assert result.validation.cited_ids == ["event-one"]
    assert result.validation.abstained is False


def test_citation_validator_abstains_on_unknown_or_missing_ids() -> None:
    unknown = validate_cited_summary("Guidance increased [invented-source].", _evidence())
    missing = validate_cited_summary("Guidance increased.", _evidence())

    assert unknown.text == ABSTENTION
    assert unknown.validation.unsupported_ids == ["invented-source"]
    assert unknown.validation.valid is False
    assert missing.validation.uncited_claim_count == 1
    assert missing.validation.valid is False


def test_irrelevant_question_returns_safe_abstention() -> None:
    result = MarketAnalysisService().analyze(
        MarketAnalyzeRequest(
            asset_id="astr",
            question="Was a dividend declared?",
        )
    )

    assert result.evidence == []
    assert result.summary == ABSTENTION
    assert result.citation_validation.valid is True
    assert result.citation_validation.abstained is True


class UnsupportedCitationGenerator:
    def generate_market(self, question, asset, evidence, metrics):
        del question, asset, evidence, metrics
        return GeneratedAnswer("A fabricated claim [not-retrieved].")


def test_generated_unsupported_citation_triggers_abstention() -> None:
    result = MarketAnalysisService(generator=UnsupportedCitationGenerator()).analyze(
        MarketAnalyzeRequest(
            asset_id="astr",
            question="What changed in data-centre guidance?",
        )
    )

    assert result.summary == ABSTENTION
    assert result.citation_validation.valid is False
    assert result.citation_validation.abstained is True


def test_expanded_evaluation_passes_release_gate() -> None:
    metrics = run()

    assert metrics["cases"] == 18
    assert metrics["answerable_cases"] == 12
    assert metrics["no_answer_cases"] == 6
    assert metrics["citation_validity"] == 1.0
    assert metrics["safe_abstention_accuracy"] == 1.0
    assert passes_release_gate(metrics) is True
    assert passes_release_gate({**metrics, "citation_validity": 0.9}) is False
