"""What the KV cache saves on a 16k prompt, and what one edited document costs.

Times one forward pass, which is the prompt processing before the first answer token.
Four cases: no cache, full prefix cached, last document edited, first document edited.
Needs a GPU. Run: uv run python prefix_cache_test.py
"""
import copy
import statistics
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from common import build_pool, load

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
REPEATS = 7
CHUNK = 1024
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float16).to("cuda").eval()
questions, texts, _ = load()
lengths = [len(tokenizer.encode(t)) for t in texts]
order = build_pool(questions[0], 0, 16_000, lengths)


def encode(text):
    return tokenizer.encode(text, add_special_tokens=False)


pieces = [encode(f"[{n}] {texts[i]}\n\n") for n, i in enumerate(order, start=1)]
corpus = [token for piece in pieces for token in piece]
question = encode(f"Question: {questions[0]['question']}")
last_doc_length = len(pieces[-1])


def forward(tokens, cache=None):
    """Chunks long prompts, because a whole 16k prompt doesn't fit in 6 GB here."""
    torch.cuda.synchronize()
    start = time.perf_counter()
    with torch.no_grad():
        for i in range(0, len(tokens), CHUNK):
            ids = torch.tensor([tokens[i:i + CHUNK]], device="cuda")
            cache = model(input_ids=ids, past_key_values=cache, use_cache=True).past_key_values
    torch.cuda.synchronize()
    return cache, time.perf_counter() - start


def timed(label, tokens, make_cache):
    runs = []
    for _ in range(REPEATS):
        cache = make_cache()
        _, seconds = forward(tokens, cache)
        runs.append(seconds)
    print(f"{label:<24} {len(tokens):>6} tokens processed  {statistics.median(runs) * 1000:9.1f} ms", flush=True)


full, _ = forward(corpus)
size = sum(t.nelement() * t.element_size() for name in ("keys", "values") for layer in full.layers for t in [getattr(layer, name)])
print(f"corpus {len(corpus)} tokens, question {len(question)} tokens, KV cache {size / 2**30:.2f} GiB")
print(f"peak GPU memory so far {torch.cuda.max_memory_allocated() / 2**30:.2f} GiB")

timed("no cache", corpus + question, lambda: None)
timed("prefix cached", question, lambda: copy.deepcopy(full))


def cropped():
    cache = copy.deepcopy(full)
    cache.crop(-last_doc_length)
    return cache


edited = encode("[edited] ") + pieces[-1]
timed("last document edited", edited + question, cropped)
first_edit = encode("[edited] ") + corpus
timed("first document edited", first_edit + question, lambda: None)
