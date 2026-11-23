# RAG That Actually Works: handbook code

Runnable code behind the free Veqtors handbook *RAG That Actually Works* by Imtiaz Nabi. The handbook's numbers and printed outputs are recorded in `RESULTS.md`.

## Setup

```sh
python -m venv .venv
pip install -r requirements.txt
```

The first run downloads the `BAAI/bge-small-en-v1.5` embedding model through fastembed. No API key or GPU is needed.

## Files

- `rag_60.py`: the whole pipeline in under 60 lines (chapter 02) on one constructed returns-policy document. Pass a text file path to use your own.
- `chunk_sweep.py`: moves the chunk boundary across 25 offsets and shows when the fact falls out of the prompt (chapters 02 and 03).
- `eval_set.py`: a 28-document, 20-question constructed set with fact-string gold labels (chapter 08).
- `score.py`: hit@k, MRR and stage labels (chunking, ranking, reached) for BM25, embeddings and fusion (chapters 08 and 09).

These are constructed examples that show the mechanisms and the scorer. They are not benchmarks of how a retriever behaves on your data.
