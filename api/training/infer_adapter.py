"""Quick qualitative check for a trained adapter."""

import os

from peft import AutoPeftModelForCausalLM
from transformers import AutoTokenizer

ADAPTER_PATH = os.getenv("FINRAG_ADAPTER_PATH", "artifacts/finqa-lora")


def main() -> None:
    tokenizer = AutoTokenizer.from_pretrained(ADAPTER_PATH)
    model = AutoPeftModelForCausalLM.from_pretrained(ADAPTER_PATH, device_map="auto")
    messages = [
        {"role": "system", "content": "Answer only from the evidence and cite its source ID."},
        {
            "role": "user",
            "content": (
                "Question: What changed in credit risk?\n"
                "Evidence [credit-01]: Non-performing CRE loans rose from 1.8% to 2.6%."
            ),
        },
    ]
    inputs = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt"
    ).to(model.device)
    generated = model.generate(inputs, max_new_tokens=160, do_sample=False)
    print(tokenizer.decode(generated[0][inputs.shape[-1] :], skip_special_tokens=True))


if __name__ == "__main__":
    main()

