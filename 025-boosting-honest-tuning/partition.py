"""Split whole recipes into training and a sealed test set, once. Run before run.py."""
import json

import numpy as np

from common import PARTITIONS, fetch_data, load_config, load_frame, sha256

if PARTITIONS.exists():
    raise SystemExit("partitions.json already exists; the split is made once. Delete it only to reproduce from scratch.")

cfg = load_config()
digest = fetch_data()
df = load_frame()
recipes = np.array(sorted(df["recipe"].unique()))
rng = np.random.default_rng(cfg["seed"])
order = rng.permutation(recipes)
n_test = round(cfg["partition"]["test_fraction_of_recipes"] * len(recipes))
test = sorted(order[:n_test].tolist())
PARTITIONS.write_text(json.dumps({
    "data_sha256": digest,
    "seed": cfg["seed"],
    "n_recipes": int(len(recipes)),
    "n_test_recipes": n_test,
    "n_test_rows": int(df["recipe"].isin(test).sum()),
    "test_recipes": test,
}, indent=1), encoding="utf-8")
print(f"{n_test} test recipes, {int(df['recipe'].isin(test).sum())} test rows; sha256 {sha256(PARTITIONS)}")
