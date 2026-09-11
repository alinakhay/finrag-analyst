"""Quick qualitative check for a trained CatalystLens adapter."""

import os

from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

ADAPTER_PATH = os.getenv(
    "CATALYSTLENS_ADAPTER_PATH",
    "artifacts/catalyst-lora",
)


def main() -> None:
    tokenizer = AutoTokenizer.from_pretrained(ADAPTER_PATH)
    model = AutoPeftModelForCausalLM.from_pretrained(
        ADAPTER_PATH,
        device_map="auto",
    )
    messages = [
        {
            "role": "system",
            "content": (
                "Attribute market moves only to evidence, quantify abnormal "
                "returns, cite source IDs, and do not give investment advice."
            ),
        },
        {
            "role": "user",
            "content": (
                "Question: What explains the ASTR move?\n"
                "Evidence [news-01]: Data-centre guidance rose to 34–38%. "
                "Five-day CAR was +6.7% versus SOX."
            ),
        },
    ]
    inputs = tokenizer.apply_chat_template(
        messages,
        add_generation_prompt=True,
        return_tensors="pt",
    ).to(model.device)
    generated = model.generate(inputs, max_new_tokens=160, do_sample=False)
    print(
        tokenizer.decode(
            generated[0][inputs.shape[-1] :],
            skip_special_tokens=True,
        )
    )


if __name__ == "__main__":
    main()
