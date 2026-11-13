"""DE-04: load DE-01's ten rows into Postgres and count them.

    docker compose up -d
    uv run python check_db.py          # create the table, load the rows, count them
    uv run python check_db.py --count  # only count (use it after a restart)
"""
import os
import sys
import time

import psycopg
from dotenv import load_dotenv

from rows import ROWS, conninfo


def connect(info: str, wait_seconds: int = 30):
    """Retry while the database finishes starting; fail with a clear message."""
    deadline = time.time() + wait_seconds
    while True:
        try:
            return psycopg.connect(info, connect_timeout=3)
        except psycopg.OperationalError as error:
            if time.time() > deadline:
                raise RuntimeError(f"Could not reach Postgres: {error}") from error
            time.sleep(1)


def main(argv) -> int:
    load_dotenv()
    try:
        conn = connect(conninfo(os.environ))
    except RuntimeError as error:
        print(f"[FAIL] {error}")
        return 1
    with conn, conn.cursor() as cur:
        if "--count" not in argv:
            cur.execute("drop table if exists order_lines")
            cur.execute(
                "create table order_lines (invoice text, stock_code text, description text,"
                " quantity int, invoice_date timestamp, price numeric(10,2), customer_id int)"
            )
            cur.executemany("insert into order_lines values (%s,%s,%s,%s,%s,%s,%s)", ROWS)
        try:
            cur.execute("select count(*) from order_lines")
        except psycopg.errors.UndefinedTable:
            print("[FAIL] order_lines does not exist. Run without --count first.")
            return 1
        count = cur.fetchone()[0]
    print(f"[ok] order_lines has {count} rows" if count == len(ROWS) else f"[FAIL] expected {len(ROWS)} rows, found {count}")
    return 0 if count == len(ROWS) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
