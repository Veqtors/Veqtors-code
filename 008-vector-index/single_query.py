"""Batch against one-at-a-time timing. Seconds for 1,000 queries equal ms per query. Needs the GloVe file from index_curve.py."""
import time, faiss, h5py, numpy as np
with h5py.File("glove-100-angular.hdf5") as f:
    train = np.array(f["train"], dtype="float32")
    q = np.array(f["test"], dtype="float32")[:1000]
faiss.normalize_L2(train); faiss.normalize_L2(q)
order = np.random.default_rng(0).permutation(len(train))
print("blas threshold", faiss.cvar.distance_compute_blas_threshold)
def batch(ix):
    ix.search(q, 10); t = time.perf_counter(); _, I = ix.search(q, 10)
    return (time.perf_counter() - t), I
def single(ix):
    for v in q[:100]: ix.search(v[None], 10)
    t = time.perf_counter()
    for v in q: ix.search(v[None], 10)
    return time.perf_counter() - t
for n in (3000, 10000, 30000, 100000, 300000, 1000000):
    d = train[order[:n]]
    fl = faiss.IndexFlatIP(100); fl.add(d)
    faiss.omp_set_num_threads(1)
    fb, tr = batch(fl); fs = single(fl)
    h = faiss.IndexHNSWFlat(100, 16, faiss.METRIC_INNER_PRODUCT); h.hnsw.efConstruction = 200
    faiss.omp_set_num_threads(8); h.add(d); faiss.omp_set_num_threads(1)
    r = []
    for ef in (16, 50, 100, 200, 400):
        h.hnsw.efSearch = ef
        hb, I = batch(h); hs = single(h)
        rc = np.mean([len(set(a) & set(t)) / 10 for a, t in zip(I, tr)])
        r.append(f"ef{ef} {rc:.3f} b{hb:.3f} s{hs:.3f}")
    print(f"{n:>9,} exact b{fb:.3f} s{fs:.3f} | " + " | ".join(r), flush=True)
