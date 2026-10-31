import sys
import tiktoken

sys.stdout.reconfigure(encoding="utf-8")
SAMPLES = [
    "hello", " hello", "Hello", "HELLO",
    "tokenization", "unbelievably", "Islamabad", "Karachi", "Peshawar",
    "1234567", "12,345.67", "3.14159265", "2026-11-17",
    "🙂", "👩‍💻",
    "def add(a, b):\n    return a + b",
    '{"name": "Imtiaz", "city": "Lahore", "active": true}',
    "name: Imtiaz\ncity: Lahore\nactive: true",
    "https://github.com/veqtors/Veqtors-code/tree/main/001-transformer",
    "The capital of Pakistan is Islamabad.",
    "پاکستان کا دارالحکومت اسلام آباد ہے۔",
]
for name in ("cl100k_base", "o200k_base"):
    enc = tiktoken.get_encoding(name)
    print("==", name, "vocab", enc.n_vocab)
    for s in SAMPLES:
        ids = enc.encode(s)
        parts = [enc.decode_single_token_bytes(i).decode("utf-8", "replace") for i in ids]
        words = len(s.split())
        print(f"{len(ids):3d} tok {words:2d} words {s!r:.50} -> {parts}"[:170])
