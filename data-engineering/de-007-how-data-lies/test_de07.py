import pandas as pd
from decimal import Decimal
from zoneinfo import ZoneInfo
from datetime import datetime

from lie_checks import layer1_encoding, layer2_type, layer3_absence, layer5_money
from sample_rows import sample_frame


def test_utf8_pound_read_as_latin1_is_two_characters():
    assert "£".encode("utf-8").decode("latin-1") == "Â£"
    assert layer1_encoding(sample_frame())["utf8_bytes_of_pound"] == "c2a3"


def test_float_key_as_text_matches_nothing_but_int_first_matches_all():
    r = layer2_type(sample_frame())
    assert r["float_as_text_vs_text_lookup_matched"] == 0
    assert r["int_as_text_vs_text_lookup_matched"] == 9


def test_absence_counts_on_ten_rows():
    r = layer3_absence(sample_frame())
    assert (r["missing_customer"], r["missing_description"], r["zero_price"]) == (1, 1, 1)


def test_money_float_and_exact_agree_on_ten_rows():
    r = layer5_money(sample_frame())
    assert Decimal(r["exact_decimal_sum"]) == Decimal("173.45") and abs(r["difference_float_minus_exact"]) < 1e-9


def test_uk_clock_change_hours_via_zoneinfo():
    london = ZoneInfo("Europe/London")
    assert datetime(2010, 3, 28, 0, 30, tzinfo=london).utcoffset().total_seconds() == 0  # GMT before the change
    assert datetime(2010, 3, 28, 2, 30, tzinfo=london).utcoffset().total_seconds() == 3600  # BST after it
    assert pd.Timestamp("2010-03-28 01:30").tz_localize("Europe/London", nonexistent="NaT") is pd.NaT
    assert datetime(2010, 10, 31, 1, 30, fold=0, tzinfo=london).utcoffset() != datetime(2010, 10, 31, 1, 30, fold=1, tzinfo=london).utcoffset()
