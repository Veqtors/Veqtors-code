"""Is the HotpotQA loss caused by the merge? Run multi_query_test.py first, so data/ exists."""
import json
from collections import defaultdict

import numpy as np

from common import load, search

K = 5
extra = json.load(open("generated.json", encoding="utf-8"))["hotpot"]
ids, texts, queries, relevant, vectors = load("hotpot")


def fuse(ranked_lists, weights, rrf_k=60):
    scores = defaultdict(float)
    for ranked, weight in zip(ranked_lists, weights):
        for rank, doc in enumerate(ranked, start=1):
            scores[int(doc)] += weight / (rrf_k + rank)
    return sorted(scores, key=scores.get, reverse=True)


def recall(orders, k=K, cap=True):
    return np.mean([len({ids[j] for j in o[:k]} & t) / (min(k, len(t)) if cap else len(t)) for o, t in zip(orders, relevant)])


plain = search(vectors, queries)
variants = [search(vectors, v) for v in extra["variants"]]
follow_up = search(vectors, extra["follow_up"])
equal = [fuse([p, *v], [1] * (len(v) + 1)) for p, v in zip(plain, variants)]
weighted = [fuse([p, *v], [4] + [1] * len(v)) for p, v in zip(plain, variants)]
keep_three = [list(p[:3]) + [d for d in f if d not in p[:3]] for p, f in zip(plain, follow_up)]

print(f"plain                         {recall(plain):.1%}")
print(f"RAG-Fusion, equal weights     {recall(equal):.1%}")
print(f"RAG-Fusion, original weight 4 {recall(weighted):.1%}")
print(f"keep top 3, then follow-up    {recall(keep_three):.1%}")
print(f"at 20: plain {recall(plain, 20, False):.1%}, RAG-Fusion {recall(equal, 20, False):.1%}")
print(f"both documents in plain top 5 {np.mean([{ids[j] for j in p[:K]} >= t for p, t in zip(plain, relevant)]):.1%}")
