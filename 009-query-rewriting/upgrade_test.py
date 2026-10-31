"""Query rewriting, HyDE and reranking, measured on two public datasets.

Downloads SciFact and nfcorpus from BEIR (about 8 MB) and uses the saved model output
in generated.json, so it needs no API key. Reranking runs far faster on a GPU, and
timings belong to the machine they ran on.
Setup: pip install -r requirements.txt   Run: python upgrade_test.py
"""
import hashlib
import json
import pathlib
import time
import urllib.request
import zipfile

import numpy as np
import torch
from fastembed import TextEmbedding
from transformers import AutoModelForSequenceClassification, AutoTokenizer

BASE = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/"
DATASETS = {
    "scifact": "536e14446a0ba56ed1398ab1055f39fe852686ecad24a6306c80c490fa8e0165",
    "nfcorpus": "efe5be03f8c5b86a5870102d0599d227c8c6e2484328e68c6522560385671b0b",
}
RERANKERS = {"MiniLM": "cross-encoder/ms-marco-MiniLM-L-6-v2", "bge-v2-m3": "BAAI/bge-reranker-v2-m3"}
K, DEPTHS, CUTOFFS, BATCH, RESAMPLES = 5, (20, 50), (1, 3, 5, 10, 20, 50), 25, 10_000
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
embedder = TextEmbedding("BAAI/bge-small-en-v1.5")
generated = json.load(open("generated.json", encoding="utf-8"))


def load(name):
    folder = pathlib.Path("data") / name
    if not folder.exists():
        archive = pathlib.Path("data") / f"{name}.zip"
        archive.parent.mkdir(exist_ok=True)
        urllib.request.urlretrieve(f"{BASE}{name}.zip", archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != DATASETS[name]:
            raise SystemExit(f"{archive} failed its checksum. Delete it and run again.")
        zipfile.ZipFile(archive).extractall("data")
    docs = [json.loads(line) for line in open(folder / "corpus.jsonl", encoding="utf-8")]
    queries = {j["_id"]: j["text"] for j in map(json.loads, open(folder / "queries.jsonl", encoding="utf-8"))}
    relevant = {}
    for line in list(open(folder / "qrels" / "test.tsv"))[1:]:
        query, doc, score = line.split("\t")
        if int(score) > 0:
            relevant.setdefault(query, set()).add(doc)
    return docs, queries, relevant


def recall(order, truth, k=K):
    """Share of relevant documents found, capped at k so a perfect top k scores 1."""
    return len(set(order[:k]) & truth) / min(k, len(truth))


def rerank(model, tokenizer, query, candidates):
    scores = []
    for start in range(0, len(candidates), BATCH):
        part = candidates[start:start + BATCH]
        batch = tokenizer([query] * len(part), part, padding=True, truncation=True, max_length=512, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            scores += model(**batch).logits.squeeze(-1).float().tolist()
    return np.argsort(-np.array(scores))


def interval(diffs, rng):
    means = rng.choice(diffs, (RESAMPLES, len(diffs))).mean(axis=1)
    return np.percentile(means, [2.5, 97.5])


def report(label, per_query, plain, ms=None):
    diffs = per_query - plain
    line = f"  {label:<26} {per_query.mean():6.1%}"
    if label != "plain":
        low, high = interval(diffs, np.random.default_rng(0))
        verdict = "gain" if low > 0 else "loss" if high < 0 else "no clear change"
        line += f"  {diffs.mean() * 100:+5.1f} [{low * 100:+5.1f}, {high * 100:+5.1f}]  helped {(diffs > 0).sum():>3} hurt {(diffs < 0).sum():>3}  {verdict}"
    if ms is not None:
        line += f"  {ms:.0f} ms"
    print(line, flush=True)


models = {}
for name, path in RERANKERS.items():
    tokenizer = AutoTokenizer.from_pretrained(path)
    dtype = torch.float16 if DEVICE == "cuda" else torch.float32
    models[name] = (AutoModelForSequenceClassification.from_pretrained(path, dtype=dtype).to(DEVICE).eval(), tokenizer)

print(f"Recall at {K}, change in points with a 95% paired bootstrap interval, device {DEVICE}")
for name in DATASETS:
    docs, queries, relevant = load(name)
    ids = [d["_id"] for d in docs]
    texts = [(d["title"] + " " + d["text"]).strip() for d in docs]
    vectors = np.array(list(embedder.embed(texts, batch_size=64)), dtype="float32")
    extra = generated[name]
    ordered = extra["ids"]
    plain_v = np.array(list(embedder.query_embed([queries[q] for q in ordered])), dtype="float32")
    rewrite_v = np.array(list(embedder.query_embed(extra["rewrite"])), dtype="float32")
    hyde_v = np.array(list(embedder.passage_embed(extra["hyde"])), dtype="float32")
    both_v = plain_v + hyde_v
    both_v /= np.linalg.norm(both_v, axis=1, keepdims=True)
    tops = {label: np.argsort(-(v @ vectors.T), axis=1)[:, :50]
            for label, v in (("plain", plain_v), ("rewrite", rewrite_v), ("HyDE", hyde_v), ("query + HyDE", both_v))}
    truth = [relevant[q] for q in ordered]
    score = lambda orders: np.array([recall(o, t) for o, t in zip(orders, truth)])
    doc_ids = lambda top: [[ids[j] for j in row] for row in top]

    print(f"\n{name}: {len(ids):,} documents, {len(ordered)} queries, {np.mean([len(t) for t in truth]):.1f} relevant per query")
    print("  plain recall at " + ", ".join(
        f"{k}: {np.mean([recall(o, t, k) for o, t in zip(doc_ids(tops['plain']), truth)]):.1%}" for k in CUTOFFS))
    plain = score(doc_ids(tops["plain"]))
    for label, top in tops.items():
        report(label, score(doc_ids(top)), plain)
    runs = [(reranker, depth, "plain") for reranker in models for depth in DEPTHS] + [("bge-v2-m3", 50, "query + HyDE")]
    for reranker, depth, start in runs:
        model, tokenizer = models[reranker]
        began = time.perf_counter()
        orders = []
        for i, q in enumerate(ordered):
            chosen = tops[start][i][:depth]
            order = rerank(model, tokenizer, queries[q], [texts[j] for j in chosen])
            orders.append([ids[chosen[j]] for j in order])
        ms = (time.perf_counter() - began) / len(ordered) * 1000
        report(f"{start}, {reranker} {depth}", score(orders), plain, ms)
