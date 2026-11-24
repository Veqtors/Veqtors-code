"""When it breaks: the real errors."""
import pandas as pd
from common import load

df = load()
for label, f in [
    ('df["CustomerID"]', lambda: df["CustomerID"]),
    ("mask without parentheses", lambda: df[df["Country"] == "France" & df["Quantity"] > 0]),
]:
    try:
        f()
    except Exception as e:
        print(f"{label}: {type(e).__name__}: {str(e)[:120]}")
