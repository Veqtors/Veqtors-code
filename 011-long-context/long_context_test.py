"""Everything in the prompt against the top 5 retrieved, on the same HotpotQA questions.

Each question gets a pool: its own 10 paragraphs, then random others up to about 4k and
16k tokens. Answers are saved to answers.json as they arrive, so a stopped run resumes.
Needs a GPU. Setup: uv pip install -r requirements.txt   Run: uv run python long_context_test.py
"""
import json
import pathlib
import time

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from common import arrange, build_pool, exact, f1, load, render, top_k

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
SIZES = {"own10": 0, "4k": 4_000, "16k": 16_000}
PLACEMENTS = ("start", "middle", "end")
RESAMPLES = 10_000
CHUNK = 1024
OUT = pathlib.Path("answers.json")

tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float16).to("cuda").eval()
questions, texts, vectors = load()
lengths = [len(tokenizer.encode(t)) for t in texts]
answers = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
STOP = set(model.generation_config.eos_token_id)


def prefill(tokens):
    """Feeds the prompt in chunks. Each chunk attends to the KV cache, so memory stays flat."""
    cache = output = None
    for i in range(0, len(tokens), CHUNK):
        ids = torch.tensor([tokens[i:i + CHUNK]], device="cuda")
        output = model(input_ids=ids, past_key_values=cache, use_cache=True)
        cache = output.past_key_values
    return output.logits[0, -1], cache


@torch.no_grad()
def ask(prompt):
    chat = tokenizer.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True)
    tokens = tokenizer.encode(chat)
    start = time.perf_counter()
    logits, cache = prefill(tokens)
    torch.cuda.synchronize()
    prefill_seconds = time.perf_counter() - start
    reply = []
    for _ in range(24):
        token = int(logits.argmax())
        if token in STOP:
            break
        reply.append(token)
        output = model(input_ids=torch.tensor([[token]], device="cuda"), past_key_values=cache, use_cache=True)
        logits, cache = output.logits[0, -1], output.past_key_values
    return {"text": tokenizer.decode(reply, skip_special_tokens=True).strip(), "tokens": len(tokens), "seconds": prefill_seconds}


@torch.no_grad()
def check_chunking():
    tokens = tokenizer.encode(" ".join(texts[:30]))[:3_000]
    whole = model(input_ids=torch.tensor([tokens], device="cuda")).logits[0, -1]
    chunked, _ = prefill(tokens)
    gap = (whole - chunked).abs().max().item()
    same = int(whole.argmax()) == int(chunked.argmax())
    print(f"chunk check on {len(tokens)} tokens: same next token {same}, largest logit gap {gap:.4f}", flush=True)
    if not same:
        raise SystemExit("Chunked prompts changed the output.")


check_chunking()


def methods(q, i):
    yield "needed only", [j for j in q["needed"]]
    for label, target in SIZES.items():
        chosen = build_pool(q, i, target, lengths)
        yield f"stuffed {label}", arrange(q, chosen, i, "shuffled")
        yield f"top 5 from {label}", top_k(q["question"], chosen, vectors)
    chosen = build_pool(q, i, SIZES["16k"], lengths)
    for place in PLACEMENTS:
        yield f"16k, needed at {place}", arrange(q, chosen, i, place)


for i, q in enumerate(questions):
    for label, order in methods(q, i):
        key = f"{label}|{i}"
        if key in answers:
            continue
        answers[key] = ask(render(order, texts, q["question"]))
        answers[key]["found"] = sum(j in order for j in q["needed"]) / max(len(q["needed"]), 1)
    if i % 10 == 9:
        OUT.write_text(json.dumps(answers, ensure_ascii=False), encoding="utf-8")
        print(i + 1, "questions", f"peak {torch.cuda.max_memory_allocated() / 2**30:.2f} GiB", flush=True)
OUT.write_text(json.dumps(answers, ensure_ascii=False), encoding="utf-8")

labels = sorted({k.split("|")[0] for k in answers})
per = {l: [answers[f"{l}|{i}"] for i in range(len(questions))] for l in labels}
score = {l: np.array([f1(a["text"], q["answer"]) for a, q in zip(per[l], questions)]) for l in labels}
base = score["top 5 from 16k"]
print(f"\n{len(questions)} questions. F1, exact match, change against top 5 from 16k with a 95% paired bootstrap interval")
for label in labels:
    diffs = score[label] - base
    means = np.random.default_rng(0).choice(diffs, (RESAMPLES, len(diffs))).mean(axis=1)
    low, high = np.percentile(means, [2.5, 97.5])
    em = np.mean([exact(a["text"], q["answer"]) for a, q in zip(per[label], questions)])
    tokens = np.mean([a["tokens"] for a in per[label]])
    seconds = np.mean([a["seconds"] for a in per[label]])
    found = np.mean([a["found"] for a in per[label]])
    print(f"{label:<24} F1 {score[label].mean():6.1%}  EM {em:6.1%}  {diffs.mean() * 100:+5.1f} [{low * 100:+5.1f}, {high * 100:+5.1f}]"
          f"  helped {(diffs > 0).sum():>3} hurt {(diffs < 0).sum():>3}  needed in prompt {found:6.1%}  {tokens:7.0f} tokens  {seconds:5.2f} s")
print(f"peak GPU memory {torch.cuda.max_memory_allocated() / 2**30:.2f} GiB")
