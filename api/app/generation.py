from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.config import Settings
from app.retrieval import SearchResult


@dataclass(frozen=True)
class GeneratedAnswer:
    answer: str
    bullets: list[str]


class Generator(Protocol):
    name: str

    def generate(self, question: str, results: list[SearchResult]) -> GeneratedAnswer: ...


class ExtractiveGenerator:
    """Deterministic fallback: useful for tests, local demos, and retrieval debugging."""

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
            "The indexed filing does not contain enough evidence to answer safely."
        )
        return GeneratedAnswer(answer=answer, bullets=sentences[2:5] or sentences[:2])


class HuggingFaceAdapterGenerator:
    """Run a local base model, upgrading automatically when a LoRA adapter exists."""

    def __init__(self, settings: Settings):
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as error:
            raise RuntimeError(
                "Install the training extra before using FINRAG_MODEL_PROVIDER=huggingface"
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
                raise RuntimeError("Install the training extra to serve a LoRA adapter") from error
            self.model = AutoPeftModelForCausalLM.from_pretrained(model_path, device_map="auto")
        else:
            self.model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto")
        self.model.eval()

    def generate(self, question: str, results: list[SearchResult]) -> GeneratedAnswer:
        evidence = "\n".join(
            f"[{result.chunk.id}] {result.chunk.text}" for result in results
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a cautious financial risk analyst. Answer only from the supplied "
                    "evidence, quantify changes, and cite source IDs."
                ),
            },
            {"role": "user", "content": f"Question: {question}\nEvidence:\n{evidence}"},
        ]
        inputs = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt"
        ).to(self.model.device)
        with self.torch.inference_mode():
            output = self.model.generate(inputs, max_new_tokens=220, do_sample=False)
        answer = self.tokenizer.decode(
            output[0][inputs.shape[-1] :], skip_special_tokens=True
        ).strip()
        return GeneratedAnswer(answer=answer, bullets=[])


def build_generator(settings: Settings) -> Generator:
    if settings.model_provider == "huggingface":
        return HuggingFaceAdapterGenerator(settings)
    return ExtractiveGenerator()
