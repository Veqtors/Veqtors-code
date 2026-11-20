"""DE-01's ten rows (file rows 33394-33403), with the file's own column names."""
import pandas as pd

COLUMNS = ["Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Customer ID", "Country"]
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


def sample_frame() -> pd.DataFrame:
    df = pd.DataFrame([row + ("United Kingdom",) for row in ROWS], columns=COLUMNS)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    return df
