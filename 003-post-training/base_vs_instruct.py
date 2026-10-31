"""Same architecture, same size, different training: base and instruct checkpoints on four prompts.

Veqtors #3, "The same model, trained three times". Run: python base_vs_instruct.py
Needs: pip install -r requirements.txt. Downloads about 2 GB on first run and loads both models in memory.
"""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

PROMPTS = ["What is the capital of Pakistan?",
           "List three tips for writing readable Python code. Use one short line per tip.",
           "Reply with only the word yes or no: is 17 a prime number?",
           "Translate to French: The meeting is moved to Friday."]
MAX_NEW = 60


def load(model_id):
    return (AutoTokenizer.from_pretrained(model_id),
            AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.float32))


def generate(tok, model, text):
    ids = tok(text, return_tensors="pt")
    out = model.generate(**ids, max_new_tokens=MAX_NEW, do_sample=False)   # greedy: same output every run
    return tok.decode(out[0, ids["input_ids"].shape[1]:], skip_special_tokens=False)


if __name__ == "__main__":
    base, inst = load("Qwen/Qwen2.5-0.5B"), load("Qwen/Qwen2.5-0.5B-Instruct")
    for prompt in PROMPTS:
        chat = inst[0].apply_chat_template([{"role": "user", "content": prompt}],
                                           tokenize=False, add_generation_prompt=True)
        print(f"\n#### {prompt}")
        print("base, raw prompt     :", repr(generate(*base, prompt)))
        print("base, chat template  :", repr(generate(*base, chat)))   # control: format alone isn't the difference
        print("instruct, chat templ.:", repr(generate(*inst, chat)))
