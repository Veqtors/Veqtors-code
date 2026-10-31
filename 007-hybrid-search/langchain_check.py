"""Does the zero-score rank happen in LangChain's own hybrid retriever?

Same six sentences and embedding model as hybrid_search.py, with LangChain's
BM25Retriever (rank_bm25 underneath) and EnsembleRetriever at default settings.
BM25 ties at zero, so which leftovers get ranks depends on document order.
This runs every order of the six sentences, for every code.
Setup: pip install -r requirements.txt   Run: python langchain_check.py
"""
from collections import Counter
from itertools import permutations

import numpy as np
from fastembed import TextEmbedding
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

ERRORS = [
    "Error E4012 means the card was declined by the bank and the customer should try another card.",
    "Error E4021 means the delivery address could not be verified and the order is on hold until support confirms it.",
    "Error E4102 means the payment gateway timed out and the charge should be retried after ten minutes.",
    "Error E4120 means the warehouse has no stock left and the order will be refunded in full.",
    "Error E4201 means the coupon has expired and the customer pays the normal price at checkout.",
    "Error E4210 means the account is locked after too many failed logins and needs a password reset.",
]
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
model = TextEmbedding("BAAI/bge-small-en-v1.5")
unit = lambda v: v / np.linalg.norm(v)
doc_vectors = {e: unit(v) for e, v in zip(ERRORS, model.embed(ERRORS))}
codes = [e.split()[1] for e in ERRORS]
query_vectors = {c: unit(v) for c, v in zip(codes, model.embed([f"{QUERY_PREFIX}What does {c} mean?" for c in codes]))}
code = lambda d: d.page_content.split()[1]


class DenseRetriever(BaseRetriever):
    docs: list
    k: int = 4

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun):
        q = query_vectors[query.split()[2]]
        return sorted(self.docs, key=lambda d: -float(doc_vectors[d.page_content] @ q))[: self.k]


wrong, runs = Counter(), Counter()
picked = Counter()
for order in permutations(ERRORS):
    docs = [Document(page_content=e) for e in order]
    keyword = BM25Retriever.from_documents(docs)
    hybrid = EnsembleRetriever(retrievers=[keyword, DenseRetriever(docs=docs)], weights=[0.5, 0.5])
    for target in codes:
        query = f"What does {target} mean?"
        runs[target] += 1
        assert code(keyword.invoke(query)[0]) == target
        top = code(hybrid.invoke(query)[0])
        if top != target:
            wrong[target] += 1
            picked[target, top] += 1

print("LangChain EnsembleRetriever, default RRF, every order of 6 sentences (720)")
for target in codes:
    print(f"  {target}: wrong top result in {wrong[target]} of {runs[target]} orders")
print("Wrong picks:", dict(picked))
