"""The ten rows worked by hand: the same four moves, small enough to check with a pencil."""
import pandas as pd
from common import SLICE, NEEDED, load, december_uk, top_five

df = load(NEEDED)
ten = df.loc[SLICE[0]:SLICE[1]]
pd.set_option("display.width", 200)
print(ten.to_string())
print("\nrevenue per line:", (ten["Quantity"] * ten["Price"]).round(2).tolist())
mask = ten["Country"] == "United Kingdom"
print("mask (United Kingdom):", mask.tolist())
print("shape: all", ten.shape, "-> kept", ten[mask].shape)
print("\ntop five (all UK rows, cancellation still inside):")
print(top_five(ten[mask]).round(2).to_string(index=False))
print("\ntop five without the cancellation:")
print(top_five(ten[mask & ~ten["Invoice"].str.startswith("C")]).round(2).to_string(index=False))
