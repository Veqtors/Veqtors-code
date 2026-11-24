"""A running total per customer depends on row order. The file's order goes backwards once."""
import pandas as pd
from common import load

df = load(["Invoice", "InvoiceDate", "Quantity", "Price", "Customer ID"])
back = df["InvoiceDate"].diff() < pd.Timedelta(0)
print("rows dated earlier than the row above:", int(back.sum()), "| at row", back[back].index.tolist())
print(df.loc[back[back].index[0] - 1: back[back].index[0], ["Invoice", "InvoiceDate"]].to_string())

c = df.dropna(subset=["Customer ID"]).copy()
c["revenue"] = c["Quantity"] * c["Price"]
by_file = c.groupby("Customer ID")["revenue"].cumsum()
by_date = c.sort_values("InvoiceDate", kind="stable").groupby("Customer ID")["revenue"].cumsum().reindex(c.index)
differs = (by_file - by_date).abs() > 0.005
print("customers:", c["Customer ID"].nunique(), "| customers with rows out of date order:",
      int(c.groupby("Customer ID")["InvoiceDate"].apply(lambda s: not s.is_monotonic_increasing).sum()))
print("rows where the running total differs by file order vs date order:", int(differs.sum()), "of", len(c))
print("final totals identical:", bool(((by_file.groupby(c["Customer ID"]).last() - by_date.groupby(c["Customer ID"]).last()).abs() < 0.005).all()))
cid = c[c["Customer ID"].isin(c.loc[differs, "Customer ID"])]["Customer ID"].value_counts().index[-1]  # fewest rows, easiest to read
ex = c[c["Customer ID"] == cid].assign(running_file=by_file, running_date=by_date)
print("example customer", int(cid)); print(ex[["Invoice", "InvoiceDate", "revenue", "running_file", "running_date"]].round({"revenue": 2, "running_file": 2, "running_date": 2}).to_string())
