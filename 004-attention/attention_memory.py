"""KV cache size under different attention settings, on Llama-3-8B's shape.

Only the Llama-3-8B GQA row is that model's real setting. The others apply each
idea to the same shape, for comparison. Run: python attention_memory.py
"""

D, LAYERS, HEADS = 4096, 32, 32      # Llama-3-8B config.json
D_HEAD = D // HEADS
BYTES = 2                            # fp16


def gib(values_per_token, tokens, window=None):
    kept = min(tokens, window) if window else tokens
    return values_per_token * LAYERS * kept * BYTES / 2**30


SETTINGS = {
    "MHA, 32 K/V heads":            (2 * 32 * D_HEAD, None),
    "GQA, 8 K/V heads (real)":      (2 * 8 * D_HEAD, None),
    "MQA, 1 K/V head":              (2 * 1 * D_HEAD, None),
    "GQA + window of 4,096":        (2 * 8 * D_HEAD, 4096),
}

print(f"{'setting':<28}{'8K tokens':>12}{'128K tokens':>14}")
for name, (per_token, window) in SETTINGS.items():
    print(f"{name:<28}{gib(per_token, 8192, window):>9.2f} GiB{gib(per_token, 128 * 1024, window):>11.2f} GiB")
