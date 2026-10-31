"""Byte pair encoding from scratch, on a toy corpus. Prints each merge."""
from collections import Counter

CORPUS = "low low low low lower lower newest newest newest widest widest"


def most_common_pair(seqs):
    pairs = Counter()
    for seq in seqs:
        pairs.update(zip(seq, seq[1:]))
    return pairs.most_common(1)[0] if pairs else None


def merge(seq, pair):
    out, i = [], 0
    while i < len(seq):
        if i + 1 < len(seq) and (seq[i], seq[i + 1]) == pair:
            out.append(seq[i] + seq[i + 1])
            i += 2
        else:
            out.append(seq[i])
            i += 1
    return out


# Each word keeps its leading space, as real tokenizers do.
words = [" " + w for w in CORPUS.split()]
seqs = [list(w) for w in words]
vocab = sorted({ch for seq in seqs for ch in seq})
print(f"start: {len(vocab)} tokens: {vocab}")

bare = list("low")
for step in range(1, 7):
    (a, b), count = most_common_pair(seqs)
    seqs = [merge(seq, (a, b)) for seq in seqs]
    bare = merge(bare, (a, b))
    vocab.append(a + b)
    print(f"step {step}: merge {a!r} + {b!r} (seen {count}x) -> {a + b!r}")

print("\nfinal split of each distinct word:")
for w, seq in dict(zip(words, seqs)).items():
    print(f"  {w!r}: {seq} = {len(seq)} tokens")
print(f"  'low' (no leading space): {bare} = {len(bare)} tokens")
