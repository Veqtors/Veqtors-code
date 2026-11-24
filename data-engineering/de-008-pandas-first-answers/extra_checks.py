"""Numbers the draft quotes that top_five.py does not print."""
from common import NEEDED, load, december_uk, top_five

df = load(NEEDED)
uk = december_uk(df)
groups = uk.groupby(["StockCode", "Description"]).ngroups
print("groupby [StockCode, Description] groups:", groups, "| distinct StockCodes:", uk["StockCode"].nunique())
dup = uk.duplicated(keep="first")
overlap = uk["InvoiceDate"] < "2010-12-10"
print("duplicate rows:", int(dup.sum()), "| of those dated 1-9 Dec:", int((dup & overlap).sum()))
print("duplicate rows dated 10-31 Dec:", int((dup & ~overlap).sum()))
for code in ("AMAZONFEE", "DOT", "84029E"):
    print(code, "descriptions in full table:", df.loc[df["StockCode"] == code, "Description"].unique().tolist())
