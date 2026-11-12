import pandas as pd

from count_problems import count_problems, row_total

# The ten consecutive rows used in the issue (file rows 33394-33403, 0-based).
ROWS = [
    ("492200", "20879", None, 6, "2009-12-15 16:06:00", 0.00, None),
    ("C492201", "84558A", "3D DOG PICTURE PLAYING CARDS", -25, "2009-12-15 16:15:00", 2.95, 14062.0),
    ("492202", "21536", "DAIRY MAID  SMALL  MILK JUG", 4, "2009-12-15 16:23:00", 2.10, 15514.0),
    ("492202", "20989", "URBAN CHIC CHOPSTICKS SET/5", 8, "2009-12-15 16:23:00", 1.95, 15514.0),
    ("492202", "22301", "COFFEE MUG CAT + BIRD DESIGN", 18, "2009-12-15 16:23:00", 2.55, 15514.0),
    ("492202", "22302", "COFFEE MUG PEARS  DESIGN", 6, "2009-12-15 16:23:00", 2.55, 15514.0),
    ("492202", "85107", "CUT GLASS T-LIGHT HOLDER OCTAGON", 12, "2009-12-15 16:23:00", 2.55, 15514.0),
    ("492202", "21311", "SET/4 BIRD MIRROR MAGNETS", 24, "2009-12-15 16:23:00", 2.10, 15514.0),
    ("492202", "21307", "SET/4 BUTTERFLY MIRROR MAGNETS", 24, "2009-12-15 16:23:00", 2.10, 15514.0),
    ("492202", "85107", "CUT GLASS T-LIGHT HOLDER OCTAGON", 12, "2009-12-15 16:23:00", 2.55, 15514.0),
]
COLS = ["Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Customer ID"]


def frame():
    df = pd.DataFrame(ROWS, columns=COLS)
    df["Country"] = "United Kingdom"
    return df


def test_counts_on_the_ten_rows():
    c = count_problems(frame())
    assert c["rows"] == 10
    assert c["cancellation_rows (Invoice starts with C)"] == 1
    assert c["no_customer_rows"] == 1
    assert c["exact_duplicate_extra_copies"] == 1
    assert c["price_exactly_zero"] == 1
    assert c["unparseable_dates"] == 0


def test_naive_total_of_the_ten_rows():
    assert row_total(frame()) == 173.45
