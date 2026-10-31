"""The DPO loss in NumPy: push the chosen answer up and the rejected one down, relative to a frozen reference.

Veqtors #3, "The same model, trained three times". Run: python dpo_loss.py
Inputs are summed log-probs of each full response (toy numbers, not from a real model).
"""
import numpy as np


def dpo_loss(pi_chosen, pi_rejected, ref_chosen, ref_rejected, beta=0.1):
    margin = (pi_chosen - ref_chosen) - (pi_rejected - ref_rejected)   # how far the policy moved toward "chosen"
    return -np.log(1 / (1 + np.exp(-beta * margin)))                     # -log sigmoid(beta * margin)


ref_c, ref_r = -42.0, -40.0          # the reference model slightly prefers the rejected answer
print(" shift  | loss")
for shift in [0, 5, 10, 20, 40]:     # the policy raises chosen by `shift` and lowers rejected by `shift`
    print(f"  {shift:>4}  | {dpo_loss(ref_c + shift, ref_r - shift, ref_c, ref_r):.3f}")
print(f"\nlog 2 = {np.log(2):.3f}: the loss when the policy still equals the reference")
