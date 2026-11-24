"""A key that went through float (DE-07's finding), caught by indicator=True. Reuses DE-07's setup."""
import pandas as pd
from common import load

df = load(["Customer ID"])
keyed = df.dropna(subset=["Customer ID"])
lookup = pd.DataFrame({"cust": keyed["Customer ID"].astype("int64").astype(str).drop_duplicates()})
print("rows with a customer:", len(keyed), "| lookup keys:", len(lookup))
try:
    keyed.merge(lookup, left_on="Customer ID", right_on="cust", how="left")
except ValueError as e:
    print("float key vs text key:", type(e).__name__, "-", str(e)[:120])
bad = keyed.assign(cust=keyed["Customer ID"].astype(str)).merge(lookup, on="cust", how="left", indicator=True)
num = pd.DataFrame({"Customer ID": lookup["cust"].astype("int64")})
print("float key vs int64 key (whole numbers):", keyed.merge(num, on="Customer ID", how="left", indicator=True)["_merge"].value_counts().to_dict())
print("float -> text key:", bad["_merge"].value_counts().to_dict(), "| example key:", repr(bad["cust"].iloc[0]))
good = keyed.assign(cust=keyed["Customer ID"].astype("int64").astype(str)).merge(lookup, on="cust", how="left", indicator=True, validate="many_to_one")
print("float -> int64 -> text key:", good["_merge"].value_counts().to_dict())
