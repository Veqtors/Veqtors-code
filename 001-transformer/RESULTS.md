# Measured results (run 2026-10-28)

These are our own measurements: first-hand proof the issue can cite as "I ran this". Reproduce with the scripts in this folder.

## model_card.py — Llama-3-8B from config (vocab 128,256 · d 4096 · 32 layers · 32 Q / 8 KV heads · FFN 14,336 · untied)

- Total **8.03B** parameters, matching Meta's stated size.
- FFN **5.64B (70%)** · attention **1.34B (17%)** · embeddings + output head **1.05B (13%)**.
- The 12·L·d² rule of thumb gives **6.44B** for the layers, against the actual 6.98B: **7.7% low**, because the real layer is about 13·d² (GQA shrinks attention to 2.5·d²; the 3-matrix SwiGLU FFN at 3.5·d is 10.5·d²). Add the untied embeddings (1.05B) and you reach 8.03B. Quoting the rule against the total (6.44B vs 8.03B, 20% short) mixes up two separate errors.
- KV cache, fp16, batch 1: **0.122 GiB per 1k tokens**, **1.000 GiB at 8,192 tokens**. Without GQA (32 KV heads): **4.000 GiB**, so GQA saves 4×.

## attention.py — 4-token causal attention (random weights, seed 0)

- The upper triangle of the weight matrix is exactly 0: the causal mask works.
- The last token ("Pakistan") spreads its attention: 0.01 / 0.25 / 0.08 / 0.66.
- The weights are random and untrained, so the pattern shows the **mechanism**, not linguistic meaning.

## tokens.py — English vs Urdu, same meaning (a 2-sentence test, so not a general statistic)

| Tokenizer | Sentence | EN | UR | Ratio |
|---|---|---|---|---|
| cl100k_base (GPT-4) | "The capital of Pakistan is Islamabad." | 7 | 30 | 4.3× |
| cl100k_base (GPT-4) | 2022 floods sentence | 15 | 49 | 3.3× |
| o200k_base (GPT-4o) | "The capital of Pakistan is Islamabad." | 7 | 10 | 1.4× |
| o200k_base (GPT-4o) | 2022 floods sentence | 14 | 16 | 1.1× |

Numbers are split into chunks of up to 3 digits in both tokenizers: "2022" → `202` + `2`; "1234567" → `123` + `456` + `7`; "3.14159" → `3` + `.` + `141` + `59`.

**Takeaway:** the tokenizer's vocabulary, not just the model, sets the cost for non-English users.
