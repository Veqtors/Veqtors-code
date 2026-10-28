"""Same meaning, different bill: token counts for English vs Urdu, and how numbers get split.

Veqtors #1, "Inside the Transformer". Run: pip install tiktoken && python tokens.py
Uses OpenAI's open tokenizers (cl100k_base: GPT-4; o200k_base: GPT-4o).
"""
import tiktoken

pairs = [
    ("The capital of Pakistan is Islamabad.", "پاکستان کا دارالحکومت اسلام آباد ہے۔"),
    ("Floods in 2022 affected millions of people across the country.",
     "2022 کے سیلاب نے ملک بھر میں لاکھوں لوگوں کو متاثر کیا۔"),
]

for name in ("cl100k_base", "o200k_base"):
    enc = tiktoken.get_encoding(name)
    print(f"\n{name}")
    for en, ur in pairs:
        n_en, n_ur = len(enc.encode(en)), len(enc.encode(ur))
        print(f"  EN {n_en:>3} | UR {n_ur:>3} | Urdu costs {n_ur / n_en:.1f}x  <- {en[:40]}")
    for num in ("2022", "1234567", "3.14159"):
        pieces = [enc.decode([t]) for t in enc.encode(num)]
        print(f"  {num:>9} -> {pieces}")
