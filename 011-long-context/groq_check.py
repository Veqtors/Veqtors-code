"""A stronger model on a smaller sample: stuffed against the top 5, on prompts under 8k tokens.

The free tier allows 8,000 tokens a minute, so this throttles from the rate-limit headers.
Needs GROQ_API_KEY in the environment. Answers go to groq_answers.json, so a stopped run resumes.
Run: uv run python groq_check.py
"""
import json
import os
import pathlib
import time
import urllib.error
import urllib.request

import numpy as np

from common import arrange, build_pool, exact, f1, load, render, top_k

MODEL = "openai/gpt-oss-20b"
URL = "https://api.groq.com/openai/v1/chat/completions"
SAMPLE, TARGET = 20, 4_000  # 20 questions stay inside the free tier's 200k tokens a day
OUT = pathlib.Path("groq_answers.json")
KEY = os.environ["GROQ_API_KEY"]
questions, texts, vectors = load()
lengths = [len(t) // 4 for t in texts]  # rough count; the API reports the real one
answers = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}


def call(prompt):
    body = json.dumps({"model": MODEL, "max_tokens": 400, "temperature": 0, "reasoning_effort": "low",
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    request = urllib.request.Request(URL, body, {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json", "User-Agent": "veqtors"})
    for _ in range(8):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                data = json.load(response)
                remaining = int(response.headers.get("x-ratelimit-remaining-tokens", 8000))
            if remaining < TARGET * 1.3:
                time.sleep(45)
            return {"text": (data["choices"][0]["message"]["content"] or "").strip(), "tokens": data["usage"]["prompt_tokens"]}
        except urllib.error.HTTPError as error:
            if error.code != 429:
                raise
            wait = float(error.headers.get("retry-after", 60))
            if wait > 900:
                raise SystemExit(f"Daily limit reached, retry after {wait:.0f} s. Saved answers are kept.")
            time.sleep(wait + 1)
    raise SystemExit("Too many rate-limit retries.")


for i, q in enumerate(questions[:SAMPLE]):
    chosen = build_pool(q, i, TARGET, lengths)
    for label, order in (("stuffed", arrange(q, chosen, i, "shuffled")),
                         ("top 5", top_k(q["question"], chosen, vectors)),
                         ("needed at middle", arrange(q, chosen, i, "middle"))):
        key = f"{label}|{i}"
        if key not in answers:
            answers[key] = call(render(order, texts, q["question"]))
            OUT.write_text(json.dumps(answers, ensure_ascii=False), encoding="utf-8")
    print(i + 1, flush=True)

for label in ("stuffed", "top 5", "needed at middle"):
    rows = [(answers[f"{label}|{i}"], q) for i, q in enumerate(questions[:SAMPLE])]
    print(f"{label:<18} F1 {np.mean([f1(a['text'], q['answer']) for a, q in rows]):6.1%}"
          f"  EM {np.mean([exact(a['text'], q['answer']) for a, q in rows]):6.1%}"
          f"  {np.mean([a['tokens'] for a, _ in rows]):6.0f} tokens")
