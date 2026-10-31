# Results

BEIR SciFact and nfcorpus, bge-small-en-v1.5 through fastembed, rewrites and HyDE passages from Qwen2.5-1.5B-Instruct (one prompt, greedy decoding), saved in `generated.json`. Reranking on an RTX 2060; timings belong to that machine. Recall divides by min(5, relevant documents).

```
Recall at 5, change in points with a 95% paired bootstrap interval, device cuda

scifact: 5,183 documents, 300 queries, 1.1 relevant per query
  plain recall at 1: 60.3%, 3: 71.3%, 5: 76.9%, 10: 84.5%, 20: 87.5%, 50: 92.8%
  plain                       76.9%
  rewrite                     77.2%   +0.3 [ -2.7,  +3.4]  helped  14 hurt  12  no clear change
  HyDE                        77.5%   +0.6 [ -2.9,  +4.2]  helped  19 hurt  17  no clear change
  query + HyDE                79.2%   +2.4 [ +0.2,  +4.7]  helped  12 hurt   4  gain
  plain, MiniLM 20            75.8%   -1.0 [ -4.7,  +2.7]  helped  17 hurt  20  no clear change  44 ms
  plain, MiniLM 50            75.6%   -1.3 [ -5.5,  +2.9]  helped  21 hurt  26  no clear change  105 ms
  plain, bge-v2-m3 20         77.2%   +0.4 [ -3.1,  +3.9]  helped  19 hurt  18  no clear change  371 ms
  plain, bge-v2-m3 50         78.4%   +1.6 [ -2.3,  +5.7]  helped  25 hurt  21  no clear change  929 ms
  query + HyDE, bge-v2-m3 50  79.3%   +2.4 [ -1.4,  +6.5]  helped  26 hurt  19  no clear change  915 ms

nfcorpus: 3,633 documents, 323 queries, 38.2 relevant per query
  plain recall at 1: 43.0%, 3: 39.2%, 5: 36.1%, 10: 31.4%, 20: 29.2%, 50: 29.2%
  plain                       36.1%
  rewrite                     31.1%   -5.0 [ -6.9,  -3.2]  helped  32 hurt  84  loss
  HyDE                        33.2%   -3.0 [ -5.6,  -0.4]  helped  54 hurt  85  loss
  query + HyDE                37.2%   +1.1 [ -0.5,  +2.7]  helped  42 hurt  36  no clear change
  plain, MiniLM 20            36.4%   +0.3 [ -1.5,  +2.1]  helped  56 hurt  52  no clear change  33 ms
  plain, MiniLM 50            37.0%   +0.9 [ -1.3,  +3.0]  helped  62 hurt  59  no clear change  81 ms
  plain, bge-v2-m3 20         35.6%   -0.5 [ -2.3,  +1.2]  helped  51 hurt  54  no clear change  358 ms
  plain, bge-v2-m3 50         35.8%   -0.3 [ -2.4,  +1.9]  helped  54 hurt  59  no clear change  903 ms
  query + HyDE, bge-v2-m3 50  36.2%   +0.1 [ -2.1,  +2.2]  helped  60 hurt  56  no clear change  912 ms
```
