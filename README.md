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
| #8 What a vector index skips | [`008-vector-index`](008-vector-index) | Hand-traced HNSW search lab, neighbour recall, and exact vs HNSW recall/time measurements |
| #9 Rewriting my queries made search worse | [`009-query-rewriting`](009-query-rewriting) | Query rewriting, HyDE and reranking on two public datasets, with bootstrap intervals |
| #10 Five searches found less than one | [`010-multi-query`](010-multi-query) | RAG-Fusion, step-back and two-round retrieval on three public datasets, with merge checks |
| #11 Long context or RAG? (in progress) | [`011-long-context`](011-long-context) | Experimental full-context versus top-5 retrieval, placement and prefix-cache scripts; results pending |
| #19 Repeatable checked records | [`019-repeatable-data-pipeline`](019-repeatable-data-pipeline) | Hash-verified UCI data, strict parsing, exact reruns and injected contract faults |
| #20 Prediction boundary and full-entry sentinel | [`020-leakage-safe-validation`](020-leakage-safe-validation) | Frozen chronological partitions, label readiness and preprocessing leakage controls |
| #21 Fixed constant and linear baselines | [`021-linear-regression-baseline`](021-linear-regression-baseline) | Paired mean/median/OLS baselines, development metrics, coefficient trace and residual diagnostics |
| #22 Logistic regression and thresholds | [`022-logistic-regression-thresholds`](022-logistic-regression-thresholds) | Standalone prior/logistic baselines, frozen training-only labels, paired log loss, fixed decision policies and reproducibility receipts |
| #24 Where a decision tree draws the line | [`024-decision-trees-and-forests`](024-decision-trees-and-forests) | Hand-checked split lab, constrained tree, 100-tree forest and unrestricted diagnostic against the #21 baselines on the same development rows |
| #25 Many weak trees, one honest score | [`025-boosting-honest-tuning`](025-boosting-honest-tuning) | Gradient boosting by hand, grouped-by-recipe CV on UCI Concrete, Bayesian (GP) vs random search at equal budget, nested CV and a once-opened test set |
| DE-01 Start data engineering with a pencil | [`data-engineering/de-001-ten-rows-are-easy`](data-engineering/de-001-ten-rows-are-easy) | Counts cancellations, missing customers, exact repeats, zero prices and bad dates in UCI Online Retail II; tested on the ten rows used in the issue |
| DE-02 Python is installed. Your code still won't run. | [`data-engineering/de-002-python-installed-code-wont-run`](data-engineering/de-002-python-installed-code-wont-run) | Four-check lab script (Python version, virtual environment, packages, tests) with six tests; run on Windows |
| DE-03 Your first Git repo | [`data-engineering/de-003-your-first-git-repo`](data-engineering/de-003-your-first-git-repo) | Break-it script that commits and deletes a fake password in a throwaway repo, a repo checker for secrets and ignored data, and a python-dotenv settings loader; four tests |
| DE-04 Why Docker exists | [`data-engineering/de-004-why-docker-exists`](data-engineering/de-004-why-docker-exists) | Compose file that runs Postgres 18 on localhost with a named volume and a password from `.env`, plus a script that loads the ten rows and counts them; tests need no Docker |
| DE-05 Read the data before you trust it | [`data-engineering/de-005-read-the-data-first`](data-engineering/de-005-read-the-data-first) | Downloads UCI's Online Retail II zip and checks it is whole, then runs a first look on both sheets: types, missing values, documented-versus-measured counts, sheet overlap and four answers to "how many orders?"; a ten-row `--sample` mode and tests need no download |

Completed experiments contain their recorded output in `RESULTS.md`. Issue 011 is still in progress; see its README for setup and limits. Install from its `requirements.txt` when present; issues 004–006 use only the Python standard library.

MIT licensed.
