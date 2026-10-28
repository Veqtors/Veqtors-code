"""Read a model card like an engineer: parameter count and KV-cache memory from config values.

Veqtors #1, "Inside the Transformer". Run: python model_card.py
Defaults are Llama-3-8B's config.json (meta-llama/Meta-Llama-3-8B on Hugging Face).
"""

def param_count(vocab, d, layers, n_heads, n_kv_heads, ffn, tied=False):
    d_head = d // n_heads
    attn = d * d + 2 * d * (n_kv_heads * d_head) + d * d   # W_q, W_k, W_v (GQA-sized), W_o
    mlp = 3 * d * ffn                                      # SwiGLU: gate, up, down
    norms = 2 * d                                          # two RMSNorm weight vectors
    per_layer = attn + mlp + norms
    embed = vocab * d * (1 if tied else 2)                 # input embedding + output head
    return {"per_layer": per_layer, "attention": attn * layers, "ffn": mlp * layers,
            "embeddings": embed, "total": per_layer * layers + embed + d}


def kv_cache_bytes(layers, n_kv_heads, d_head, tokens, batch=1, bytes_per=2):
    return 2 * layers * n_kv_heads * d_head * tokens * batch * bytes_per   # 2 = K and V


if __name__ == "__main__":
    cfg = dict(vocab=128_256, d=4096, layers=32, n_heads=32, n_kv_heads=8, ffn=14_336)
    p = param_count(**cfg)
    print(f"Total parameters : {p['total'] / 1e9:.2f} B")
    for part in ("ffn", "attention", "embeddings"):
        print(f"  {part:<11}: {p[part] / 1e9:.2f} B ({p[part] / p['total']:.0%})")
    print(f"Rule of thumb 12*L*d^2: {12 * cfg['layers'] * cfg['d'] ** 2 / 1e9:.2f} B (ignores GQA, SwiGLU width, embeddings)")

    d_head = cfg["d"] // cfg["n_heads"]
    for n in (1_000, 8_192):
        gib = kv_cache_bytes(cfg["layers"], cfg["n_kv_heads"], d_head, n) / 2**30
        print(f"KV cache, {n:>5} tokens, fp16, batch 1: {gib:.3f} GiB")
    full = kv_cache_bytes(cfg["layers"], cfg["n_heads"], d_head, 8_192) / 2**30
    print(f"Same at 8,192 tokens without GQA (32 KV heads): {full:.3f} GiB")
