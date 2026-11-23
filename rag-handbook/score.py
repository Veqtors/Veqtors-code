"""Score retrieval on the 20-question set, then name the stage that failed.

Run: python score.py            (full ranking of every chunk for every question)
Metrics: hit@k (did the fact reach the top k?) and MRR (1 / rank of the first chunk with the fact).
Stage label per question: chunking (no chunk holds the fact), ranking (a chunk holds it but sits
below k), or reached (the fact is in the prompt, so any remaining error is the model's).
"""
import math
import re
from collections import Counter

import numpy as np
from fastembed import TextEmbedding

from eval_set import DOCS, QUESTIONS

PREFIX = "Represent this sentence for searching relevant passages: "
MODEL = TextEmbedding("BAAI/bge-small-en-v1.5")
TOKEN = re.compile(r"[a-z0-9][a-z0-9.,-]*[a-z0-9]|[a-z0-9]", re.I)


def tokens(text):
    return [t.lower().strip(".,") for t in TOKEN.findall(text)]


def chunk_words(text, size, offset=0):
    w = text.split()
    return [" ".join(w[i:i + size]) for i in range(offset, len(w), size)]


def dense_rank(question, chunks):
    vecs = np.array(list(MODEL.embed(chunks + [PREFIX + question])))
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
    return list(np.argsort(-(vecs[:-1] @ vecs[-1]), kind="stable"))


def bm25_rank(question, chunks, k1=1.5, b=0.75):
    docs = [tokens(c) for c in chunks]
    avg = sum(map(len, docs)) / len(docs)
    df = Counter(t for d in docs for t in set(d))
    def score(d):
        tf = Counter(d)
        return sum(
            math.log(1 + (len(docs) - df[t] + 0.5) / (df[t] + 0.5)) * tf[t] * (k1 + 1)
            / (tf[t] + k1 * (1 - b + b * len(d) / avg))
            for t in set(tokens(question)) if t in tf
        )
    return list(np.argsort([-score(d) for d in docs], kind="stable"))


def rrf_rank(question, chunks, k=60):
    fused = Counter()
    for ranking in (bm25_rank(question, chunks), dense_rank(question, chunks)):
        for pos, i in enumerate(ranking):
            fused[i] += 1 / (k + pos + 1)
    return sorted(fused, key=lambda i: -fused[i])


def first_rank(ranking, chunks, fact):
    """1-based rank of the first chunk containing the fact, or None if no chunk does."""
    return next((pos + 1 for pos, i in enumerate(ranking) if fact in chunks[i]), None)


def evaluate(chunks, ranker, ks=(1, 3, 5)):
    ranks = [first_rank(ranker(q, chunks), chunks, fact) for q, fact, _ in QUESTIONS]
    out = {f"hit@{k}": sum(r is not None and r <= k for r in ranks) / len(ranks) for k in ks}
    out["MRR"] = sum(1 / r for r in ranks if r) / len(ranks)
    return out, ranks


def stage(rank, k):
    return "chunking" if rank is None else "ranking" if rank > k else "reached"


if __name__ == "__main__":
    assert all(any(f in d for d in DOCS) for _, f, _ in QUESTIONS), "a fact is missing from the docs"
    print(f"{len(DOCS)} chunks, {len(QUESTIONS)} questions\n")
    for name, ranker in (("bm25", bm25_rank), ("dense", dense_rank), ("rrf", rrf_rank)):
        m, ranks = evaluate(DOCS, ranker)
        print(f"{name:6}", "  ".join(f"{key} {v:.2f}" for key, v in m.items()))
        for kind in ("plain", "reworded", "code"):
            rs = [r for r, (_, _, kd) in zip(ranks, QUESTIONS) if kd == kind]
            print(f"  {kind:9} hit@1 {sum(r == 1 for r in rs)}/{len(rs)}")
    def diagnose(label, chunks, ranker, k=3):
        _, ranks = evaluate(chunks, ranker)
        print(f"\n{label}, k={k}: {dict(Counter(stage(r, k) for r in ranks))}")
        for (q, _, _), r in zip(QUESTIONS, ranks):
            if stage(r, k) != "reached":
                print(f"  {stage(r, k):9} rank {r}  {q}")

    diagnose("rrf on the 28 chunks", DOCS, rrf_rank)
    # Same questions after a careless re-chunk: all docs joined and cut at 25 words.
    diagnose("dense on 25-word chunks", chunk_words(" ".join(DOCS), 25), dense_rank)
