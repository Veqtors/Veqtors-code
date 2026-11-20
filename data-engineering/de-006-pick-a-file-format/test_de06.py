from hand_slice import as_columns, as_csv, as_jsonl
from sample_rows import sample_frame
import io
import pandas as pd


def test_csv_and_jsonl_have_ten_rows():
    df = sample_frame()
    assert as_csv(df).count("\n") == 11  # header + ten rows
    assert as_jsonl(df).count("\n") == 10


def test_jsonl_is_longer_than_csv():
    df = sample_frame()
    assert len(as_jsonl(df)) > len(as_csv(df))


def test_csv_round_trip_loses_types_but_keeps_missing():
    df = sample_frame()
    back = pd.read_csv(io.StringIO(as_csv(df)))
    assert not pd.api.types.is_numeric_dtype(back["Invoice"])  # C492201 forces text
    assert not pd.api.types.is_datetime64_any_dtype(back["InvoiceDate"])  # dates come back as text
    assert back["Customer ID"].isna().sum() == 1


def test_parquet_round_trip_keeps_dtypes(tmp_path):
    df = sample_frame()
    df.to_parquet(tmp_path / "t.parquet", engine="pyarrow", index=False)
    back = pd.read_parquet(tmp_path / "t.parquet", engine="pyarrow")
    assert back.dtypes.equals(df.dtypes)


def test_columns_layout_has_a_line_per_column():
    assert as_columns(sample_frame()).count("\n") == 8
