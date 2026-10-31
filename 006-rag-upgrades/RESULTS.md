# Results

Constructed example: one document, three questions, 25 boundary offsets, chunks of 25 words, BM25, no model call. It shows how an upgrade can backfire, not how often. The sentence splitter ignores offsets, so its rows are one trial repeated.

```

original: What is the deadline for a refund request?
  baseline, top 1      lost  4/25  split 1  words  25  offsets [16, 17, 18, 19]
  top 2                lost  3/25  split 1  words  40  offsets [17, 18, 19]
  top 3                lost  3/25  split 1  words  63  offsets [17, 18, 19]
  overlap 5, top 1     lost  6/25  split 0  words  25  offsets [2, 3, 4, 22, 23, 24]
  overlap 10, top 1    lost  2/25  split 0  words  25  offsets [13, 14]
  overlap 5, top 2     lost  0/25  split 0  words  44  offsets []
  sentences, top 1     lost  0/25  split 0  words  24  offsets []
  sentences, top 2     lost  0/25  split 0  words  35  offsets []

reworded A: How long do I have to get my money back?
  baseline, top 1      lost 17/25  split 1  words  25  offsets [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
  top 2                lost 16/25  split 1  words  39  offsets [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
  top 3                lost 16/25  split 1  words  63  offsets [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
  overlap 5, top 1     lost 20/25  split 0  words  25  offsets [0, 1, 2, 3, 4, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
  overlap 10, top 1    lost 21/25  split 0  words  25  offsets [0, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 21, 22, 23, 24]
  overlap 5, top 2     lost 16/25  split 0  words  41  offsets [0, 1, 2, 3, 4, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
  sentences, top 1     lost  0/25  split 0  words  24  offsets []
  sentences, top 2     lost  0/25  split 0  words  35  offsets []

reworded B: Can I still return this after two weeks?
  baseline, top 1      lost  3/25  split 1  words  25  offsets [2, 19, 20]
  top 2                lost  2/25  split 1  words  48  offsets [19, 20]
  top 3                lost  2/25  split 1  words  63  offsets [19, 20]
  overlap 5, top 1     lost  2/25  split 0  words  25  offsets [9, 10]
  overlap 10, top 1    lost 11/25  split 0  words  25  offsets [1, 2, 3, 4, 9, 10, 16, 17, 18, 19, 24]
  overlap 5, top 2     lost  0/25  split 0  words  50  offsets []
  sentences, top 1     lost 25/25  split 0  words  12  offsets [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]
  sentences, top 2     lost  0/25  split 0  words  36  offsets []

Baseline lost: [16, 17, 18, 19]
Overlap 5 lost: [2, 3, 4, 22, 23, 24]
Newly lost: [2, 3, 4, 22, 23, 24]
Rescued: [16, 17, 18, 19]

offset 2: top score 3.33, chunk with fact 3.23
  top: customer unless the item arrived damaged. Customers who want their money back must write to the support team, and the deadline for a refund request
  fact: deadline for a refund request is 14 days after delivery. Gift cards are not covered by this policy and they never expire. Store credit is

offset 3: top score 3.91, chunk with fact 2.13
  top: unless the item arrived damaged. Customers who want their money back must write to the support team, and the deadline for a refund request is
  fact: for a refund request is 14 days after delivery. Gift cards are not covered by this policy and they never expire. Store credit is issued

offset 4: top score 3.93, chunk with fact 2.08
  top: the item arrived damaged. Customers who want their money back must write to the support team, and the deadline for a refund request is 14
  fact: a refund request is 14 days after delivery. Gift cards are not covered by this policy and they never expire. Store credit is issued within

offset 22: top score 3.10, chunk with fact 3.01
  top: customer unless the item arrived damaged. Customers who want their money back must write to the support team, and the deadline for a refund request
  fact: deadline for a refund request is 14 days after delivery. Gift cards are not covered by this policy and they never expire. Store credit is

offset 23: top score 3.71, chunk with fact 2.00
  top: unless the item arrived damaged. Customers who want their money back must write to the support team, and the deadline for a refund request is
  fact: for a refund request is 14 days after delivery. Gift cards are not covered by this policy and they never expire. Store credit is issued

offset 24: top score 3.73, chunk with fact 1.95
  top: the item arrived damaged. Customers who want their money back must write to the support team, and the deadline for a refund request is 14
  fact: a refund request is 14 days after delivery. Gift cards are not covered by this policy and they never expire. Store credit is issued within
```
