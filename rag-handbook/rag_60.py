"""A whole RAG pipeline in under 60 lines. Prints what each stage held.

Stages: ingest, chunk, embed, retrieve, assemble, answer. The answer step prints
the prompt a model would receive, so no API key and no model download beyond the
small embedding model. Swap one line to call a real model.
The document and question are constructed. Run: python rag_60.py [file.txt]
"""
import sys
from pathlib import Path

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
QUESTION = "What is the deadline for a refund request?"
FACT = "14 days"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
MODEL = TextEmbedding("BAAI/bge-small-en-v1.5")


def chunk(text, size=25, offset=0):
    words = text.split()
    parts = [words[:offset]] if offset else []
    parts += [words[i:i + size] for i in range(offset, len(words), size)]
    return [" ".join(p) for p in parts if p]


def embed(texts):
    vectors = np.array(list(MODEL.embed(texts)))
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


def retrieve(question, chunks, k=1):
    scores = embed(chunks) @ embed([QUERY_PREFIX + question])[0]
    order = np.argsort(-scores)[:k]
    return [(chunks[i], float(scores[i])) for i in order]


def build_prompt(question, hits):
    context = "\n".join(f"- {text}" for text, _ in hits)
    return f"Answer using only this context.\n{context}\nQuestion: {question}\nAnswer:"


def answer(prompt):
    print(prompt)  # swap in: return your_llm(prompt)


def run(text, question, size=25, offset=0, k=1):
    chunks = chunk(text, size, offset)
    hits = retrieve(question, chunks, k)
    print(f"{len(chunks)} chunks of {size} words, offset {offset}, top {k}")
    print(f"  whole in a chunk: {any(FACT in c for c in chunks)}")
    print(f"  in the prompt:    {any(FACT in c for c, _ in hits)}  (top score {hits[0][1]:.3f})")
    answer(build_prompt(question, hits))


if __name__ == "__main__":
    text = Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else DOC
    for offset in (0, 16, 19):
        run(text, QUESTION, offset=offset)
        print()
    lost = [o for o in range(25) if not any(FACT in c for c, _ in retrieve(QUESTION, chunk(text, 25, o)))]
    print(f"Fact missing from the prompt at {len(lost)} of 25 offsets {lost} (chunks of 25 words, top 1).")
