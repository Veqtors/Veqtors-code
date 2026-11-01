# Issue 11: Long context or RAG?

**In progress.** These are the experiment scripts for an issue still in research. There is no final `RESULTS.md` or measured conclusion yet. The dependency pins match issue 10; the full experiment has not been validated for this snapshot.

## Setup

Run from this directory in a Python environment with CUDA-enabled PyTorch and a supported NVIDIA GPU for the local-model scripts:

```sh
uv pip install -r requirements.txt
uv run python probe_size.py
uv run python probe_chunks.py
uv run python long_context_test.py
uv run python prefix_cache_test.py
```

The first run downloads the public HotpotQA validation dataset, checks its SHA-256, and caches paragraph embeddings in `data/`. Model weights also download on first use. Dataset files and local answer caches are excluded from version control.

- `common.py`: dataset loading, deterministic document pools, retrieval, and answer scoring.
- `probe_size.py`: single-pass prompt memory probe.
- `probe_chunks.py`: chunked prompt-processing memory and timing probe.
- `long_context_test.py`: full-pool versus top-5 retrieval on 300 questions, with placement variants and paired bootstrap intervals. Resumes from `answers.json`.
- `prefix_cache_test.py`: prompt-processing timings for no cache, a cached prefix, and edits near the start or end of the corpus.
- `groq_check.py`: optional API check on 20 questions; requires `GROQ_API_KEY` in the environment and resumes from `groq_answers.json`. Running it makes API calls; check your account's current limits and pricing. Its pool sizes are estimates rather than a hard request-token cap.

These scripts execute their experiments at module level. Run them directly; importing them also starts work.
