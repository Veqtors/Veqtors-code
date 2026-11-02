"""Run exact rerun and deliberately injected fault experiments."""
import argparse
import time
from pathlib import Path

import pandas as pd
from dataset import ContractError, audit, code_hash, parse, sha, source_bytes, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", help="Existing official ZIP; exact archive/member hashes still checked")
    args = parser.parse_args()
    root = Path(__file__).parent
    started = time.perf_counter()
    raw = source_bytes(root / "data", args.archive)
    a, b = parse(raw), parse(raw)
    pd.testing.assert_frame_equal(a, b, check_exact=True)
    a.to_parquet(root / "data/canonical.parquet", index=False)
    b.to_parquet(root / "data/rerun.parquet", index=False)
    pd.testing.assert_frame_equal(a, pd.read_parquet(root / "data/canonical.parquet"), check_exact=True)
    lines = raw.decode().splitlines()
    missing = "\n".join(",".join(row.split(",")[:-1]) for row in lines).encode()
    bad = lines.copy()
    row = bad[1].split(","); row[5] = "not-an-hour"; bad[1] = ",".join(row)
    duplicate = lines + [lines[1]]
    faults = {}
    for name, payload in {"missing_column": missing, "bad_numeric": "\n".join(bad).encode(), "duplicate_id": "\n".join(duplicate).encode()}.items():
        try:
            parse(payload)
        except ContractError as exc:
            faults[name] = {"injected": True, "fixture_sha256": sha(payload), "source_sha256": sha(raw), "error": exc.detail, "batch_accepted": 0, "success_output_written": False}
        else:
            raise AssertionError(f"fault escaped: {name}")
    report = audit(a)
    report.update({"exact_rerun": True, "lossless_parquet_readback": True, "parquet_bytes_equal": (root / "data/canonical.parquet").read_bytes() == (root / "data/rerun.parquet").read_bytes(), "parquet_sha256": sha((root / "data/canonical.parquet").read_bytes()), "faults": faults, "elapsed_seconds": time.perf_counter() - started, "code_sha256": code_hash()})
    write_json(root / "audit.json", report)
    print(report)


if __name__ == "__main__":
    main()
