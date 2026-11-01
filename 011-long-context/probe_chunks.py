"""Feeds a long prompt in chunks through the KV cache, so attention stays small."""
import time
import warnings

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from common import build_pool, load

warnings.simplefilter("always")
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float16).to("cuda").eval()
questions, texts, _ = load()
lengths = [len(tokenizer.encode(t)) for t in texts]
order = build_pool(questions[0], 0, 34_000, lengths)
tokens = tokenizer.encode("\n\n".join(texts[i] for i in order))
for size in (4_000, 8_000, 16_000):
    for chunk in (512, 1024):
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        cache = None
        start = time.perf_counter()
        with torch.no_grad():
            for i in range(0, size, chunk):
                ids = torch.tensor([tokens[i:min(i + chunk, size)]], device="cuda")
                cache = model(input_ids=ids, past_key_values=cache, use_cache=True).past_key_values
        torch.cuda.synchronize()
        print(f"{size:>6} tokens  chunk {chunk}  {time.perf_counter() - start:6.2f} s  peak {torch.cuda.max_memory_allocated() / 2**30:.2f} GiB", flush=True)
        del cache
