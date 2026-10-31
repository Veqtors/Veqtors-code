"""Loads the three datasets and searches them with bge-small. Vectors are cached in data/."""
import hashlib
import json
import pathlib
import urllib.request
import zipfile

import numpy as np
import pyarrow.parquet as parquet
from fastembed import TextEmbedding

BEIR = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/"
HOTPOT = "https://huggingface.co/api/datasets/hotpotqa/hotpot_qa/parquet/distractor/validation/0.parquet"
SHA256 = {
    "scifact": "536e14446a0ba56ed1398ab1055f39fe852686ecad24a6306c80c490fa8e0165",
    "nfcorpus": "efe5be03f8c5b86a5870102d0599d227c8c6e2484328e68c6522560385671b0b",
    "hotpot": "c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6",
}
HOTPOT_QUESTIONS = 300
DATA = pathlib.Path("data")
embedder = TextEmbedding("BAAI/bge-small-en-v1.5")


def fetch(name, url, suffix):
    DATA.mkdir(exist_ok=True)
    path = DATA / f"{name}{suffix}"
    if not path.exists():
        request = urllib.request.Request(url, headers={"User-Agent": "curl/8"})
        with urllib.request.urlopen(request) as response:
            path.write_bytes(response.read())
    if hashlib.sha256(path.read_bytes()).hexdigest() != SHA256[name]:
        raise SystemExit(f"{path} failed its checksum. Delete it and run again.")
    return path


def load_beir(name):
    folder = DATA / name
    if not folder.exists():
        zipfile.ZipFile(fetch(name, f"{BEIR}{name}.zip", ".zip")).extractall(DATA)
    docs = [json.loads(line) for line in open(folder / "corpus.jsonl", encoding="utf-8")]
    text = {j["_id"]: j["text"] for j in map(json.loads, open(folder / "queries.jsonl", encoding="utf-8"))}
    relevant = {}
    for line in list(open(folder / "qrels" / "test.tsv"))[1:]:
        query, doc, score = line.split("\t")
        if int(score) > 0:
            relevant.setdefault(query, set()).add(doc)
    ordered = sorted(relevant)
    ids = [d["_id"] for d in docs]
    texts = [(d["title"] + " " + d["text"]).strip() for d in docs]
    return ids, texts, [text[q] for q in ordered], [relevant[q] for q in ordered]


def load_hotpot():
    """The first 300 questions, searched over the 10 paragraphs that came with each."""
    table = parquet.read_table(fetch("hotpot", HOTPOT, ".parquet"), columns=["question", "supporting_facts", "context"])
    rows = table.slice(0, HOTPOT_QUESTIONS).to_pylist()
    pool = {}
    for row in rows:
        for title, sentences in zip(row["context"]["title"], row["context"]["sentences"]):
            pool.setdefault(title, title + " " + "".join(sentences))
    relevant = [set(r["supporting_facts"]["title"]) & set(pool) for r in rows]
    return list(pool), list(pool.values()), [r["question"] for r in rows], relevant


def load(name):
    ids, texts, queries, relevant = load_hotpot() if name == "hotpot" else load_beir(name)
    cache = DATA / f"{name}.npy"
    if not cache.exists():
        np.save(cache, np.array(list(embedder.embed(texts, batch_size=64)), dtype="float32"))
    return ids, texts, queries, relevant, np.load(cache)


def search(vectors, texts_to_search, depth=50):
    query_vectors = np.array(list(embedder.query_embed(texts_to_search)), dtype="float32")
    return np.argsort(-(query_vectors @ vectors.T), axis=1)[:, :depth]
