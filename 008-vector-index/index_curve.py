"""Exact search, HNSW and IVF: recall, speed, scale and filters.

Uses GloVe-100 from ANN-Benchmarks (about 463 MB, real word vectors) and FAISS,
with no API key. Timings are single-threaded and belong to the machine they ran on.
Setup: pip install -r requirements.txt   Run: python index_curve.py
"""
import hashlib
import pathlib
import shutil
import time
import urllib.request

import faiss
import h5py
import numpy as np

URL = "https://ann-benchmarks.com/glove-100-angular.hdf5"
PATH = pathlib.Path("glove-100-angular.hdf5")
SHA256 = "544af1d5e84e112cd4749571dcfd8ca109818a572f850af75a3a09e093a953c4"
SIZES = [3_000, 10_000, 30_000, 100_000, 300_000, 1_000_000]
EFS = [16, 50, 100, 200, 400]
NPROBES = [1, 5, 10, 20, 50, 100]
K, QUERIES, BUILD_THREADS = 10, 1000, 8

if not PATH.exists():
    print("Downloading GloVe-100...", flush=True)
    request = urllib.request.Request(URL, headers={"User-Agent": "curl/8"})  # the host rejects Python's default
    partial = PATH.with_suffix(".part")
    with urllib.request.urlopen(request) as response, open(partial, "wb") as out:
        shutil.copyfileobj(response, out)
    partial.replace(PATH)
with open(PATH, "rb") as f:
    if hashlib.file_digest(f, "sha256").hexdigest() != SHA256:
        raise SystemExit(f"{PATH} failed its checksum. Delete it and run again.")
with h5py.File(PATH) as f:
    train = np.array(f["train"], dtype="float32")
    queries = np.array(f["test"], dtype="float32")[:QUERIES]
faiss.normalize_L2(train)
faiss.normalize_L2(queries)
rng = np.random.default_rng(0)
order = rng.permutation(len(train))
dim = train.shape[1]


def timed(index, k=K):
    faiss.omp_set_num_threads(1)
    index.search(queries, k)  # warm the caches
    start = time.perf_counter()
    _, ids = index.search(queries, k)
    return (time.perf_counter() - start) / len(queries) * 1000, ids


def recall(ids, truth):
    return float(np.mean([len(set(a) & set(t)) / K for a, t in zip(ids, truth)]))


def hnsw(data, m=16):
    index = faiss.IndexHNSWFlat(dim, m, faiss.METRIC_INNER_PRODUCT)
    index.hnsw.efConstruction = 200
    faiss.omp_set_num_threads(BUILD_THREADS)
    index.add(data)
    return index


print("Scale: top 10, 1,000 queries")
print(f"{'vectors':>9} {'exact ms':>9}  HNSW M=16, recall at ms per query")
for size in SIZES:
    data = train[order[:size]]
    flat = faiss.IndexFlatIP(dim)
    flat.add(data)
    exact_ms, truth = timed(flat)
    index = hnsw(data)
    row = []
    for ef in EFS:
        index.hnsw.efSearch = ef
        ms, ids = timed(index)
        row.append(f"ef{ef} {recall(ids, truth):.3f} at {ms:.3f}")
    print(f"{size:>9,} {exact_ms:>9.3f}  " + "  ".join(row), flush=True)

SIZE = 100_000
data = train[order[:SIZE]]
flat = faiss.IndexFlatIP(dim)
flat.add(data)
_, truth = timed(flat)

print(f"\nIVF at {SIZE:,} vectors")
nlist = int(4 * SIZE ** 0.5)
quantizer = faiss.IndexFlatIP(dim)
ivf = faiss.IndexIVFFlat(quantizer, dim, nlist, faiss.METRIC_INNER_PRODUCT)
faiss.omp_set_num_threads(BUILD_THREADS)
ivf.train(data)
ivf.add(data)
for nprobe in NPROBES:
    ivf.nprobe = nprobe
    ms, ids = timed(ivf)
    print(f"  nlist {nlist} nprobe {nprobe:>3}: recall {recall(ids, truth):.3f} at {ms:.3f} ms")

print(f"\nPost-filter at {SIZE:,} vectors, HNSW ef 200, random labels, top 10")
index = hnsw(data)
index.hnsw.efSearch = 200
for share in (0.5, 0.1, 0.01):
    keep = rng.random(SIZE) < share
    allowed = np.where(keep)[0]
    sub = faiss.IndexFlatIP(dim)
    sub.add(data[allowed])
    _, local = sub.search(queries, K)
    true_ids = allowed[local]
    for over in (1, 3, 10, 30):
        _, ids = index.search(queries, K * over)
        kept = [[i for i in row if i >= 0 and keep[i]][:K] for row in ids]
        hit = np.mean([len(set(a) & set(t)) / K for a, t in zip(kept, true_ids)])
        empty = np.mean([len(a) == 0 for a in kept])
        print(f"  keep {share:>4.0%}, fetch {K * over:>3}: recall {hit:.3f}, empty {empty:.1%}", flush=True)
