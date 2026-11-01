"""HotpotQA loader and the prompt pools. Vectors and the dataset are cached in data/."""
import hashlib
import pathlib
import random
import re
import string
import urllib.request
from collections import Counter

import numpy as np
import pyarrow.parquet as parquet
from fastembed import TextEmbedding

HOTPOT = "https://huggingface.co/api/datasets/hotpotqa/hotpot_qa/parquet/distractor/validation/0.parquet"
SHA256 = "c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6"
QUESTIONS = 300
DATA = pathlib.Path("data")
PROMPT = "Answer the question using only these documents. Reply with the answer alone, as few words as possible.\n\n{docs}\n\nQuestion: {q}"
embedder = TextEmbedding("BAAI/bge-small-en-v1.5")


def load():
    """The first 300 questions, as on Dec 18. Each row keeps its own 10 paragraphs."""
    DATA.mkdir(exist_ok=True)
    path = DATA / "hotpot.parquet"
    if not path.exists():
        request = urllib.request.Request(HOTPOT, headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(request) as response:
            path.write_bytes(response.read())
    if hashlib.sha256(path.read_bytes()).hexdigest() != SHA256:
        raise SystemExit(f"{path} failed its checksum. Delete it and run again.")
    columns = ["question", "answer", "supporting_facts", "context"]
    rows = parquet.read_table(path, columns=columns).slice(0, QUESTIONS).to_pylist()
    pool = {}
    for row in rows:
        for title, sentences in zip(row["context"]["title"], row["context"]["sentences"]):
            pool.setdefault(title, title + ". " + "".join(sentences))
    titles = list(pool)
    index = {t: i for i, t in enumerate(titles)}
    questions = [{
        "question": r["question"],
        "answer": r["answer"],
        "needed": sorted({index[t] for t in r["supporting_facts"]["title"] if t in index}),
        "own": sorted({index[t] for t in r["context"]["title"]}),
    } for r in rows]
    cache = DATA / "paragraphs.npy"
    texts = [pool[t] for t in titles]
    if not cache.exists():
        np.save(cache, np.array(list(embedder.embed(texts, batch_size=64)), dtype="float32"))
    return questions, texts, np.load(cache)


def build_pool(q, seed, target, lengths):
    """The question's own 10 paragraphs, then random others until the target token count.

    A fixed seed per question makes each smaller pool a subset of the larger ones.
    """
    chosen = list(q["own"])
    rest = [i for i in range(len(lengths)) if i not in set(q["own"])]
    random.Random(seed).shuffle(rest)
    total = sum(lengths[i] for i in chosen)
    for i in rest:
        if total >= target:
            break
        chosen.append(i)
        total += lengths[i]
    return chosen


def arrange(q, chosen, seed, placement):
    """Order a pool. Placement puts the needed paragraphs together at a chosen point."""
    others = [i for i in chosen if i not in q["needed"]]
    random.Random(seed).shuffle(others)
    if placement == "shuffled":
        order = others + q["needed"]
        random.Random(seed + 1).shuffle(order)
        return order
    cut = {"start": 0, "middle": len(others) // 2, "end": len(others)}[placement]
    return others[:cut] + q["needed"] + others[cut:]


def render(order, texts, question):
    docs = "\n\n".join(f"[{n}] {texts[i]}" for n, i in enumerate(order, start=1))
    return PROMPT.format(docs=docs, q=question)


def top_k(question, chosen, vectors, k=5):
    query = np.array(list(embedder.query_embed([question])), dtype="float32")[0]
    scores = vectors[chosen] @ query
    return [chosen[j] for j in np.argsort(-scores)[:k]]


def normalize(text):
    text = "".join(c for c in text.lower() if c not in set(string.punctuation))
    text = re.sub(r"\b(a|an|the)\b", " ", text)
    return " ".join(text.split())


def f1(prediction, answer):
    """HotpotQA's scoring: token overlap after normalizing, with yes and no needing an exact match."""
    pred, gold = normalize(prediction), normalize(answer)
    if gold in ("yes", "no", "noanswer") or pred in ("yes", "no", "noanswer"):
        return float(pred == gold)
    a, b = pred.split(), gold.split()
    same = sum((Counter(a) & Counter(b)).values())
    if not same:
        return 0.0
    precision, recall = same / len(a), same / len(b)
    return 2 * precision * recall / (precision + recall)


def exact(prediction, answer):
    return float(normalize(prediction) == normalize(answer))
