"""Write DE-01's ten rows three ways and count characters. No download needed."""
import json
import sys

from sample_rows import sample_frame


def as_csv(df) -> str:
    return df.to_csv(index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S")


def as_jsonl(df) -> str:
    # default=str turns Timestamps into text; NaN becomes null via the None swap
    rows = df.astype(object).where(df.notna(), None).to_dict("records")
    return "".join(json.dumps(r, default=str) + "\n" for r in rows)


def as_columns(df) -> str:
    """Each column written whole, one line per column (a picture of a column layout, not Parquet)."""
    return "".join(f"{c}: {df[c].tolist()}\n" for c in df.columns)


def as_collapsed(df) -> str:
    """Each column written whole, with runs of equal neighbours collapsed to 'value xN'."""
    out = []
    for c in df.columns:
        runs, prev = [], object()
        for v in df[c].tolist():
            key = "blank" if v != v or v is None else str(v)
            if runs and key == prev:
                runs[-1][1] += 1
            else:
                runs.append([key, 1])
            prev = key
        out.append(f"{c}: " + ", ".join(k if n == 1 else f"{k} x{n}" for k, n in runs) + "\n")
    return "".join(out)


def main() -> None:
    df = sample_frame()
    if "--show" in sys.argv:  # print the layouts themselves, as shown in the issue
        print(as_csv(df), *as_jsonl(df).splitlines()[:2], as_collapsed(df), sep="\n")
    for name, text in (("CSV", as_csv(df)), ("JSON lines", as_jsonl(df)), ("columns written out", as_columns(df)), ("columns, runs collapsed", as_collapsed(df))):
        print(f"{name}: {len(text)} characters")
    key_chars = sum(len(json.dumps(c)) + 1 for c in df.columns) * len(df)  # '"Invoice":' x 10 rows
    print(f"JSON lines repeats the eight key names {len(df)} times = {key_chars} characters")


if __name__ == "__main__":
    main()
