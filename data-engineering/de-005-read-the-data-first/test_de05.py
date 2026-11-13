import zipfile

import pandas as pd

from fetch_data import check_zip
from first_look import documented_vs_measured, order_counts, sheet_overlap
from sample_rows import sample_frame


def test_three_answers_on_the_ten_rows():
    assert order_counts(sample_frame()) == {
        "rows": 10,
        "distinct invoices": 3,
        "distinct invoices not starting with C": 2,
        "...and with at least one sold line": 1,
    }


def test_documented_vs_measured_on_the_ten_rows():
    got = documented_vs_measured(sample_frame())
    assert got["invoice is 6 digits"] == 9
    assert got["invoice is C + 6 digits (uppercase)"] == 1
    assert got["invoice is c + 6 digits (lowercase, as documented)"] == 0
    assert got["invoice is anything else"] == 0
    assert got["stock code is not 5 digits"] == 1
    assert got["rows with no Customer ID"] == 1


def test_check_zip_accepts_a_whole_zip_and_rejects_a_cut_one(tmp_path):
    whole = tmp_path / "whole.zip"
    with zipfile.ZipFile(whole, "w") as archive:
        archive.writestr("a.txt", "hello" * 1000)
    assert check_zip(whole) is None
    cut = tmp_path / "cut.zip"
    cut.write_bytes(whole.read_bytes()[:-30])
    assert check_zip(cut) is not None


def test_check_zip_rejects_a_text_file(tmp_path):
    bad = tmp_path / "bad.zip"
    bad.write_text("not a zip")
    assert "not a zip" in check_zip(bad)


def test_sheet_overlap_finds_shared_dates_and_rows():
    cols = ["Invoice", "InvoiceDate"]
    first = pd.DataFrame([["1", "2010-12-08"], ["2", "2010-12-09"], ["2", "2010-12-09"]], columns=cols)
    second = pd.DataFrame([["2", "2010-12-09"], ["3", "2010-12-10"]], columns=cols)
    first["InvoiceDate"] = pd.to_datetime(first["InvoiceDate"])
    second["InvoiceDate"] = pd.to_datetime(second["InvoiceDate"])
    got = sheet_overlap(first, second)
    assert got["dates in both sheets"] == "2010-12-09 to 2010-12-09"
    assert got["sheet 1 rows in that window"] == 2
    assert got["sheet 2 rows in that window"] == 1
    assert got["exact repeats inside each sheet"] == 1
    assert got["exact repeats once stacked"] == 2
