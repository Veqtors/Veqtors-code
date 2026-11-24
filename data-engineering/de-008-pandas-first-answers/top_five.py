"""Four moves on the full table: load, select, filter, group. Prints the shape after each."""
from common import NEEDED, load, december_uk, top_five

df = load(NEEDED)                     # move 1 and 2: load only the columns the question needs
print("loaded:", df.shape)
uk_dec = december_uk(df)              # move 3: keep only the rows the question needs
print("UK, December 2010:", uk_dec.shape)
print("distinct StockCodes:", uk_dec["StockCode"].nunique())
print("\nnaive top five (every row counted):")
print(top_five(uk_dec).round(2).to_string(index=False))                       # move 4

cancel = uk_dec["Invoice"].str.startswith("C")
print("C-prefix vs Quantity<0 disagree on", int((cancel != (uk_dec["Quantity"] < 0)).sum()), "rows")
print("\ncancellation rows in UK December 2010:", int(cancel.sum()))
print("top five without cancellations:")
print(top_five(uk_dec[~cancel]).round(2).to_string(index=False))

dup = uk_dec.duplicated(keep="first")
print("\nexact-duplicate rows in UK December 2010:", int(dup.sum()))
print("top five without duplicates:")
print(top_five(uk_dec[~dup]).round(2).to_string(index=False))
print("top five without duplicates or cancellations:")
print(top_five(uk_dec[~dup & ~cancel]).round(2).to_string(index=False))
