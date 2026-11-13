# DE-05 results (measured 2026-11-13)

Windows 11, Python 3.13.9, pandas 3.1.1, openpyxl 3.1.5, on the official `online_retail_II.xlsx` from UCI (zip 45,622,418 bytes; xlsx 45,622,278 bytes).

- `uv run pytest -q`: 5 passed.
- Download: 3,824 s at about 11.9 KB/s. `Range` request answered with HTTP 200, so no resume.
- Reading both sheets: 35 s in `first_look.py`; peak working set 626 MB (whole process).
- Sheets: 525,461 + 541,910 = 1,067,371 rows. 22,523 rows from 2010-12-01 to 2010-12-09 are in both sheets.
- Without `dtype`, sheet 1's Invoice cells were 515,252 integers and 10,209 strings; StockCode cells were 445,349 integers and 80,112 strings (mixed types). A truncated copy of an in-progress zip (2,686,976 bytes) raised `BadZipFile`.
- Exact repeats: 12,133 inside the sheets, 34,335 once stacked.
- Documented versus measured: invoice with lowercase c (as documented) 0; uppercase C 19,494; invoice neither 6 digits nor C+6 digits 6; stock code not 5 digits 134,986; no Customer ID 243,007.
- How many orders: 1,067,371 rows; 53,628 distinct invoices; 45,336 not starting with C; 40,077 of those with at least one sold line.
- Ten-row sample: 10 rows, 3 invoices, 2 not starting with C, 1 with a sold line.
