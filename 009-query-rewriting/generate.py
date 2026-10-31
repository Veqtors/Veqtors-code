"""Writes generated.json: a rewrite and a HyDE passage for every test query.

Optional, because generated.json is already in the repo. Needs a GPU to finish quickly.
Run upgrade_test.py once first, so the datasets are in data/.
"""
import json
import pathlib

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
BATCH = 16
PROMPTS = {
    "rewrite": ("Rewrite this as one short search query for a scientific paper database. Output only the query.\n\n{q}", 40),
    "hyde": ("Write one short passage from a scientific paper abstract that addresses this statement. Output only the passage.\n\n{q}", 120),
}

tokenizer = AutoTokenizer.from_pretrained(MODEL, padding_side="left")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float16 if device == "cuda" else torch.float32).to(device).eval()


def generate(texts, max_tokens):
    out = []
    for i in range(0, len(texts), BATCH):
        chats = [tokenizer.apply_chat_template([{"role": "user", "content": t}], tokenize=False, add_generation_prompt=True)
                 for t in texts[i:i + BATCH]]
        batch = tokenizer(chats, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            ids = model.generate(**batch, max_new_tokens=max_tokens, do_sample=False)
        out += tokenizer.batch_decode(ids[:, batch.input_ids.shape[1]:], skip_special_tokens=True)
    return [text.strip() for text in out]


result = {}
for name in ("scifact", "nfcorpus"):
    folder = pathlib.Path("data") / name
    queries = {j["_id"]: j["text"] for j in map(json.loads, open(folder / "queries.jsonl", encoding="utf-8"))}
    ids = sorted({line.split("\t")[0] for line in list(open(folder / "qrels" / "test.tsv"))[1:]})
    result[name] = {"ids": ids}
    for kind, (prompt, tokens) in PROMPTS.items():
        result[name][kind] = generate([prompt.format(q=queries[q]) for q in ids], tokens)
json.dump(result, open("generated.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
