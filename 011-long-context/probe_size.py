"""Finds the longest prompt the GPU can process in one forward pass."""
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from common import build_pool, load

MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.float16).to("cuda").eval()
questions, texts, _ = load()
lengths = [len(tokenizer.encode(t)) for t in texts]
order = build_pool(questions[0], 0, 34_000, lengths)
tokens = tokenizer.encode("\n\n".join(texts[i] for i in order))
print(f"weights {torch.cuda.memory_allocated() / 2**30:.2f} GiB", flush=True)
for size in (2_000, 4_000, 6_000, 8_000, 10_000, 12_000, 14_000, 16_000):
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    ids = torch.tensor([tokens[:size]], device="cuda")
    try:
        start = time.perf_counter()
        with torch.no_grad():
            model(input_ids=ids, use_cache=True)
        torch.cuda.synchronize()
        print(f"{size:>6} tokens  {time.perf_counter() - start:6.2f} s  peak {torch.cuda.max_memory_allocated() / 2**30:.2f} GiB", flush=True)
    except torch.OutOfMemoryError as error:
        print(f"{size:>6} tokens  out of memory: {str(error).split('.')[0]}.{str(error).split('.')[1][:12]}", flush=True)
        break
