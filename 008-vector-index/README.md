# What a vector index skips — runnable companion

Two paths: a quick standard-library illustration, and the optional historical
FAISS experiment. The small lab explains search; its graph and coordinates are
invented. The stored GloVe results measure an actual implementation.

## 1. Quick reader lab (no installation or download)

From the repository root, with Python 3.9 or newer:

```powershell
python -B 008-vector-index/reader_lab.py
python -B 008-vector-index/reader_lab.py --check
```

Only the standard library is used. No network, FAISS import, filesystem writes,
or import-time execution. `--check` runs deterministic assertions and prints
`PASS: deterministic lab checks`. No timing claim is made for this Python lab.

### What the graph does

Coordinates: A=0, B=2, C=5, D=8, E=9, F=12, G=15, H=20.
Query=10; distance is the absolute gap; **k=3 in both runs**. Exact top three:
**E,D,F**, with gaps 1,2,2. Alphabetical ID order resolves ties for selection,
eviction and display. Admission and stopping compare distances alone.

Upper undirected links: A–C, C–H; entry A. Bottom undirected links:
A–B, B–C, C–D, C–G, D–F, G–H, H–E.

The lab implements the search skeleton of HNSW paper Algorithms 2 and 5 with
sorted lists instead of priority queues, single entry per layer, and deterministic
ties. It does **not** implement HNSW construction, random levels, connection
selection or pruning. In particular this hand-wired 1D graph lacks some local
links a constructed proximity graph could have. It illustrates how exploration
can miss a neighbour; it is not evidence that HNSW would build this topology.
`M` (graph connectivity) and `efConstruction` (build-time exploration) are outside
the lab. Its bottom `ef` corresponds conceptually to query-time `efSearch`, not
to a visit counter or the requested number of returned IDs. The lab enforces
`ef >= k`; this is not a claim that every FAISS version rejects `efSearch < k`.

Exact checked receipts (lists are in event order):

| Run | Upper distance-evaluated / expanded | Lower distance-evaluated | Lower expanded | Returned / recall@3 |
|---|---|---|---|---|
| ef3 | A,C,H / A,C | C,B,D,G,F,H | C,D,F,G | D,F,C / 2/3 = 66.666…% |
| ef8 | A,C,H / A,C | C,B,D,G,F,H,A,E | C,D,F,G,B,A,H,E | E,D,F / 3/3 = 100% |

“Distance-evaluated” means a gap was computed; “expanded” means its adjacency
list was inspected. Counts are per layer. Upper descent ends at C (gap 5);
H (gap 10) was evaluated, not expanded. Narrow search evaluates six lower-layer
IDs and expands four, despite ef=3. Across layers it evaluates seven unique IDs
using nine gap computations (per-layer distance caches). Wide search evaluates
eight unique IDs using eleven gap computations. These are work counts, not
benchmarked speedups; even the narrow run computes more gaps than the eight-point
exact scan when upper-layer repeats are counted.

Keep the frontier C distinct from retained best W in the paper. After finding F,
W is D,F,C. G was evicted from W but remains queued at gap 5. The stop comparison
is **strict `>`**, so G still expands at equality and evaluates H, which is rejected
at gap 10. Next B has gap 8 > worst retained gap 5, so narrow search stops without
expanding B or H. It never evaluates E. With ef8, H is retained and eventually
expanded, exposing E. No step chooses an unlinked node or uses exact answers to
guide the approximate search.

## Fresh-value checkpoint

These are **invented practice values**, not graph-search or FAISS measurements.

1. Query=12, k=4; J=-4, K=1, L=6, M=10, N=13, P=18, R=25.
   Find exact top four using gap then ID order. Approximate IDs are N,M,P,R.
   Calculate recall@4.
2. A separate practice grid has fast: 90% at .20 ms; balanced: 96% at .45 ms;
   deep: 99% at .90 ms. Choose the fastest tested option satisfying **recall ≥95%
   and time ≤.50 ms**. Repeat for recall ≥98% and the same time budget.

<details>
<summary>Answers</summary>

1. Gaps in ascending order: N=1, M=2, L=6, P=6, K=11, R=13, J=16.
   Exact N,M,L,P; overlap N,M,P is three IDs; recall=3/4=75%.
2. Balanced qualifies at 95%/.50 ms. Fast fails recall; deep fails time.
   At 98%/.50 ms **none** qualifies. Do not silently lower the target.

</details>

## Reading the actual stored measurements

`RESULTS.md` contains the full tables and secondary checks; `RESULTS.txt` contains
the main raw output. Times below are batch-average ms/query, not service p95/p99.

- 3,000 vectors: exact 100%/.037; ef50 95.6%/.034; ef100 99.3%/.063;
  ef200 99.9%/.128; ef400 100.0%/.284 (display-rounded).
- At recall ≥99% **and strictly faster than exact**, no tested HNSW setting at
  3,000 qualifies. Exact remains a quality-qualified baseline. At recall ≥95%,
  ef50 does qualify as faster in these rounded historical rows.
- 100,000: exact 100%/1.848; ef400 97.3%/.658. At recall ≥99% and time ≤1 ms,
  none of the tested choices qualifies: exact misses the time limit; all tested
  HNSW rows miss recall. This is **not** a matched-99% speed crossover.
- Fixed ef100 recovers 99.3% at 3,000 and 88.4% at 100,000 in this run.
  Re-evaluate at the intended size; do not infer a universal monotonic law.

Exact-ID agreement measures fidelity to a distance ranking, not semantic
relevance or answer correctness. This script computes a fresh exact answer key
for every sampled corpus, rather than reusing full-dataset ground truth.
ANN-Benchmarks' current plotting code uses distance-threshold recall with a
1e-3 tolerance; this companion's historical code uses strict ID overlap. These
are related measures, not guaranteed identical on ties or near-ties.

## 2. Optional full historical FAISS benchmark (~463 MiB download)

**Not run again for the 2026-11-03 research refresh.** Existing receipts state
FAISS 1.15.1; `requirements.txt` pins `faiss-cpu==1.15.1` and `numpy==2.5.4`,
and leaves `h5py` unpinned. Treat these as historical artifact versions, not a
verified currently installable environment. CPU model, OS, BLAS, original Python
version and h5py version were not recorded. Current-machine compatibility and
performance are unknown. The quick lab is independent of these packages.

For an intentional new run, open a terminal **in this `code` directory** (the
scripts resolve the dataset relative to the current working directory). Use a
separate environment with Python ≥3.11 (`hashlib.file_digest` is used):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -u index_curve.py
.\.venv\Scripts\python.exe -u single_query.py
.\.venv\Scripts\python.exe -u fetch_vs_ef.py
```

If those pins are unavailable on your Python/platform, stop: a supported-version
port would be a **new** experiment, not a silent reproduction of these receipts.
Record actual package versions and machine details alongside any new output.
Commands print to the terminal; do not redirect them over `RESULTS.md` or
`RESULTS.txt`. The full sweep builds up to one million vectors and can take
substantial time/RAM. `single_query.py` and `fetch_vs_ef.py` require the downloaded
file; the latter does not explicitly pin search threads, so use it only as an
ID/recall receipt, not single-thread timing evidence.

Dataset URL: https://ann-benchmarks.com/glove-100-angular.hdf5

Expected dataset SHA-256 (checked by `index_curve.py` before loading):
`544af1d5e84e112cd4749571dcfd8ca109818a572f850af75a3a09e093a953c4`.
This refresh inspected the checksum code; it did not download/re-hash the dataset.
The upstream listing labels it 463 MB; the brief describes roughly 463 MiB.
Neither is a fresh byte-size measurement here.

Experiment contract from `index_curve.py`: GloVe-100, 100 dimensions; first
1,000 test queries; normalized float32 train/query vectors; inner product;
seed-0 permutation of train, nested size prefixes; k=10; IndexFlatIP ground
truth recomputed per prefix; IndexHNSWFlat M=16, efConstruction=200; efSearch
16/50/100/200/400. Builds explicitly use 8 OpenMP threads; searches explicitly
use 1. One warm-up batch then one timed batch per setting; elapsed time divided
by 1,000. No repetitions/confidence intervals, no build-time or memory benchmark.
Construction and machine/library differences can change results.

### Historical artifact fingerprints

Git blob hashes inspected on 2026-11-03 (not dataset SHA-256):

| File | `git hash-object` |
|---|---|
| index_curve.py | 5ee90ae7dc52c2212130e5ec86338c0dddc1bffe |
| RESULTS.md | f5b37aa4cc6625b664814b47ff7c8ecb6be97860 |
| RESULTS.txt | 4e5adc3bc177148fcbce393ecdcef5db0812c3b1 |
| requirements.txt | b9424622ff13d1f069034659847317425505ce34 |
| single_query.py | bd0432787ed424becf0427df47a26403831322c9 |
| fetch_vs_ef.py | 0751250dcd96166ee6b6af4f2b9ff78578d31f83 |

## Primary sources

- HNSW paper, Algorithms 2 and 5 (PDF pp. 4–5): https://arxiv.org/pdf/1603.09320
- FAISS indexes: https://github.com/facebookresearch/faiss/wiki/Faiss-indexes
- FAISS selection guide: https://github.com/facebookresearch/faiss/wiki/Guidelines-to-choose-an-index
- ANN-Benchmarks paper: https://arxiv.org/abs/1807.05614
- Dataset and benchmark contract: https://github.com/erikbern/ann-benchmarks
- Metric implementation: https://github.com/erikbern/ann-benchmarks/blob/main/ann_benchmarks/plotting/metrics.py
