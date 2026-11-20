"""Follow one value of DE-01's ten rows through five layers. No download needed."""
from decimal import Decimal

from sample_rows import sample_frame

ROW = 1  # invoice C492201, customer 14062, price 2.95


def main() -> None:
    df = sample_frame()
    row = df.iloc[ROW]
    text = str(int(row["Customer ID"]))
    print("1 bytes -> characters :", " ".join(f"{b:02x}" for b in text.encode("utf-8")), "->", repr(text))
    print("2 characters -> type  :", repr(text), "->", float(row["Customer ID"]), "(the column holds a missing value, so it is float)")
    print("3 absence             :", float(row["Customer ID"]), "next to", float(df.iloc[0]["Customer ID"]), "(row 1 has no customer)")
    print("4 date -> moment      :", row["InvoiceDate"], "tz =", row["InvoiceDate"].tzinfo)
    print("5 number -> money     :", f"price {float(row['Price'])} goes into a sum: {float(row['Price'])} x {int(row['Quantity'])} = {float(row['Price']) * int(row['Quantity'])}")
    line = df.iloc[4]  # 18 coffee mugs at 2.55, the example in the draft
    print("  the draft's example :", f"float {float(line['Price']) * int(line['Quantity'])!r}  vs  exact {Decimal('2.55') * 18}  (2.55 x 18)")


if __name__ == "__main__":
    main()
