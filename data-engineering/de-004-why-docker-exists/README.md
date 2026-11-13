# DE-04: Postgres in Docker, once

One Compose file, one script. The password is fake in every example.

- `compose.yaml` starts Postgres 18 on `127.0.0.1`, keeps its data in a named volume, and reads the password from `.env`.
- `check_db.py` loads DE-01's ten rows into a table and counts them. `--count` only counts.
- `rows.py` holds the ten rows and builds the connection string.

## Use it

You need Docker Desktop (Windows, macOS) or Docker Engine (Linux), running, and uv (see DE-02). From this folder:

```
cp .env.example .env        # then edit .env: DB_PASSWORD=not-a-real-password
docker compose up -d
uv sync
uv run python check_db.py
```

Expected: `[ok] order_lines has 10 rows`.

Keep the data across a restart, or wipe it:

```
docker compose down         # container gone, volume kept
docker compose up -d
uv run python check_db.py --count   # still 10 rows
docker compose down -v      # container AND volume gone
```

Tests that need no Docker: `uv run pytest`.

## When it breaks

- `cannot connect to the Docker daemon`: start Docker Desktop and wait until it says it is running.
- `port is already allocated`: something already uses 5432. Put `DB_PORT=5433` in `.env`; both Compose and `check_db.py` read it.
- `required variable DB_PASSWORD is missing`: you have no `.env`. Copy `.env.example`.
- The container exits at once: `docker compose logs db`.
- Windows: Docker Desktop needs WSL 2 (the default) or Hyper-V, and a restart after the first install.
