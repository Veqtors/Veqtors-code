"""Traces one HotpotQA merge. Run multi_query_test.py first, so data/ exists."""
import json
from collections import defaultdict

from common import load, search

QUESTION = 31
extra = json.load(open("generated.json", encoding="utf-8"))["hotpot"]
ids, texts, queries, relevant, vectors = load("hotpot")
lists = [search(vectors, [queries[QUESTION]])[0], *search(vectors, extra["variants"][QUESTION])]

scores = defaultdict(float)
for ranked in lists:
    for rank, doc in enumerate(ranked, start=1):
        scores[int(doc)] += 1 / (60 + rank)
order = sorted(scores, key=scores.get, reverse=True)

print(queries[QUESTION])
print("needs:", sorted(relevant[QUESTION]))
print("plain top 5:", [ids[int(d)] for d in lists[0][:5]])
print("fused top 5:", [f"{ids[d]} {scores[d]:.5f}" for d in order[:5]])
for title in sorted(relevant[QUESTION]):
    doc = ids.index(title)
    print(f"{title}: plain rank {list(map(int, lists[0])).index(doc) + 1}, fused rank {order.index(doc) + 1}, score {scores[doc]:.5f}")
print("step-back, Derrickson question:", extra["step_back"][0])
