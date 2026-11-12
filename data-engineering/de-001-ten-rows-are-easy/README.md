# DE-01: count the four problems

Companion code for **DE-01, "Start data engineering with a pencil"**. You do not
need to run anything to follow the issue; nothing is installed until DE-02.

## What it does

`count_problems.py` counts, over the whole Online Retail II file:

- cancellation rows (Invoice starts with `C`, and, separately, lowercase `c`)
- rows with no Customer ID
- extra copies of exact repeats (all eight columns, first copy kept)
- rows with Price below zero and exactly zero
- unparseable dates and dates outside 2009-12-01 to 2011-12-09
- StockCodes that are not exactly five digits

and the plain total of Quantity x Price. `test_count_problems.py` checks the
script on the ten rows used in the issue (plain total 173.45).

## Run it

```
pip install -r requirements.txt
python count_problems.py path/to/online_retail_II.xlsx
python -m pytest
```

It reads every sheet of an `.xlsx`, or a `.csv` or `.parquet` file.

## Where the data comes from, and how it was checked

- Official source: UCI Online Retail II, https://archive.ics.uci.edu/dataset/502/online+retail+ii
  (CC BY 4.0, one Excel file, two sheets: "Year 2009-2010" with 525,461 data rows
  and "Year 2010-2011" with 541,910; total 1,067,371).
- The numbers in `RESULTS.md` were measured on **OpenML's Parquet copy** (dataset
  43368, 1,067,371 rows). UCI's server was throttled when this was written, and
  only the first sheet of the official file downloaded completely.
- That copy was compared with the first sheet of the official file, row by row,
  over all 525,461 rows: Quantity, Price, Customer ID, InvoiceDate and whether
  Invoice and StockCode are text or numbers all matched exactly.
- **Not yet done:** the second sheet was not compared row by row, and this script
  has not been run end to end on the official `.xlsx`. Do that before relying on
  the numbers beyond this issue.
- The dataset is not stored in this repository. Download it yourself.
