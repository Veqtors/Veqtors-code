# DE-03: your first Git repo, without the password

Three small scripts. Every password in them is fake.

- `break_it.py` makes a throwaway repo in a temp folder. It commits a `.env` holding `DB_PASSWORD=not-a-real-password`, deletes it, commits again, and prints what `git log -p` still finds. Then it deletes the temp folder and leaves your files untouched.
- `check_repo.py` runs inside your lab. It checks that `.gitignore` keeps out `.venv/`, `data/` and `.env`, and that no `.env` file is tracked.
- `settings.py` reads `DB_PASSWORD` from `.env` with python-dotenv. It never prints the value.

`.gitignore` and `.env.example` are the two files to copy into your own lab.

## Use it

You need Git ([download](https://git-scm.com/downloads)) and uv (see DE-02). From this folder:

```
uv sync
uv run python break_it.py
```

Copy `check_repo.py`, `.gitignore` and `.env.example` into your lab (the folder you ran `git init` in), then from there:

```
uv run python check_repo.py
```

For `settings.py`, copy `.env.example` to `.env` and replace `change-me` with your own value. `.env` is in `.gitignore`, so Git never sees it.

## When it breaks

- **`git` is not recognized:** install Git, then open a new terminal.
- **`Author identity unknown` on your first commit:** run `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"`.
- **`check_repo.py` says `.env` is tracked:** run `git rm --cached .env` and commit. Then **change that password**. It is in your history now, so treat it as leaked.

## Tests

```
uv run pytest
```

`test_de03.py` has four tests. The last one runs the real break-it in a temp folder and is skipped if Git is not installed.
