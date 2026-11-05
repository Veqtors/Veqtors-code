"""Synthetic teaching arithmetic for the draft's by-hand section and practice task.

These six and five rows are invented for teaching. They are not from the UCI data.
Run: uv run python toy.py   (asserts every number the draft prints)
"""
import json

# (label, age in days, water-to-cement ratio, strength in MPa)
ROWS = [("A", 3, 0.6, 14), ("B", 7, 0.6, 20), ("C", 28, 0.6, 32),
        ("D", 28, 0.4, 50), ("E", 90, 0.5, 44), ("F", 90, 0.4, 56)]
NU = 0.5


def best_stump(rows, resid):
    """Try every 'feature <= threshold' split; return the one with the lowest squared error."""
    best = None
    for f, name in ((1, "age"), (2, "w/c")):
        for t in sorted({r[f] for r in rows})[:-1]:
            left = [e for r, e in zip(rows, resid) if r[f] <= t]
            right = [e for r, e in zip(rows, resid) if r[f] > t]
            ml, mr = sum(left) / len(left), sum(right) / len(right)
            sse = sum((e - ml) ** 2 for e in left) + sum((e - mr) ** 2 for e in right)
            if best is None or sse < best["sse"]:
                best = {"feature": name, "f": f, "threshold": t, "left": ml, "right": mr, "sse": sse}
    return best


def stats(pred, y):
    r = [a - p for a, p in zip(y, pred)]
    return r, sum(e * e for e in r), sum(abs(e) for e in r) / len(r)


y = [r[3] for r in ROWS]
F0 = sum(y) / len(y)
pred = [F0] * len(y)
r0, sse0, mae0 = stats(pred, y)
out = {"F0": F0, "round0": {"resid": r0, "sse": sse0, "mae": mae0}, "rounds": []}
for m in (1, 2):
    resid = stats(pred, y)[0]
    s = best_stump(ROWS, resid)
    h = [s["left"] if row[s["f"]] <= s["threshold"] else s["right"] for row in ROWS]
    pred = [p + NU * v for p, v in zip(pred, h)]
    r, sse, mae = stats(pred, y)
    out["rounds"].append({"stump": {k: s[k] for k in ("feature", "threshold", "left", "right")},
                          "pred": pred, "resid": r, "sse": sse, "mae": mae})
# the first stump alone, at full strength (nu = 1): the "weak rule"
s1 = out["rounds"][0]["stump"]
full = [F0 + (s1["left"] if row[2] <= s1["threshold"] else s1["right"]) for row in ROWS]
out["stump1_full_strength"] = {"pred": full, "mae": stats(full, y)[2]}

assert F0 == 36 and r0 == [-22, -16, -4, 14, 8, 20] and sse0 == 1416 and mae0 == 14
a, b = out["rounds"]
assert (a["stump"]["feature"], a["stump"]["threshold"], a["stump"]["left"], a["stump"]["right"]) == ("w/c", 0.5, 14, -14)
assert a["pred"] == [29, 29, 29, 43, 43, 43] and a["resid"] == [-15, -9, 3, 7, 1, 13]
assert a["sse"] == 534 and a["mae"] == 8
assert (b["stump"]["feature"], b["stump"]["threshold"], b["stump"]["left"], b["stump"]["right"]) == ("age", 7, -12, 6)
assert b["pred"] == [23, 23, 32, 46, 46, 46] and b["resid"] == [-9, -3, 0, 4, -2, 10]
assert b["sse"] == 210 and abs(b["mae"] - 28 / 6) < 1e-12
assert full == [22, 22, 22, 50, 50, 50] and abs(out["stump1_full_strength"]["mae"] - 32 / 6) < 1e-12

# practice task: 5 rows, given stump "age <= 7", nu = 0.5
P_AGE, P_Y = [3, 7, 28, 56, 90], [10, 20, 30, 40, 50]
p0 = sum(P_Y) / 5
pr = [v - p0 for v in P_Y]
left = sum(pr[:2]) / 2
right = sum(pr[2:]) / 3
p1 = [p0 + NU * (left if a <= 7 else right) for a in P_AGE]
pr1 = [v - p for v, p in zip(P_Y, p1)]
practice = {"F0": p0, "resid0": pr, "leaf_left": left, "leaf_right": right, "F1": p1, "resid1": pr1,
            "mae0": sum(map(abs, pr)) / 5, "mae1": sum(map(abs, pr1)) / 5}
assert p0 == 30 and pr == [-20, -10, 0, 10, 20] and (left, right) == (-15, 10)
assert p1 == [22.5, 22.5, 35, 35, 35] and pr1 == [-12.5, -2.5, -5, 5, 15]
assert practice["mae0"] == 12 and practice["mae1"] == 8
out["practice"] = practice
print(json.dumps(out, indent=1))
