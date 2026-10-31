"""Test RAG upgrades one at a time on Tuesday's constructed example.

Same document, chunker and BM25 as tiny_rag.py, across all 25 boundary offsets.
This shows how an upgrade can backfire, not how often it does.
The sentence splitter ignores offsets, so its result is one trial, not 25.
Run: python upgrade_ladder.py
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
QUESTIONS = {
    "original": "What is the deadline for a refund request?",
    "reworded A": "How long do I have to get my money back?",
    "reworded B": "Can I still return this after two weeks?",
}
FACT = "14 days"
SIZE = 25
STOP = set("the a an of for is what to in and on our their it are be by but can who must they this".split())


def tokens(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


def chunk(text, size, offset=0, overlap=0):
    words = text.split()
    parts = [words[:offset]] if offset else []
    parts += [words[i:i + size] for i in range(offset, len(words), size - overlap)]
    return [" ".join(p) for p in parts if p]


def sentences(text):
    return re.split(r"(?<=\.)\s+", text)


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


LADDER = [
    ("baseline, top 1", lambda o: chunk(DOC, SIZE, o), 1),
    ("top 2", lambda o: chunk(DOC, SIZE, o), 2),
    ("top 3", lambda o: chunk(DOC, SIZE, o), 3),
    ("overlap 5, top 1", lambda o: chunk(DOC, SIZE, o, 5), 1),
    ("overlap 10, top 1", lambda o: chunk(DOC, SIZE, o, 10), 1),
    ("overlap 5, top 2", lambda o: chunk(DOC, SIZE, o, 5), 2),
    ("sentences, top 1", lambda o: sentences(DOC), 1),
    ("sentences, top 2", lambda o: sentences(DOC), 2),
]


def evaluate(make_chunks, question, top_k):
    lost, split, words = [], [], 0
    for offset in range(SIZE):
        chunks = make_chunks(offset)
        order, _ = bm25(question, chunks)
        context = [chunks[i] for i in order[:top_k]]
        words += sum(len(c.split()) for c in context)
        if not any(FACT in c for c in chunks):
            split.append(offset)
        if not any(FACT in c for c in context):
            lost.append(offset)
    return lost, split, words / SIZE


for name, question in QUESTIONS.items():
    print(f"\n{name}: {question}")
    for label, make_chunks, top_k in LADDER:
        lost, split, words = evaluate(make_chunks, question, top_k)
        print(f"  {label:20} lost {len(lost):2}/25  split {len(split)}  words {words:3.0f}  offsets {lost}")

q = QUESTIONS["original"]
base = evaluate(LADDER[0][1], q, 1)[0]
over = evaluate(LADDER[3][1], q, 1)[0]
print(f"\nBaseline lost: {base}\nOverlap 5 lost: {over}\nNewly lost: {sorted(set(over) - set(base))}\nRescued: {sorted(set(base) - set(over))}")
for offset in sorted(set(over) - set(base)):
    chunks = chunk(DOC, SIZE, offset, 5)
    order, scores = bm25(q, chunks)
    holder = next(i for i, c in enumerate(chunks) if FACT in c)
    print(f"\noffset {offset}: top score {scores[order[0]]:.2f}, chunk with fact {scores[holder]:.2f}\n  top: {chunks[order[0]]}\n  fact: {chunks[holder]}")
