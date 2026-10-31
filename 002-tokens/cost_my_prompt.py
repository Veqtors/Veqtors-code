"""Count a prompt under two tokenizers and price it.

Usage: python cost_my_prompt.py prompt.txt [dollars_per_million_input_tokens]
With no file, compares the same retrieved records as JSON and as key: value lines.
"""
import json
import sys

import tiktoken

sys.stdout.reconfigure(encoding="utf-8")
PRICE = float(sys.argv[2]) if len(sys.argv) > 2 else None


def report(label, text):
    print(f"{label} ({len(text.split())} words)")
    for name in ("cl100k_base", "o200k_base"):
        n = len(tiktoken.get_encoding(name).encode(text))
        cost = f"  ${n / 1e6 * PRICE:.6f}" if PRICE else ""
        print(f"  {name}: {n} tokens{cost}")


if len(sys.argv) > 1:
    with open(sys.argv[1], encoding="utf-8") as f:
        report(sys.argv[1], f.read())
else:
    records = [
        {"id": i, "title": f"Policy document {i}", "section": "Refunds",
         "updated": "2026-11-17", "text": "Customers can request a refund within 14 days."}
        for i in range(1, 21)
    ]
    as_json = json.dumps(records, indent=2)
    as_lines = "\n\n".join(
        "\n".join(f"{k}: {v}" for k, v in r.items()) for r in records
    )
    report("20 records as JSON", as_json)
    report("20 records as key: value lines", as_lines)
