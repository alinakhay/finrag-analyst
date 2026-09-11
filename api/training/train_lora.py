"""Parameter-efficient SFT for grounded news-to-market impact briefs.

Run from api/: python training/train_lora.py
The small default model supports a laptop smoke test. A CUDA runner is recommended
for a portfolio-quality experiment with repeated seeds and a larger instruct model.
"""

import os
from pathlib import Path

import torch
from datasets import load_dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
)

ROOT = Path(__file__).parent
MODEL_ID = os.getenv(
    "CATALYSTLENS_BASE_MODEL",
    "Qwen/Qwen2.5-0.5B-Instruct",
)
OUTPUT_DIR = os.getenv(
    "CATALYSTLENS_ADAPTER_PATH",
    "artifacts/catalyst-lora",
)
MAX_LENGTH = int(os.getenv("CATALYSTLENS_MAX_LENGTH", "768"))


def main() -> None:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, use_fast=True)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    dataset = load_dataset(
        "json",
        data_files={
            "train": str(ROOT / "data" / "train.jsonl"),
            "validation": str(ROOT / "data" / "validation.jsonl"),
        },
    )

    def encode(batch: dict) -> dict:
        text = tokenizer.apply_chat_template(
            batch["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
        return tokenizer(text, truncation=True, max_length=MAX_LENGTH)

    tokenized = dataset.map(encode, remove_columns=dataset["train"].column_names)
    use_cuda = torch.cuda.is_available()
    model_kwargs = {"device_map": "auto"} if use_cuda else {}
    if use_cuda:
        model_kwargs["load_in_8bit"] = True
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, **model_kwargs)
    if use_cuda:
        model = prepare_model_for_kbit_training(model)
    model = get_peft_model(
        model,
        LoraConfig(
            task_type="CAUSAL_LM",
            r=16,
            lora_alpha=32,
            lora_dropout=0.05,
            bias="none",
            target_modules="all-linear",
        ),
    )
    model.print_trainable_parameters()

    arguments = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=float(os.getenv("CATALYSTLENS_EPOCHS", "3")),
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=8,
        learning_rate=2e-4,
        warmup_ratio=0.05,
        weight_decay=0.01,
        logging_steps=5,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        bf16=use_cuda and torch.cuda.is_bf16_supported(),
        fp16=use_cuda and not torch.cuda.is_bf16_supported(),
        report_to="none",
        seed=42,
    )
    trainer = Trainer(
        model=model,
        args=arguments,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
    )
    trainer.train()
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)


if __name__ == "__main__":
    main()
