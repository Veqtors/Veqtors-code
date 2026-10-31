"""Does a bigger fetch improve HNSW search? Needs the GloVe file from index_curve.py."""
import faiss, h5py, numpy as np
with h5py.File("glove-100-angular.hdf5") as f:
    train = np.array(f["train"], dtype="float32")
    q = np.array(f["test"], dtype="float32")[:1000]
faiss.normalize_L2(train); faiss.normalize_L2(q)
order = np.random.default_rng(0).permutation(len(train))
data = train[order[:100_000]]
flat = faiss.IndexFlatIP(100); flat.add(data)
_, truth = flat.search(q, 20)
ix = faiss.IndexHNSWFlat(100, 16, faiss.METRIC_INNER_PRODUCT)
ix.hnsw.efConstruction = 200
faiss.omp_set_num_threads(8); ix.add(data)
def rec(ids, n):
    return float(np.mean([len(set(a[:n]) & set(t[:n])) / n for a, t in zip(ids, truth)]))
for ef, k in [(200, 10), (200, 20), (200, 100), (200, 300), (300, 10), (300, 300), (400, 10)]:
    ix.hnsw.efSearch = ef
    _, ids = ix.search(q, k)
    print(f"ef {ef} k {k}: returned {np.mean((ids >= 0).sum(1)):.1f}, top10 recall {rec(ids, 10):.3f}, top20 recall {rec(ids, 20) if k >= 20 else float('nan'):.3f}", flush=True)
