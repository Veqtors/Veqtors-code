"""The same merge at full size: a product lookup built from the retail table, joined back."""
from pandas.errors import MergeError
from common import checked_merge, expected_rows, load, lookup

df = load(["StockCode", "Description", "Quantity", "Price"])
rev = lambda f: round((f["Quantity"] * f["Price"]).sum(), 2)
lines = df.drop(columns="Description")
products = lookup(df)
codes = products["StockCode"].value_counts()
print("lines:", len(lines), "revenue", rev(lines), "| distinct codes", df["StockCode"].nunique())
print("lookup rows:", len(products), "| codes with more than one description:", int((codes > 1).sum()),
      "| codes with no non-blank description:", df["StockCode"].nunique() - len(codes))
out = lines.merge(products, on="StockCode", how="left")
print("merge: rows", len(lines), "->", len(out), f"(x{len(out) / len(lines):.2f})", "| revenue", rev(lines), "->", rev(out))
print("rows by the rule:", expected_rows(lines, products, "StockCode"), "| unmatched lines (no description):", int(out["Description"].isna().sum()))
blanks = df[["StockCode", "Description"]].drop_duplicates()  # blanks kept
kept = lines.merge(blanks, on="StockCode", how="left")
print("blanks kept in the lookup: lookup rows", len(blanks), "| merge rows", len(kept), "| revenue", rev(kept))
try:
    lines.merge(products, on="StockCode", how="left", validate="many_to_one")
except MergeError as e:
    print("validate='many_to_one' raises MergeError:", e)
fixed = lines.merge(products.drop_duplicates("StockCode"), on="StockCode", how="left", validate="many_to_one")
try:
    checked_merge(lines.assign(revenue=lines["Quantity"] * lines["Price"]), products, "StockCode", "revenue")
except (MergeError, AssertionError) as e:
    print("checked_merge on the fan-out lookup:", type(e).__name__, "-", str(e).splitlines()[0])
print("one description per code: rows", len(fixed), "| revenue", rev(fixed))
