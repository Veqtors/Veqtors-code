"""What SFT actually trains on: one conversation as a single token stream, and which tokens count.

Veqtors #3, "The same model, trained three times". Run: python chat_template.py
Needs: pip install -r requirements.txt. Downloads only the tokenizer.
"""
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
messages = [{"role": "user", "content": "What is the capital of Pakistan?"},
            {"role": "assistant", "content": "The capital of Pakistan is Islamabad."}]

prompt = tok.apply_chat_template(messages[:1], tokenize=False, add_generation_prompt=True)
full = tok.apply_chat_template(messages, tokenize=False)
print(full)

n_prompt = len(tok(prompt)["input_ids"])
n_full = len(tok(full)["input_ids"])
print(f"prompt tokens   : {n_prompt}   (system + user + '<|im_start|>assistant')")
print(f"response tokens : {n_full - n_prompt}   (the answer, end marker and trailing newline)")
print(f"share trained on, if the prompt is masked: {(n_full - n_prompt) / n_full:.0%}")
