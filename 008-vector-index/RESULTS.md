# Results

GloVe-100 from ANN-Benchmarks (real word vectors, 100 dimensions), FAISS 1.15.1, 1,000 queries, top 10, one search thread on one machine. Timings belong to this machine. Filter labels are random, so they share no relation with the vectors.

```
Scale: top 10, 1,000 queries
  vectors  exact ms  HNSW M=16, recall at ms per query
    3,000     0.037  ef16 0.802 at 0.012  ef50 0.956 at 0.034  ef100 0.993 at 0.063  ef200 0.999 at 0.128  ef400 1.000 at 0.284
   10,000     0.106  ef16 0.718 at 0.014  ef50 0.904 at 0.036  ef100 0.966 at 0.069  ef200 0.992 at 0.154  ef400 1.000 at 0.344
   30,000     0.302  ef16 0.675 at 0.016  ef50 0.848 at 0.038  ef100 0.924 at 0.074  ef200 0.970 at 0.161  ef400 0.992 at 0.383
  100,000     1.848  ef16 0.645 at 0.034  ef50 0.810 at 0.102  ef100 0.884 at 0.159  ef200 0.935 at 0.344  ef400 0.973 at 0.658
  300,000     5.850  ef16 0.605 at 0.048  ef50 0.772 at 0.118  ef100 0.842 at 0.212  ef200 0.898 at 0.411  ef400 0.941 at 0.854
1,000,000    21.051  ef16 0.572 at 0.060  ef50 0.743 at 0.159  ef100 0.813 at 0.250  ef200 0.875 at 0.538  ef400 0.915 at 1.014

IVF at 100,000 vectors
  nlist 1264 nprobe   1: recall 0.305 at 0.022 ms
  nlist 1264 nprobe   5: recall 0.575 at 0.024 ms
  nlist 1264 nprobe  10: recall 0.678 at 0.031 ms
  nlist 1264 nprobe  20: recall 0.772 at 0.049 ms
  nlist 1264 nprobe  50: recall 0.865 at 0.100 ms
  nlist 1264 nprobe 100: recall 0.924 at 0.186 ms

Post-filter at 100,000 vectors, HNSW ef 200, random labels, top 10
  keep  50%, fetch  10: recall 0.505, empty 0.1%
  keep  50%, fetch  30: recall 0.915, empty 0.0%
  keep  50%, fetch 100: recall 0.916, empty 0.0%
  keep  50%, fetch 300: recall 0.916, empty 0.0%
  keep  10%, fetch  10: recall 0.103, empty 33.1%
  keep  10%, fetch  30: recall 0.298, empty 4.8%
  keep  10%, fetch 100: recall 0.793, empty 0.0%
  keep  10%, fetch 300: recall 0.854, empty 0.0%
  keep   1%, fetch  10: recall 0.008, empty 92.4%
  keep   1%, fetch  30: recall 0.025, empty 77.6%
  keep   1%, fetch 100: recall 0.089, empty 40.5%
  keep   1%, fetch 300: recall 0.282, empty 6.5%
```

## Checks

`single_query.py`: seconds for 1,000 queries, which equals ms per query. b is a batch, s is one query at a time.

```
blas threshold 128000
    3,000 exact b0.034 s0.035 | ef16 0.802 b0.013 s0.016 | ef50 0.956 b0.032 s0.036 | ef100 0.993 b0.061 s0.070 | ef200 0.999 b0.125 s0.133 | ef400 1.000 b0.279 s0.290
   10,000 exact b0.106 s0.109 | ef16 0.718 b0.015 s0.018 | ef50 0.904 b0.039 s0.043 | ef100 0.966 b0.073 s0.075 | ef200 0.992 b0.160 s0.159 | ef400 1.000 b0.352 s0.351
   30,000 exact b0.311 s0.312 | ef16 0.675 b0.019 s0.020 | ef50 0.848 b0.038 s0.042 | ef100 0.924 b0.076 s0.082 | ef200 0.970 b0.164 s0.174 | ef400 0.992 b0.377 s0.399
  100,000 exact b1.916 s1.896 | ef16 0.645 b0.034 s0.045 | ef50 0.810 b0.081 s0.091 | ef100 0.884 b0.148 s0.160 | ef200 0.935 b0.307 s0.318 | ef400 0.973 b0.671 s0.662
  300,000 exact b5.821 s5.820 | ef16 0.605 b0.046 s0.051 | ef50 0.772 b0.111 s0.117 | ef100 0.842 b0.208 s0.212 | ef200 0.898 b0.398 s0.405 | ef400 0.941 b0.813 s0.820
1,000,000 exact b19.709 s19.053 | ef16 0.572 b0.062 s0.065 | ef50 0.743 b0.145 s0.166 | ef100 0.813 b0.245 s0.255 | ef200 0.875 b0.517 s0.470 | ef400 0.915 b0.918 s0.922

```

`fetch_vs_ef.py`, 100,000 vectors:

```
ef 200 k 10: returned 10.0, top10 recall 0.935
ef 200 k 20: returned 20.0, top10 recall 0.935
ef 200 k 100: returned 100.0, top10 recall 0.935
ef 200 k 300: returned 300.0, top10 recall 0.935
ef 300 k 10: returned 10.0, top10 recall 0.960
ef 300 k 300: returned 300.0, top10 recall 0.960
ef 400 k 10: returned 10.0, top10 recall 0.973
```
