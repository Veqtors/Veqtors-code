"""Causal mask vs sliding window mask, and how far a token reaches after N layers."""

N, W = 8, 4

print("causal mask" + " " * 9 + f"window mask (W={W})")
for t in range(N):
    full = " ".join("1" if j <= t else "." for j in range(N))
    win = " ".join("1" if t - W < j <= t else "." for j in range(N))
    print(f"{full}    {win}")


def furthest_back(layers, window):
    return layers * (window - 1)


print("\nfurthest position back a token can reach, upper bound:")
for w, layers in ((4096, 1), (4096, 2), (4096, 32)):
    print(f"  window {w}, {layers:>2} layers: {furthest_back(layers, w):,} tokens")
