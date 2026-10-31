# Measured results (run 2026-10-29)

Our own measurements, CPU only, transformers 5.21.0, greedy decoding (same output every run). Reproduce with the scripts in this folder.

## base_vs_instruct.py: Qwen2.5-0.5B base vs Instruct, same prompts

Configs are identical except the end-of-sequence token (base `<|endoftext|>`, Instruct `<|im_end|>`) and one sliding-window setting that is inactive by default: 24 layers, hidden size 896, vocab 151,936.

| Prompt | Base, raw prompt | Instruct, chat template |
|---|---|---|
| What is the capital of Pakistan? | " The capital of Pakistan is Islamabad." then stops | "The capital of Pakistan is Islamabad." |
| Reply with only the word yes or no: is 17 a prime number? | " 17 is a prime number." (ignores the format) | "yes" |
| List three tips… one short line per tip. | Long bolded paragraphs, cut off at 60 tokens after tip 2 | Three tips, shorter but still more than one line each, cut off at 60 tokens |
| Translate to French: The meeting is moved to Friday. | "Le débat est mis en place pour le vendredi." (wrong meaning) | "La réunion est mise en place pour mardi." (wrong day: mardi = Tuesday) |

Control, the base model given the Instruct chat template: it answers the first and third prompts, but never emits `<|im_end|>`, adds a stray word ("Snapdragon"), and on the translation prompt introduces itself as Qwen in French and loops.

What this shows, on 4 prompts with a 0.5B model (a demo, not a benchmark):
- The base model already answers a simple factual question. It doesn't ramble on every prompt.
- Post-training shows up in **format and constraints** ("only yes or no") and in ending the turn with the right token.
- Post-training didn't make the small model accurate: both got the translation wrong, in different ways.

## chat_template.py: what SFT trains on

One question and answer through the Qwen2.5 Instruct chat template (it inserts a default system prompt by itself):
- 45 tokens in total: **36 prompt tokens** (system + user + the assistant header) and **9 response tokens**.
- If the prompt is masked from the loss, SFT trains on **20%** of this sequence.

## dpo_loss.py: the DPO loss on toy log-probs (beta 0.1)

| Shift toward chosen (log-prob units, each side) | Loss |
|---|---|
| 0 (policy = reference) | 0.693 (= log 2) |
| 5 | 0.313 |
| 10 | 0.127 |
| 20 | 0.018 |
| 40 | 0.000 |
