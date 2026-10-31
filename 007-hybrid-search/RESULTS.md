# Results

Constructed examples: one document across 25 offsets and six error sentences, BM25, bge-small-en-v1.5 through fastembed, RRF k=60, no model call for answers. They show mechanisms, not how often these happen.

```
Lost of 25 offsets, chunks of 25 words
  original    top 1: bm25  4  dense  6  rrf  4  rrf matched  4
  original    top 2: bm25  3  dense  4  rrf  3  rrf matched  3
  reworded A  top 1: bm25 17  dense  4  rrf 16  rrf matched 16
  reworded A  top 2: bm25 16  dense  1  rrf  3  rrf matched  1
  reworded B  top 1: bm25  3  dense  5  rrf  3  rrf matched  3
  reworded B  top 2: bm25  2  dense  1  rrf  1  rrf matched  1

Error codes, top 1
  E4012: bm25 E4012  dense E4012  rrf E4012  rrf matched E4012
  E4021: bm25 E4021  dense E4021  rrf E4021  rrf matched E4021
  E4102: bm25 E4102  dense E4102  rrf E4102  rrf matched E4102
  E4120: bm25 E4120  dense E4012 WRONG  rrf E4012 WRONG  rrf matched E4120
  E4201: bm25 E4201  dense E4201  rrf E4201  rrf matched E4201
  E4210: bm25 E4210  dense E4210  rrf E4210  rrf matched E4210

Trace: What does E4120 mean?
  BM25:  E4120 1.57, E4012 0.00, E4021 0.00, E4102 0.00, E4201 0.00, E4210 0.00
  dense: E4012 0.599, E4102 0.595, E4120 0.575, E4210 0.568, E4021 0.564, E4201 0.546
  rrf: E4012 0.03252, E4120 0.03227, E4102 0.03175
  rrf matched: E4120 0.03227, E4012 0.01639, E4102 0.01613

The fix's limit: What error means E4120?
  bm25 E4120  dense E4102  rrf E4012  rrf matched E4012
```

## LangChain check (langchain_check.py)

LangChain EnsembleRetriever with BM25Retriever, default RRF, every order of the six sentences:

```
E4120: wrong top result (E4012) in 144 of 720 orders
The other five codes: 0 of 720
BM25 alone was right in every run.
```

BM25 ties at zero, so which leftover takes second place depends on document order.
