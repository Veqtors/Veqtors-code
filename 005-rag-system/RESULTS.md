# Results

Constructed example: one document and one question, chunks of 25 words, BM25, top 1, no model call. It shows the mechanism, not how often this happens.

```

Boundary A: 5 chunks of 25 words, offset 0
  in document:      True
  whole in a chunk: True
  in the prompt:    True
  top chunk (score 4.18): want their money back must write to the support team, and the deadline for a refund request is 14 days after delivery. Gift cards are

Boundary B: 6 chunks of 25 words, offset 16
  in document:      True
  whole in a chunk: True
  in the prompt:    False
  top chunk (score 2.94): the customer unless the item arrived damaged. Customers who want their money back must write to the support team, and the deadline for a refund

Boundary C: 5 chunks of 25 words, offset 19
  in document:      True
  whole in a chunk: False
  in the prompt:    False
  top chunk (score 4.31): the item arrived damaged. Customers who want their money back must write to the support team, and the deadline for a refund request is 14

Fact missing from the prompt at 4 of 25 boundary offsets (chunks of 25 words, top 1).
```

Boundary B scores: the chunk with "14 days" 1.30, the top chunk 2.94.
