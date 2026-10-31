"""BM25, embeddings and rank fusion on constructed examples.

Same document, chunker and BM25 as the earlier issues, plus a small local
embedding model (no API key). This shows mechanisms, not how often they happen.
Setup: pip install -r requirements.txt   Run: python hybrid_search.py
"""
import math
import re
from collections import Counter

import numpy as np
from fastembed import TextEmbedding

DOC = (
    "Our returns policy covers every order placed through the online store. "
    "Items must be unused and in their original packaging when they reach us. "
    "Sale items can be exchanged but they cannot be returned for cash. "
    "Shipping costs are paid by the customer unless the item arrived damaged. "
    "Customers who want their money back must write to the support team, "
    "and the deadline for a refund request is 14 days after delivery. "
    "Gift cards are not covered by this policy and they never expire. "
    "Store credit is issued within two working days of an approved exchange. "
    "Our warehouse is closed on public holidays, which can delay processing. "
    "Business customers should contact their account manager about bulk orders."
)
QUESTIONS = {
    "original": "What is the deadline for a refund request?",
    "reworded A": "How long do I have to get my money back?",
    "reworded B": "Can I still return this after two weeks?",
}
FACT = "14 days"
SIZE = 25
ERRORS = [
    "Error E4012 means the card was declined by the bank and the customer should try another card.",
    "Error E4021 means the delivery address could not be verified and the order is on hold until support confirms it.",
    "Error E4102 means the payment gateway timed out and the charge should be retried after ten minutes.",
    "Error E4120 means the warehouse has no stock left and the order will be refunded in full.",
    "Error E4201 means the coupon has expired and the customer pays the normal price at checkout.",
    "Error E4210 means the account is locked after too many failed logins and needs a password reset.",
]
STOP = set("the a an of for is what to in and on our their it are be by but can who must they this".split())
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "  # from the BGE model card

model = TextEmbedding("BAAI/bge-small-en-v1.5")
cache = {}


def tokens(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


def chunk(text, size, offset=0):
    words = text.split()
    parts = [words[:offset]] if offset else []
    parts += [words[i:i + size] for i in range(offset, len(words), size)]
    return [" ".join(p) for p in parts if p]


def bm25(query, docs, k1=1.5, b=0.75):
    tokenized = [tokens(d) for d in docs]
    avg = sum(map(len, tokenized)) / len(tokenized)
    scores = []
    for doc in tokenized:
        tf, score = Counter(doc), 0.0
        for term in tokens(query):
            df = sum(term in d for d in tokenized)
            idf = math.log(1 + (len(docs) - df + 0.5) / (df + 0.5))
            score += idf * tf[term] * (k1 + 1) / (tf[term] + k1 * (1 - b + b * len(doc) / avg))
        scores.append(score)
    return sorted(range(len(docs)), key=lambda i: -scores[i]), scores


def embed(texts):
    missing = [t for t in texts if t not in cache]
    if missing:
        for text, vector in zip(missing, model.embed(missing)):
            cache[text] = vector / np.linalg.norm(vector)
    return np.array([cache[t] for t in texts])


def dense(query, docs):
    scores = embed(docs) @ embed([QUERY_PREFIX + query])[0]
    return [int(i) for i in np.argsort(-scores)], scores


def rrf(rankings, k=60):
    scores = Counter()
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            scores[doc] += 1 / (k + rank)
    return sorted(scores, key=lambda d: -scores[d]), scores


def retrievers(query, docs):
    keyword, scores = bm25(query, docs)
    vector = dense(query, docs)[0]
    matched = [i for i in keyword if scores[i] > 0]
    return {
        "bm25": keyword,
        "dense": vector,
        "rrf": rrf([keyword, vector])[0],
        "rrf matched": rrf([matched, vector])[0],
    }


print("Lost of 25 offsets, chunks of 25 words")
for name, question in QUESTIONS.items():
    for top_k in (1, 2):
        lost = Counter()
        for offset in range(SIZE):
            chunks = chunk(DOC, SIZE, offset)
            for method, order in retrievers(question, chunks).items():
                lost[method] += not any(FACT in chunks[i] for i in order[:top_k])
        print(f"  {name:11} top {top_k}: " + "  ".join(f"{m} {lost[m]:2}" for m in ("bm25", "dense", "rrf", "rrf matched")))

print("\nError codes, top 1")
codes = [e.split()[1] for e in ERRORS]
for code in codes:
    picks = {m: codes[o[0]] for m, o in retrievers(f"What does {code} mean?", ERRORS).items()}
    print(f"  {code}: " + "  ".join(f"{m} {c}{'' if c == code else ' WRONG'}" for m, c in picks.items()))

print("\nTrace: What does E4120 mean?")
query = "What does E4120 mean?"
keyword, scores = bm25(query, ERRORS)
vector, cosine = dense(query, ERRORS)
print("  BM25:  " + ", ".join(f"{codes[i]} {scores[i]:.2f}" for i in keyword))
print("  dense: " + ", ".join(f"{codes[i]} {cosine[i]:.3f}" for i in vector))
for label, ranking in (("rrf", keyword), ("rrf matched", [i for i in keyword if scores[i] > 0])):
    order, fused = rrf([ranking, vector])
    print(f"  {label}: " + ", ".join(f"{codes[i]} {fused[i]:.5f}" for i in order[:3]))

print("\nThe fix's limit: What error means E4120?")
picks = retrievers("What error means E4120?", ERRORS)
print("  " + "  ".join(f"{m} {codes[o[0]]}" for m, o in picks.items()))
