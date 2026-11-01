# Veqtors code

Runnable code behind the [Veqtors](https://veqtors.substack.com) newsletter: production-grade AI systems, explained in diagrams. There's one folder per issue, with the experiments and calculations behind each article.

| Issue | Folder | What's inside |
|---|---|---|
| #1 Inside the Transformer | [`001-transformer`](001-transformer) | NumPy causal attention, a parameter and KV-cache calculator, English vs Urdu token counts |
| #2 A single space cut my token count | [`002-tokens`](002-tokens) | Tokenizer probes, a BPE toy, and a prompt-cost calculator |
| #3 The same model, trained three times | [`003-post-training`](003-post-training) | Base vs instruct checkpoints, chat-template tokens, and DPO loss |
| #4 128x less memory, with a catch | [`004-attention`](004-attention) | MHA/GQA/MQA memory calculations and sliding-window masks |
| #5 The model never saw your answer | [`005-rag-system`](005-rag-system) | A tiny BM25 RAG pipeline and chunk-boundary failures |
| #6 Overlap made my RAG worse | [`006-rag-upgrades`](006-rag-upgrades) | A measured upgrade ladder across chunking and retrieval choices |
| #7 Hybrid search lost the easy answer | [`007-hybrid-search`](007-hybrid-search) | BM25, dense retrieval, RRF, and the zero-score rank bug |
| #8 My vector index made search slower | [`008-vector-index`](008-vector-index) | Exact, HNSW and IVF recall curves, the size crossover, and post-filter loss |
| #9 Rewriting my queries made search worse | [`009-query-rewriting`](009-query-rewriting) | Query rewriting, HyDE and reranking on two public datasets, with bootstrap intervals |
| #10 Five searches found less than one | [`010-multi-query`](010-multi-query) | RAG-Fusion, step-back and two-round retrieval on three public datasets, with merge checks |
| #11 Long context or RAG? (in progress) | [`011-long-context`](011-long-context) | Experimental full-context versus top-5 retrieval, placement and prefix-cache scripts; results pending |

Completed experiments contain their recorded output in `RESULTS.md`. Issue 011 is still in progress; see its README for setup and limits. Install from its `requirements.txt` when present; issues 004–006 use only the Python standard library.

MIT licensed.
