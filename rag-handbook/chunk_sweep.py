"""Chunking ladder with embeddings, same constructed example as issue #6.

Issue #6 ran this ladder with BM25. This runs it with bge-small-en-v1.5 so the
handbook can compare. Constructed example: one document, three questions, 25
boundary offsets. It shows mechanisms, not how often they happen. The sentence
splitter ignores offsets, so its rows are one trial repeated.
Run: python chunk_sweep.py
"""
import re

from rag_60 import DOC, FACT, chunk as plain_chunk, retrieve

QUESTIONS = {
    "original": "What is the deadline for a refund request?",
    "reworded A": "How long do I have to get my money back?",
    "reworded B": "Can I still return this after two weeks?",
}
SIZE = 25


def chunk(text, size, offset=0, overlap=0):
    words = text.split()
    parts = [words[:offset]] if offset else []
    parts += [words[i:i + size] for i in range(offset, len(words), size - overlap)]
    return [" ".join(p) for p in parts if p]


def sentences(text):
    return re.split(r"(?<=\.)\s+", text)


LADDER = [
    ("baseline, top 1", lambda o: chunk(DOC, SIZE, o), 1),
    ("top 2", lambda o: chunk(DOC, SIZE, o), 2),
    ("overlap 5, top 1", lambda o: chunk(DOC, SIZE, o, 5), 1),
    ("overlap 10, top 1", lambda o: chunk(DOC, SIZE, o, 10), 1),
    ("overlap 5, top 2", lambda o: chunk(DOC, SIZE, o, 5), 2),
    ("sentences, top 1", lambda o: sentences(DOC), 1),
    ("sentences, top 2", lambda o: sentences(DOC), 2),
]


def evaluate(make_chunks, question, top_k):
    lost, split = [], []
    for offset in range(SIZE):
        chunks = make_chunks(offset)
        context = [c for c, _ in retrieve(question, chunks, top_k)]
        if not any(FACT in c for c in chunks):
            split.append(offset)
        if not any(FACT in c for c in context):
            lost.append(offset)
    return lost, split


for name, question in QUESTIONS.items():
    print(f"\n{name}: {question}")
    for label, make_chunks, top_k in LADDER:
        lost, split = evaluate(make_chunks, question, top_k)
        print(f"  {label:20} lost {len(lost):2}/25  split {len(split)}  offsets {lost}")
