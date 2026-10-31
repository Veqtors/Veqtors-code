# Results

SciFact and nfcorpus from BEIR, plus the first 300 HotpotQA dev questions searched over the 2,964 paragraphs that came with them. bge-small-en-v1.5, one set of query outputs from Qwen2.5-1.5B-Instruct (one prompt per method, greedy decoding), saved in `generated.json`. Lists merge with RRF, k = 60, except where stated. Recall divides by min(5, relevant documents).

```
Recall at 5, change in points with a 95% paired bootstrap interval

scifact: 5,183 documents, 300 queries, 1.1 relevant per query
  plain                     76.9%  0 model calls, 1 search
  variants only             74.5%   -2.3 [ -6.1,  +1.3]  helped  17 hurt  23  no clear change  1 model call, 4 searches
  RAG-Fusion                75.4%   -1.4 [ -4.8,  +2.0]  helped  15 hurt  18  no clear change  1 model call, 5 searches
  step-back only            75.2%   -1.7 [ -5.5,  +2.2]  helped  18 hurt  23  no clear change  1 model call, 1 search
  step-back + query         78.8%   +1.9 [ -0.9,  +4.8]  helped  14 hurt   7  no clear change  1 model call, 2 searches
  iterative, two rounds     78.5%   +1.7 [ -0.5,  +4.0]  helped  11 hurt   6  no clear change  1 model call, 2 searches

nfcorpus: 3,633 documents, 323 queries, 38.2 relevant per query
  plain                     36.1%  0 model calls, 1 search
  variants only             34.8%   -1.3 [ -3.2,  +0.7]  helped  39 hurt  56  no clear change  1 model call, 4 searches
  RAG-Fusion                35.6%   -0.6 [ -2.4,  +1.3]  helped  39 hurt  47  no clear change  1 model call, 5 searches
  step-back only            34.6%   -1.5 [ -3.5,  +0.4]  helped  47 hurt  61  no clear change  1 model call, 1 search
  step-back + query         36.7%   +0.6 [ -0.7,  +1.9]  helped  31 hurt  31  no clear change  1 model call, 2 searches
  iterative, two rounds     34.3%   -1.8 [ -3.3,  -0.4]  helped  30 hurt  49  loss  1 model call, 2 searches

hotpot: 2,964 documents, 300 queries, 2.0 relevant per query
  plain                     87.0%  0 model calls, 1 search
  variants only             77.0%  -10.0 [-13.2,  -7.0]  helped  14 hurt  67  loss  1 model call, 4 searches
  RAG-Fusion                79.2%   -7.8 [-11.0,  -4.8]  helped  17 hurt  59  loss  1 model call, 5 searches
  step-back only            78.3%   -8.7 [-11.7,  -5.8]  helped  10 hurt  55  loss  1 model call, 1 search
  step-back + query         83.3%   -3.7 [ -5.5,  -1.8]  helped   5 hurt  27  loss  1 model call, 2 searches
  iterative, two rounds     81.7%   -5.3 [ -7.8,  -2.8]  helped  14 hurt  45  loss  1 model call, 2 searches
```

## Merge check (check_merge.py), HotpotQA

```
plain                         87.0%
RAG-Fusion, equal weights     79.2%
RAG-Fusion, original weight 4 82.8%
keep top 3, then follow-up    87.0%
at 20: plain 96.7%, RAG-Fusion 91.5%
both documents in plain top 5 75.3%
```

## Merge trace (trace_merge.py)

```
Hayden is a singer-songwriter from Canada, but where does Buck-Tick hail from?
needs: ['Buck-Tick', 'Hayden (musician)']
plain top 5: ['Hayden (musician)', 'Buck-Tick', 'Skyscraper National Park', 'Mild and Hazy', 'Atsushi Sakurai']
fused top 5: ['Buck-Tick 0.08170', 'Atsushi Sakurai 0.07964', 'Bukkehorn 0.05985', 'Spangled Unicorn 0.05798', 'Owsley Stanley 0.05259']
Buck-Tick: plain rank 2, fused rank 1, score 0.08170
Hayden (musician): plain rank 1, fused rank 53, score 0.01639
step-back, Derrickson question: Are any filmmakers from the 1950s known for directing horror films also considered to be part of the "B-movie" genre?
```
