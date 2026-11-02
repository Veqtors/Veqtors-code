"""Shared helper v1, originally authored for issue 019; replicas must be byte-identical.

Source/provenance: wiki/sources/2026-11-01-bike-sharing-dataset-contract.md.
No fitted transformations or target-distribution filtering occur here.
"""
import csv
import hashlib
import importlib.metadata
import io
import json
import platform
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

URL = "https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip"
ZIP_SHA = "b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401"
SOURCE_SHA = "e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f"
HEADER = "instant,dteday,season,yr,mnth,hr,holiday,weekday,workingday,weathersit,temp,atemp,hum,windspeed,casual,registered,cnt".split(",")
FLOATS = ["temp", "atemp", "hum", "windspeed"]
RANGES = {"instant": (1, None), "season": (1, 4), "yr": (0, 1), "mnth": (1, 12), "hr": (0, 23), "holiday": (0, 1), "weekday": (0, 6), "workingday": (0, 1), "weathersit": (1, 4), "casual": (0, None), "registered": (0, None), "cnt": (0, None)}
SCHEMA = {"version": 1, "header": HEADER, "integers": RANGES, "finite_normalized_0_1": FLOATS, "date": "%Y-%m-%d", "policy": "fail batch; no row removal; source-calendar naive"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def versions():
    return {"python": platform.python_version(), **{p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scikit-learn", "pytest", "pyarrow", "scipy"]}}


def code_hash():
    return sha(b"".join(p.name.encode() + b"\0" + p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py"))))


class ContractError(ValueError):
    def __init__(self, rule, field=None, row=None, token=None):
        self.detail = {"rule": rule, "field": field, "row": row, "token": token}
        super().__init__(json.dumps(self.detail))


def source_bytes(data_dir, archive=None):
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    path = Path(archive) if archive else data_dir / "bike.zip"
    if not path.exists():
        payload = urllib.request.urlopen(URL, timeout=60).read()
        if sha(payload) != ZIP_SHA:
            raise ContractError("archive SHA mismatch")
        path.write_bytes(payload)
    payload = path.read_bytes()
    if sha(payload) != ZIP_SHA:
        raise ContractError("archive SHA mismatch")
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        member = z.read("hour.csv")
    if sha(member) != SOURCE_SHA:
        raise ContractError("member SHA mismatch")
    return member


def parse(raw):
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8"), newline=""), strict=True))
    if not rows or rows[0] != HEADER:
        raise ContractError("exact required header", token=rows[0] if rows else [])
    for line, row in enumerate(rows[1:], 2):
        if len(row) != len(HEADER):
            raise ContractError("exact field count", row=line, token=row)
    df = pd.DataFrame(rows[1:], columns=HEADER)
    for field in RANGES:
        invalid = ~df[field].str.fullmatch(r"[0-9]+")
        if invalid.any():
            i = invalid[invalid].index[0]
            raise ContractError("nonnegative integer syntax", field, int(i) + 2, df.at[i, field])
        try:
            df[field] = df[field].astype("int64")
        except (ValueError, OverflowError) as exc:
            raise ContractError("int64 conversion", field) from exc
        low, high = RANGES[field]
        if ((df[field] < low) | ((df[field] > high) if high is not None else False)).any():
            raise ContractError("declared integer range", field)
    for field in FLOATS:
        try:
            df[field] = pd.to_numeric(df[field], errors="raise").astype("float64")
        except ValueError as exc:
            raise ContractError("numeric conversion", field) from exc
        if not (np.isfinite(df[field]) & df[field].between(0, 1)).all():
            raise ContractError("finite normalized range [0,1]", field)
    try:
        dates = pd.to_datetime(df.dteday, format="%Y-%m-%d", errors="raise")
    except ValueError as exc:
        raise ContractError("ISO calendar date", "dteday") from exc
    if dates.isna().any() or not dates.dt.strftime("%Y-%m-%d").eq(df.dteday).all():
        raise ContractError("exact ISO calendar date", "dteday")
    if not ((dates.dt.year == df.yr + 2011) & (dates.dt.month == df.mnth)).all():
        raise ContractError("date/year/month consistency")
    df["target_time"] = dates + pd.to_timedelta(df.hr, unit="h")
    df["weekday_mon0"] = dates.dt.dayofweek.astype("int64")
    df["record_id"] = SOURCE_SHA + ":" + df.instant.astype(str)
    if df.record_id.duplicated().any():
        raise ContractError("duplicate stable ID", "instant")
    if df.target_time.duplicated().any():
        raise ContractError("duplicate date-hour coordinate")
    if not df.cnt.eq(df.casual + df.registered).all():
        raise ContractError("cnt = casual + registered")
    return df.sort_values(["target_time", "instant"]).reset_index(drop=True)


def logical_hash(df):
    # Explicit canonical logical serialization, not a promise about parquet bytes.
    return sha(df.to_csv(index=False, lineterminator="\n", float_format="%.17g", date_format="%Y-%m-%dT%H:%M:%S").encode("utf-8"))


def audit(df):
    grid = pd.date_range(df.target_time.min(), df.target_time.max(), freq="h")
    missing = grid.difference(df.target_time)
    mapping = {str(int(k)): sorted(map(int, v.unique())) for k, v in df.groupby("weekday").weekday_mon0}
    return {"rows": len(df), "accepted": len(df), "rejected": 0, "start": str(df.target_time.min()), "end": str(df.target_time.max()), "duplicate_ids": int(df.record_id.duplicated().sum()), "duplicate_date_hours": int(df.target_time.duplicated().sum()), "missing_calendar_hours": len(missing), "gap_examples": list(map(str, missing[:8])), "source_weekday_to_mon0": mapping, "component_identity_all_rows": bool(df.cnt.eq(df.casual + df.registered).all()), "null_fields": int(df.isna().sum().sum()), "workingday_rule_matches": bool(df.workingday.eq((~df.weekday_mon0.isin([5, 6]) & df.holiday.eq(0)).astype(int)).all()), "logical_sha256": logical_hash(df), "source_sha256": SOURCE_SHA, "zip_sha256": ZIP_SHA, "schema_sha256": sha(encoded(SCHEMA)), "code_sha256": code_hash(), "versions": versions(), "scope": "Whole-source mechanical audit reads all cnt/casual/registered, including eventual reserved targets. No distribution filtering, imputation, scores, or gap filling."}
