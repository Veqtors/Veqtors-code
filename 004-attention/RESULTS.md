# Results

Llama-3-8B shape: hidden 4096, 32 layers, 32 heads, fp16. Only the GQA row at 8K is the real model. The rest apply each idea to the same shape, and 128K exceeds this model's original 8K context.

## attention_memory.py

```
setting                        8K tokens   128K tokens
MHA, 32 K/V heads                4.00 GiB      64.00 GiB
GQA, 8 K/V heads (real)          1.00 GiB      16.00 GiB
MQA, 1 K/V head                  0.12 GiB       2.00 GiB
GQA + window of 4,096            0.50 GiB       0.50 GiB
```

## window_mask.py

```
causal mask         window mask (W=4)
1 . . . . . . .    1 . . . . . . .
1 1 . . . . . .    1 1 . . . . . .
1 1 1 . . . . .    1 1 1 . . . . .
1 1 1 1 . . . .    1 1 1 1 . . . .
1 1 1 1 1 . . .    . 1 1 1 1 . . .
1 1 1 1 1 1 . .    . . 1 1 1 1 . .
1 1 1 1 1 1 1 .    . . . 1 1 1 1 .
1 1 1 1 1 1 1 1    . . . . 1 1 1 1

furthest position back a token can reach, upper bound:
  window 4096,  1 layers: 4,095 tokens
  window 4096,  2 layers: 8,190 tokens
  window 4096, 32 layers: 131,040 tokens
```
