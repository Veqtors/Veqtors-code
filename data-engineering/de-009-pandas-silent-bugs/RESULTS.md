# DE-09 results

## Key numbers
- Hand slice: invoice 492521, rows 37895 to 37899 (17 Dec 2009). 5 lines, 3 codes. Product table for those codes: 5 rows (85014A and 85014B have two descriptions each). Rule: 3 x 1 + 1 x 2 + 1 x 2 = 7 rows out. Revenue 71.40 to 95.20. `validate="many_to_one"` raises `MergeError: Merge keys are not unique in right dataset; not a many-to-one merge`. One description per code: 5 rows, 71.40.
- Full size: lookup = distinct (StockCode, Description) pairs with blanks dropped, 6,570 rows. 1,232 of 5,305 codes have more than one description; 355 codes have no non-blank description (363 lines get no description). Merge: 1,067,371 rows to 1,736,410 (x1.63); revenue 19,287,250.57 to 36,003,189.22. The rule gives 1,736,410. One description per code: 1,067,371 rows, 19,287,250.57. Blanks kept in the lookup (9,021 rows): 2,120,243 rows, revenue 44,502,452.77.
- Key drift (reuses DE-07's finding): 824,364 rows with a customer; float key against int64 key matches all 824,364 (both 824,364); float key against text key raises `ValueError` (loud). Float turned into text gives '13085.0': `indicator=True` reports left_only 824,364, both 0. Float to int64 to text: both 824,364.
- Window order: file order goes backwards once, at row 525,461 (2010-12-09 20:01 then 2010-12-01 08:26), where the second Excel sheet starts. 150 of 5,942 customers have rows out of date order. 7,331 of 824,364 rows have a different running total by file order vs date order; final totals are identical. Example customer 15299 (invoices 536809 to 536811 appear in both sheets).
- Guard: `checked_merge` in `common.py` (validate="many_to_one" plus asserts on rows and total) raises `MergeError` on the fan-out lookup and passes with one description per code.
- Tests: 4 passed (`test_de09.py`; one needs the Parquet).

Run 2026-11-24. Windows 11, Python 3.13.9 (uv.lock), 64 logical cores. DE-06's typed Parquet in data/. One run each.


## hand_merge.py
```
      Invoice StockCode  Quantity  Price
37895  492521    85014B         2   5.95
37896  492521   15056BL         3   5.95
37897  492521   15056BL         3   5.95
37898  492521   15056BL         2   5.95
37899  492521    85014A         2   5.95

       StockCode                       Description
75        85014A  BLACK/BLUE DOTS RUFFLED UMBRELLA
76        85014B   RED/WHITE DOTS RUFFLED UMBRELLA
613      15056BL           EDWARDIAN PARASOL BLACK
351980    85014A      BLACK/BLUE POLKADOT UMBRELLA
356197    85014B            RED RETROSPOT UMBRELLA
15056BL: 3 line(s) x 1 description(s) = 3
85014B: 1 line(s) x 2 description(s) = 2
85014A: 1 line(s) x 2 description(s) = 2
rows out by the rule: 7
merge: rows 5 -> 7 | revenue 71.4 -> 95.2
validate='many_to_one' raises MergeError: Merge keys are not unique in right dataset; not a many-to-one merge

Duplicates in right:
 StockCode
   85014A
   85014B ...
one description per code: rows 5 | revenue 71.4
```


## fanout.py
```
lines: 1067371 revenue 19287250.57 | distinct codes 5305
lookup rows: 6570 | codes with more than one description: 1232 | codes with no non-blank description: 355
merge: rows 1067371 -> 1736410 (x1.63) | revenue 19287250.57 -> 36003189.22
rows by the rule: 1736410 | unmatched lines (no description): 363
blanks kept in the lookup: lookup rows 9021 | merge rows 2120243 | revenue 44502452.77
validate='many_to_one' raises MergeError: Merge keys are not unique in right dataset; not a many-to-one merge

Duplicates in right:
 StockCode
    22195
    21733
   85123A
    71477
    22232 ...
checked_merge on the fan-out lookup: MergeError - Merge keys are not unique in right dataset; not a many-to-one merge
one description per code: rows 1067371 | revenue 19287250.57
```


## key_drift.py
```
rows with a customer: 824364 | lookup keys: 5942
float key vs text key: ValueError - You are trying to merge on float64 and str columns for key 'Customer ID'. If you wish to proceed you should use pd.conca
float key vs int64 key (whole numbers): {'both': 824364, 'left_only': 0, 'right_only': 0}
float -> text key: {'left_only': 824364, 'right_only': 0, 'both': 0} | example key: '13085.0'
float -> int64 -> text key: {'both': 824364, 'left_only': 0, 'right_only': 0}
```


## window_order.py
```
rows dated earlier than the row above: 1 | at row [525461]
       Invoice         InvoiceDate
525460  538171 2010-12-09 20:01:00
525461  536365 2010-12-01 08:26:00
customers: 5942 | customers with rows out of date order: 150
rows where the running total differs by file order vs date order: 7331 of 824364
final totals identical: True
example customer 15299
        Invoice         InvoiceDate  revenue  running_file  running_date
735     C489535 2009-12-01 12:11:00    -9.00         -9.00         -9.00
736     C489535 2009-12-01 12:11:00   -19.00        -28.00        -28.00
52638    494210 2010-01-12 11:34:00   731.52        703.52        703.52
367054   524971 2010-10-01 14:55:00   612.00       1315.52       1315.52
464418   533254 2010-11-16 15:11:00   306.00       1621.52       1621.52
507788   536809 2010-12-02 16:48:00  1003.20       2624.72       2624.72
507789   536810 2010-12-02 16:50:00   303.96       2928.68       3931.88
507790   536811 2010-12-02 16:51:00   527.85       3456.53       4763.69
530311   536809 2010-12-02 16:48:00  1003.20       4459.73       3627.92
530312   536810 2010-12-02 16:50:00   303.96       4763.69       4235.84
530313   536811 2010-12-02 16:51:00   527.85       5291.54       5291.54
613532  C543758 2011-02-11 15:07:00   -65.91       5225.63       5225.63
652502   547154 2011-03-21 12:06:00   600.00       5825.63       5825.63
681189  C550010 2011-04-14 10:29:00    -2.20       5823.43       5823.43
681190  C550010 2011-04-14 10:29:00    -3.81       5819.62       5819.62
747225  C556274 2011-06-09 19:46:00  -600.00       5219.62       5219.62
768368   558381 2011-06-28 17:01:00   600.00       5819.62       5819.62
819300  C562622 2011-08-08 12:37:00   -48.00       5771.62       5771.62
899119   569339 2011-10-03 14:18:00   830.00       6601.62       6601.62
899120   569340 2011-10-03 14:19:00   642.00       7243.62       7243.62
```
