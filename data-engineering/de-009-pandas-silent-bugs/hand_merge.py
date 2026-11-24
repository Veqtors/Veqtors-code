"""Five invoice lines joined to a product table, counted by hand first."""
import pandas as pd
from pandas.errors import MergeError
from common import SLICE, expected_rows, load, lookup

df = load()
lines = df.loc[SLICE[0]:SLICE[1], ["Invoice", "StockCode", "Quantity", "Price"]]
products = lookup(df)
products = products[products["StockCode"].isin(lines["StockCode"])]
pd.set_option("display.width", 200)
print(lines.to_string()); print(); print(products.to_string())

left_n, right_n = lines["StockCode"].value_counts(), products["StockCode"].value_counts()
for code in left_n.index:
    print(f"{code}: {left_n[code]} line(s) x {right_n[code]} description(s) = {left_n[code] * right_n[code]}")
print("rows out by the rule:", int((left_n * right_n).sum()))

out = lines.merge(products, on="StockCode", how="left")
rev = lambda f: round((f["Quantity"] * f["Price"]).sum(), 2)
print("merge: rows", len(lines), "->", len(out), "| revenue", rev(lines), "->", rev(out))
assert len(out) == expected_rows(lines, products, "StockCode")
try:
    lines.merge(products, on="StockCode", how="left", validate="many_to_one")
except MergeError as e:
    print("validate='many_to_one' raises MergeError:", e)
fixed = lines.merge(products.drop_duplicates("StockCode"), on="StockCode", how="left", validate="many_to_one")
print("one description per code: rows", len(fixed), "| revenue", rev(fixed))
