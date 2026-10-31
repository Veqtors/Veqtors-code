"""Writes generated.json: query variants, step-back questions and follow-up queries.

Optional, because generated.json is already in the repo. Needs a GPU to finish quickly.
"""
import json
import re

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from common import load, search

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
BATCH = 16
VARIANTS = "Write 4 different search queries for this question, one per line. Output only the queries.\n\n{q}"
STEP_BACK = "Rewrite this as a more general question about the underlying topic or principle. Output only the question.\n\n{q}"
FOLLOW_UP = "Question: {q}\n\nFound so far:\n{found}\n\nWrite one search query for the information still missing. Output only the query."

tokenizer = AutoTokenizer.from_pretrained(MODEL, padding_side="left")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float16 if device == "cuda" else torch.float32).to(device).eval()


def generate(prompts, max_tokens):
    out = []
    for i in range(0, len(prompts), BATCH):
        chats = [tokenizer.apply_chat_template([{"role": "user", "content": p}], tokenize=False, add_generation_prompt=True)
                 for p in prompts[i:i + BATCH]]
        batch = tokenizer(chats, return_tensors="pt", padding=True).to(device)
        with torch.no_grad():
            ids = model.generate(**batch, max_new_tokens=max_tokens, do_sample=False)
        out += tokenizer.batch_decode(ids[:, batch.input_ids.shape[1]:], skip_special_tokens=True)
    return [text.strip() for text in out]


def lines(text):
    cleaned = [re.sub(r"^\s*(\d+[.)]|[-*])\s*", "", line).strip().strip('"') for line in text.splitlines()]
    return [line for line in cleaned if line][:4]


result = {}
for name in ("scifact", "nfcorpus", "hotpot"):
    ids, texts, queries, relevant, vectors = load(name)
    first = search(vectors, queries, depth=3)
    found = ["\n".join(texts[j][:300] for j in row) for row in first]
    result[name] = {
        "variants": [lines(t) for t in generate([VARIANTS.format(q=q) for q in queries], 100)],
        "step_back": generate([STEP_BACK.format(q=q) for q in queries], 40),
        "follow_up": generate([FOLLOW_UP.format(q=q, found=f) for q, f in zip(queries, found)], 40),
    }
    print(name, "done", flush=True)
    json.dump(result, open("generated.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
