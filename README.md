# Veqtors code

Runnable code behind the [Veqtors](https://veqtors.substack.com) newsletter: production-grade AI systems, explained in diagrams. There's one folder per issue. Every number quoted in an issue can be reproduced from here.

| Issue | Folder | What's inside |
|---|---|---|
| #1 Inside the Transformer | [`001-transformer`](001-transformer) | NumPy causal attention, a parameter and KV-cache calculator, English vs Urdu token counts |

```bash
pip install numpy tiktoken
python 001-transformer/model_card.py
```

MIT licensed.
