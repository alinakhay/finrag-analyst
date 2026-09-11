from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from app.config import Settings
from app.retrieval import SearchResult


@dataclass(frozen=True)
class GeneratedAnswer:
    answer: str
    bullets: list[str]


class Generator(Protocol):
    name: str

    def generate(self, question: str, results: list[SearchResult]) -> GeneratedAnswer: ...

    def generate_market(
        self,
        question: str,
        asset: dict[str, Any],
        evidence: list[Any],
        metrics: Any,
    ) -> GeneratedAnswer: ...


class ExtractiveGenerator:
    """Deterministic fallback for tests, local demos, and attribution debugging."""

    name = "extractive"

    def generate(self, question: str, results: list[SearchResult]) -> GeneratedAnswer:
        del question
        sentences = [
            sentence
            for result in results[:2]
            for sentence in result.chunk.text.split(". ")
            if len(sentence.strip()) > 35
        ]
        sentences = [sentence.rstrip(".") + "." for sentence in sentences]
        answer = " ".join(sentences[:2]) or (
            "The indexed document does not contain enough evidence to answer safely."
        )
        return GeneratedAnswer(answer=answer, bullets=sentences[2:5] or sentences[:2])

    def generate_market(
        self,
        question: str,
        asset: dict[str, Any],
        evidence: list[Any],
        metrics: Any,
    ) -> GeneratedAnswer:
        del question, evidence, metrics
        return GeneratedAnswer(answer=asset["narrative"], bullets=[])


class HuggingFaceAdapterGenerator:
    """Run a local base model, upgrading automatically when a LoRA adapter exists."""

    def __init__(self, settings: Settings):
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as error:
            raise RuntimeError(
                "Install the training extra before using "
                "CATALYSTLENS_MODEL_PROVIDER=huggingface"
            ) from error
        self.torch = torch
        adapter_path = Path(settings.adapter_path)
        has_adapter = (adapter_path / "adapter_config.json").exists()
        model_path = str(adapter_path) if has_adapter else settings.base_model
        self.name = "huggingface-lora" if has_adapter else "huggingface-base"
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        if has_adapter:
            try:
                from peft import AutoPeftModelForCausalLM
            except ImportError as error:
                raise RuntimeError(
                    "Install the training extra to serve a LoRA adapter"
                ) from error
            self.model = AutoPeftModelForCausalLM.from_pretrained(
                model_path,
                device_map="auto",
            )
        else:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map="auto",
            )
        self.model.eval()

    def _complete(self, messages: list[dict[str, str]]) -> str:
        inputs = self.tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(self.model.device)
        with self.torch.inference_mode():
            output = self.model.generate(
                inputs,
                max_new_tokens=220,
                do_sample=False,
            )
        return self.tokenizer.decode(
            output[0][inputs.shape[-1] :],
            skip_special_tokens=True,
        ).strip()

    def generate(self, question: str, results: list[SearchResult]) -> GeneratedAnswer:
        evidence = "\n".join(
            f"[{result.chunk.id}] {result.chunk.text}" for result in results
        )
        answer = self._complete(
            [
                {
                    "role": "system",
                    "content": (
                        "Answer only from supplied evidence, quantify changes, "
                        "cite source IDs, and abstain when support is weak."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\nEvidence:\n{evidence}",
                },
            ]
        )
        return GeneratedAnswer(answer=answer, bullets=[])

    def generate_market(
        self,
        question: str,
        asset: dict[str, Any],
        evidence: list[Any],
        metrics: Any,
    ) -> GeneratedAnswer:
        evidence_text = "\n".join(
            f"[{item.id}] {item.headline}. {item.quote}" for item in evidence
        )
        prompt = (
            f"Asset: {asset['ticker']} vs {asset['benchmark']}\n"
            f"Question: {question}\n"
            f"Five-day cumulative abnormal return: "
            f"{metrics.cumulative_abnormal_return:+.2f}%\n"
            f"Volume z-score: {metrics.volume_z_score:.2f}\n"
            f"Evidence:\n{evidence_text}"
        )
        answer = self._complete(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a market catalyst analyst. Attribute price moves "
                        "only to supplied evidence, distinguish initiating from "
                        "reinforcing news, quantify abnormal return, cite source "
                        "IDs, and do not give investment advice."
                    ),
                },
                {"role": "user", "content": prompt},
            ]
        )
        return GeneratedAnswer(answer=answer, bullets=[])


def build_generator(settings: Settings) -> Generator:
    if settings.model_provider == "huggingface":
        return HuggingFaceAdapterGenerator(settings)
    return ExtractiveGenerator()
