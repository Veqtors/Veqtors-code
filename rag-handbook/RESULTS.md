# Handbook code results (measured 2026-11-12)

Windows 11, Python 3.14.0 in a fresh virtual environment, fastembed 0.9.1, numpy 2.5.4, onnxruntime 1.31.1. fastembed loaded `BAAI/bge-small-en-v1.5` from its quantized ONNX build (cache repo `Qdrant/bge-small-en-v1.5-onnx-Q`). One CPU run, 15.9 s including a first-time model download.

Constructed example: one document, chunks of 25 words, bge-small-en-v1.5 embeddings with the BGE query prefix, cosine similarity, no model call. It shows mechanisms, not how often they happen. These are embedding results; issues #5 and #6 report the same ladder with BM25.

## rag_60.py (`python rag_60.py`)

```
5 chunks of 25 words, offset 0, top 1
  whole in a chunk: True
  in the prompt:    True  (top score 0.784)
Answer using only this context.
- want their money back must write to the support team, and the deadline for a refund request is 14 days after delivery. Gift cards are
Question: What is the deadline for a refund request?
Answer:

6 chunks of 25 words, offset 16, top 1
  whole in a chunk: True
  in the prompt:    False  (top score 0.752)
Answer using only this context.
- the customer unless the item arrived damaged. Customers who want their money back must write to the support team, and the deadline for a refund
Question: What is the deadline for a refund request?
Answer:

5 chunks of 25 words, offset 19, top 1
  whole in a chunk: False
  in the prompt:    False  (top score 0.762)
Answer using only this context.
- the item arrived damaged. Customers who want their money back must write to the support team, and the deadline for a refund request is 14
Question: What is the deadline for a refund request?
Answer:

Fact missing from the prompt at 6 of 25 offsets [14, 15, 16, 17, 18, 19] (chunks of 25 words, top 1).

```

For comparison, issue #5 (BM25, same document and question): fact missing at 4 of 25 offsets, [16, 17, 18, 19].

## chunk_sweep.py (`python chunk_sweep.py`)

```

original: What is the deadline for a refund request?
  baseline, top 1      lost  6/25  split 1  offsets [14, 15, 16, 17, 18, 19]
  top 2                lost  4/25  split 1  offsets [16, 17, 18, 19]
  overlap 5, top 1     lost  6/25  split 0  offsets [0, 3, 4, 20, 23, 24]
  overlap 10, top 1    lost  3/25  split 0  offsets [12, 13, 14]
  overlap 5, top 2     lost  0/25  split 0  offsets []
  sentences, top 1     lost  0/25  split 0  offsets []
  sentences, top 2     lost  0/25  split 0  offsets []

reworded A: How long do I have to get my money back?
  baseline, top 1      lost  4/25  split 1  offsets [16, 17, 18, 19]
  top 2                lost  1/25  split 1  offsets [19]
  overlap 5, top 1     lost  8/25  split 0  offsets [0, 1, 2, 3, 20, 21, 22, 23]
  overlap 10, top 1    lost  2/25  split 0  offsets [12, 13]
  overlap 5, top 2     lost  0/25  split 0  offsets []
  sentences, top 1     lost  0/25  split 0  offsets []
  sentences, top 2     lost  0/25  split 0  offsets []

reworded B: Can I still return this after two weeks?
  baseline, top 1      lost  5/25  split 1  offsets [3, 13, 17, 18, 19]
  top 2                lost  1/25  split 1  offsets [19]
  overlap 5, top 1     lost  2/25  split 0  offsets [3, 9]
  overlap 10, top 1    lost  2/25  split 0  offsets [3, 14]
  overlap 5, top 2     lost  0/25  split 0  offsets []
  sentences, top 1     lost 25/25  split 0  offsets [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
  sentences, top 2     lost  0/25  split 0  offsets []
```

Reading it: for the original question, overlap 5 with top 1 loses 6 of 25 offsets, the same count as the baseline, but a different set. Baseline offsets 14 to 19 were rescued and offsets 0, 3, 4, 20, 23, 24 were newly lost. The sentence splitter ignores offsets, so its rows are one trial repeated 25 times.

## score.py (`python score.py`, measured 2026-11-23)

Python 3.14.0, fastembed 0.9.1, numpy 2.5.4, onnxruntime 1.32.0, one CPU run. 28 constructed support documents, 20 questions (`eval_set.py`). BM25 is a 30-line implementation (k1 1.5, b 0.75, no stemming); fusion is RRF k = 60 over the full BM25 and dense rankings. Constructed data: it shows the scorer working, not how any retriever behaves on your data.

```
28 chunks, 20 questions

bm25   hit@1 0.80  hit@3 0.85  hit@5 0.85  MRR 0.83
  plain     hit@1 8/10
  reworded  hit@1 4/6
  code      hit@1 4/4
dense  hit@1 0.95  hit@3 1.00  hit@5 1.00  MRR 0.97
  plain     hit@1 9/10
  reworded  hit@1 6/6
  code      hit@1 4/4
rrf    hit@1 0.85  hit@3 0.85  hit@5 0.90  MRR 0.87
  plain     hit@1 9/10
  reworded  hit@1 4/6
  code      hit@1 4/4

rrf on the 28 chunks, k=3: {'reached': 17, 'ranking': 3}
  ranking   rank 8  What export formats can I get?
  ranking   rank 5  Can I get my money back on a yearly subscription?
  ranking   rank 8  What happens if I enter the wrong password too many times?

dense on 25-word chunks, k=3: {'reached': 19, 'chunking': 1}
  chunking  rank None  How long are deleted projects recoverable?
```

Derived: 19, 16 and 17 of 20 questions first at rank 1 for dense, BM25 and fusion. Paired at rank 1: dense right and fusion wrong on 3, fusion right and dense wrong on 1; exact two-sided sign test p = 0.625. Wilson 95% intervals: 19/20 = 0.764 to 0.991; 17/20 = 0.640 to 0.948. BM25 misses: invoice question rank 2, export 25, refund 17, password 22. Dense miss: webhook retries, rank 2.
