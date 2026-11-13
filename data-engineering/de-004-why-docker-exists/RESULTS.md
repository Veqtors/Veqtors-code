# DE-04 results (measured 2026-11-13)

Windows 11, Docker Desktop, Docker 28.5.1 (client and server), image `postgres:18` = PostgreSQL 18.7. Fake password `not-a-real-password`. Full log: `../evidence.md`.

- `uv run pytest -q`: 6 passed.
- `docker compose up -d` without `.env`: stops with `required variable DB_PASSWORD is missing a value`.
- `docker compose up -d`, then `uv run python check_db.py`: `[ok] order_lines has 10 rows`.
- `docker compose down`, `up -d`, `check_db.py --count`: `[ok] order_lines has 10 rows` (volume kept).
- `docker compose down -v`, `up -d`, `check_db.py --count`: `[FAIL] order_lines does not exist` (volume deleted).
- `docker compose ps`: `127.0.0.1:55432->5432/tcp` (the test used `DB_PORT=55432` because the machine already had databases on 5432).
- Start time with the image already pulled: 1.93 s on a fresh volume, 1.29 s on restart.
