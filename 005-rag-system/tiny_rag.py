"""A tiny RAG pipeline with no model call. Prints what each stage held.

The document and question are constructed to show one failure. This shows the
mechanism, not how often it happens. Run: python tiny_rag.py
"""
import math
import re
from collections import Counter

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
QUESTION = "What is the deadline for a refund request?"
FACT = "14 days"
STOP = set("the a an of for is what to in and on our their it are be by but can who must they this".split())


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


def run(label, size, offset, top_k=1):
    chunks = chunk(DOC, size, offset)
    order, scores = bm25(QUESTION, chunks)
    context = [chunks[i] for i in order[:top_k]]
    print(f"\n{label}: {len(chunks)} chunks of {size} words, offset {offset}")
    print(f"  in document:      {FACT in DOC}")
    print(f"  whole in a chunk: {any(FACT in c for c in chunks)}")
    print(f"  in the prompt:    {any(FACT in c for c in context)}")
    print(f"  top chunk (score {scores[order[0]]:.2f}): {context[0]}")


run("Boundary A", 25, 0)
run("Boundary B", 25, 16)
run("Boundary C", 25, 19)

fails = sum(FACT not in chunk(DOC, 25, o)[bm25(QUESTION, chunk(DOC, 25, o))[0][0]] for o in range(25))
print()
print(f"Fact missing from the prompt at {fails} of 25 boundary offsets (chunks of 25 words, top 1).")
