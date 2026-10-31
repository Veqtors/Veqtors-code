"""RAG-Fusion, step-back and iterative retrieval against plain search.

Downloads SciFact, nfcorpus and HotpotQA (about 35 MB) and uses the saved model output
in generated.json, so it needs no API key. Everything merges with RRF, k = 60.
Setup: pip install -r requirements.txt   Run: python multi_query_test.py
"""
import json
from collections import defaultdict

import numpy as np

from common import load, search

K, RRF_K, RESAMPLES = 5, 60, 10_000
generated = json.load(open("generated.json", encoding="utf-8"))


def fuse(ranked_lists):
    scores = defaultdict(float)
    for ranked in ranked_lists:
        for rank, doc in enumerate(ranked, start=1):
            scores[int(doc)] += 1 / (RRF_K + rank)
    return sorted(scores, key=scores.get, reverse=True)


def score(orders, ids, relevant):
    return np.array([len({ids[j] for j in o[:K]} & t) / min(K, len(t)) for o, t in zip(orders, relevant)])


def report(label, per_query, plain, cost):
    diffs = per_query - plain
    line = f"  {label:<24} {per_query.mean():6.1%}"
    if label != "plain":
        means = np.random.default_rng(0).choice(diffs, (RESAMPLES, len(diffs))).mean(axis=1)
        low, high = np.percentile(means, [2.5, 97.5])
        verdict = "gain" if low > 0 else "loss" if high < 0 else "no clear change"
        line += f"  {diffs.mean() * 100:+5.1f} [{low * 100:+5.1f}, {high * 100:+5.1f}]  helped {(diffs > 0).sum():>3} hurt {(diffs < 0).sum():>3}  {verdict}"
    print(f"{line}  {cost}", flush=True)


print(f"Recall at {K}, change in points with a 95% paired bootstrap interval")
for name in ("scifact", "nfcorpus", "hotpot"):
    ids, texts, queries, relevant, vectors = load(name)
    extra = generated[name]
    plain_top = search(vectors, queries)
    step_top = search(vectors, extra["step_back"])
    follow_top = search(vectors, extra["follow_up"])
    variant_tops = [search(vectors, v) if v else np.empty((0, 50), dtype=int) for v in extra["variants"]]
    print(f"\n{name}: {len(ids):,} documents, {len(queries)} queries, {np.mean([len(t) for t in relevant]):.1f} relevant per query")
    runs = {
        "plain": ([list(r) for r in plain_top], "0 model calls, 1 search"),
        "variants only": ([fuse(v) if len(v) else list(p) for v, p in zip(variant_tops, plain_top)], "1 model call, 4 searches"),
        "RAG-Fusion": ([fuse([p, *v]) for p, v in zip(plain_top, variant_tops)], "1 model call, 5 searches"),
        "step-back only": ([list(r) for r in step_top], "1 model call, 1 search"),
        "step-back + query": ([fuse([p, s]) for p, s in zip(plain_top, step_top)], "1 model call, 2 searches"),
        "iterative, two rounds": ([fuse([p, f]) for p, f in zip(plain_top, follow_top)], "1 model call, 2 searches"),
    }
    plain = score(runs["plain"][0], ids, relevant)
    for label, (orders, cost) in runs.items():
        report(label, score(orders, ids, relevant), plain, cost)
