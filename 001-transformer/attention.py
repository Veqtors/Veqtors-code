"""Causal self-attention in NumPy: one head, four tokens, every step visible.

Veqtors #1, "Inside the Transformer". Run: python attention.py
"""
import numpy as np

rng = np.random.default_rng(0)
tokens = ["The", "capital", "of", "Pakistan"]
T, d_model, d_head = len(tokens), 8, 4

x = rng.normal(size=(T, d_model))            # token embeddings (+ position, omitted here)
W_q, W_k, W_v = (rng.normal(size=(d_model, d_head)) for _ in range(3))

Q, K, V = x @ W_q, x @ W_k, x @ W_v          # each token asks (Q), advertises (K), offers (V)
scores = Q @ K.T / np.sqrt(d_head)           # how well each query matches each key

mask = np.triu(np.ones((T, T), dtype=bool), k=1)
scores[mask] = -np.inf                       # causal: no peeking at future tokens

weights = np.exp(scores - scores.max(axis=-1, keepdims=True))
weights /= weights.sum(axis=-1, keepdims=True)   # softmax: each row sums to 1

out = weights @ V                            # each token = weighted mix of earlier values

np.set_printoptions(precision=2, suppress=True)
print("Attention weights (row = token reading, column = token read):")
for tok, row in zip(tokens, weights):
    print(f"{tok:>9} {row}")
print("\nOutput shape:", out.shape, "-> one context-mixed vector per token")
