# DE-08 results

Run 2026-11-24. Windows 11, Python 3.14.0, 64 logical cores, pandas via `uv.lock`, DE-06's typed Parquet (`code/data/online_retail_II.parquet`, 7,236,529 bytes). Timings are best of three reads, warm cache; everything else is one run.

## Shapes (`top_five.py`)
- Loaded: 1,067,371 rows x 7 columns
- UK, December 2010: 61,472 rows
- Distinct StockCodes in that slice: 2,802. Groupby on [StockCode, Description] returns 2,810 groups (`extra_checks.py`).

## Top five by revenue, UK, December 2010
| Variant | #1 | #2 | #3 | #4 | #5 |
|---|---|---|---|---|---|
| Naive (all rows) | 22423 REGENCY CAKESTAND 3 TIER 38,206.59 | DOT DOTCOM POSTAGE 37,474.56 | 22086 PAPER CHAIN KIT 50'S CHRISTMAS 14,374.00 | 85123A WHITE HANGING HEART T-LIGHT HOLDER 13,862.57 | 84029E RED WOOLLY HOTTIE WHITE HEART. 13,717.32 |
| Without 931 cancellation rows | 22423 39,128.04 | DOT 37,474.56 | AMAZONFEE 27,082.66 | 85123A 15,150.72 | 22086 14,412.35 |
| Without 21,844 exact duplicates | 22423 25,186.91 | DOT 24,671.19 | 84029E 9,246.73 | 22086 9,152.05 | 85123A 8,824.31 |
| Without duplicates and cancellations | 22423 25,929.56 | DOT 24,671.19 | AMAZONFEE 13,541.33 | 85123A 10,109.91 | 84029E 9,246.73 |

- Exact duplicates are 21,844 of 61,472 rows (35.5%): 1 to 9 Dec 2010 sits in both Excel sheets (DE-06 research).
- Cancellation definitions: Invoice starts with `C` vs `Quantity < 0` disagree on 134 rows of the UK December 2010 slice (`top_five.py` line 13).

## Extra checks (`extra_checks.py`)
- Of the 21,844 duplicate rows, 21,668 are dated 1 to 9 Dec 2010 (the sheet overlap) and 176 are dated 10 to 31 Dec.
- Descriptions in the full table: AMAZONFEE = "AMAZON FEE" (only value); DOT = "DOTCOM POSTAGE" (plus blanks); 84029E = "RED WOOLLY HOTTIE WHITE HEART." (plus blanks).

## Hand slice (ten rows, 2010-12-14, `hand_slice.py`)
- Rows (code, description, qty, price, country): 538722 21756 BATH BUILDING BLOCK WORD 7 @5.95; 22694 WICKER STAR 3 @2.10; 21135 VICTORIAN METAL POSTCARD SPRING 8 @1.69; 20763 DAISY SKETCHBOOK 1 @3.75; 20777 CHRYSANTHEMUM NOTEBOOK 1 @1.65 (UK); C538723 22333 -7 @1.65, 22094 -5 @1.25, 21217 -1 @9.95 (Australia); 538724 22311 1 @2.95 (UK); C538725 22680 -20 @1.25 (UK). Line revenue: 41.65, 6.30, 13.52, 3.75, 1.65, -11.55, -6.25, -9.95, 2.95, -25.00. Mask: T T T T T F F F T T.
- UK mask keeps 7 of 10 rows. Top five: 21756 41.65, 21135 13.52, 22694 6.30, 20763 3.75, 22311 2.95. Removing the one UK cancellation row (C538725, -25.00) does not change the list.

## `columns=` cost (`time_load.py`, one machine, warm cache)
- 8 columns: 0.033 s, 123 MB in memory
- 7 needed columns: 0.029 s, 114 MB
- 3 columns (StockCode, Quantity, Price): 0.024 s, 31 MB

## Errors shown (`breaks.py`)
- `df["CustomerID"]`: `KeyError: 'CustomerID'`
- unparenthesised `&` mask: `TypeError: Cannot perform 'rand_' with a dtyped [int64] array and scalar of type [bool]`
