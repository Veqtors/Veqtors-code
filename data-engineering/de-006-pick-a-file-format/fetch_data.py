"""DE-05: download UCI's Online Retail II file into data/ and check it is whole.

    uv run python fetch_data.py

The server answers a Range request with the whole file, so an interrupted
download cannot be resumed: a failed attempt starts again from byte 0.
data/ is in .gitignore; the file is never committed.
"""
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
DATA = Path("data")
ZIP_NAME = "online-retail-ii.zip"
XLSX_NAME = "online_retail_II.xlsx"
ATTEMPTS = 3


def check_zip(path: Path) -> str | None:
    """Return None if the zip is whole, otherwise a plain-language reason."""
    if not zipfile.is_zipfile(path):
        return "not a zip file (the download is probably cut off)"
    try:
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
    except zipfile.BadZipFile as error:
        return f"damaged zip: {error}"
    return f"member {bad} failed its CRC check" if bad else None


def download(url: str, target: Path, chunk: int = 1 << 16) -> int:
    done, shown = 0, 0
    with urllib.request.urlopen(url, timeout=60) as response, open(target, "wb") as out:
        while block := response.read(chunk):
            out.write(block)
            done += len(block)
            if done - shown >= 5_000_000:
                print(f"  {done / 1e6:.1f} MB so far")
                shown = done
    return done


def main() -> int:
    DATA.mkdir(exist_ok=True)
    xlsx = DATA / XLSX_NAME
    if xlsx.exists():
        print(f"[ok] {xlsx} is already here ({xlsx.stat().st_size:,} bytes)")
        return 0
    target = DATA / ZIP_NAME
    for attempt in range(1, ATTEMPTS + 1):
        print(f"Attempt {attempt} of {ATTEMPTS}: downloading from byte 0 (the server is slow; this can take an hour)")
        started = time.time()
        try:
            size = download(URL, target)
        except OSError as error:
            print(f"  download stopped: {error}")
            continue
        reason = check_zip(target)
        if reason is None:
            print(f"  downloaded {size:,} bytes in {time.time() - started:.0f} s, zip check passed")
            break
        print(f"  {reason}")
    else:
        print("[FAIL] no complete download. Delete data/ and try again, or download the zip in a browser.")
        return 1
    with zipfile.ZipFile(target) as archive:
        archive.extract(XLSX_NAME, DATA)
    print(f"[ok] {xlsx} ({xlsx.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
