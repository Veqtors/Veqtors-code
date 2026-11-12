# DE-03 results (measured 2026-11-12, Windows 11, git 2.55.0.windows.5, uv 0.10.0)

Locked versions: python-dotenv 1.2.4, pytest 9.2.0, Python 3.13.

## `uv run pytest`

```
4 passed in 0.40s
```

## `uv run python break_it.py`

```
files in the folder now: app.py
lines in git log -p that still hold the password: 2
  -DB_PASSWORD=not-a-real-password
  +DB_PASSWORD=not-a-real-password
```

## `uv run python check_repo.py`

In the lab, after writing `.gitignore` first (exit code 0):

```
[ok] gitignore: .venv, data/ and .env are all ignored
[ok] secrets: no .env file is tracked
```

In a new repo with no `.gitignore` (exit code 1):

```
[FAIL] gitignore: not ignored: .venv/, data/, .env (add them to .gitignore)
[ok] secrets: no .env file is tracked
```

In a repo where `.env` was committed before the `.gitignore` was written (exit code 1):

```
[ok] gitignore: .venv, data/ and .env are all ignored
[FAIL] secrets: tracked: .env (run git rm --cached on it, and change that password: treat it as leaked)
```

Outside a repo: `[FAIL] this folder is not a Git repository (run: git init)` (exit code 1).

## `uv run python settings.py`

| `.env` | Output |
|---|---|
| missing | `[FAIL] DB_PASSWORD is not set. Copy .env.example to .env and fill it in.` |
| copied from `.env.example` | `[FAIL] DB_PASSWORD still says change-me. Put your own value in .env.` |
| `DB_PASSWORD=not-a-real-password` | `[ok] DB_PASSWORD loaded (19 characters, not printed)` |

Raw command runs for the issue (`git cat-file`, `uv init`, `.venv/.gitignore`, branch and merge) are in the issue's `evidence.md`.

Not measured: macOS, Linux, the push to GitHub.
