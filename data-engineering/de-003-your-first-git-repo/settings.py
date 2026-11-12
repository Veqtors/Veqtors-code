"""DE-03: read the database password from .env instead of from your code.

Copy .env.example to .env, put your value in it, then:

    uv run python settings.py

.env stays on your machine: .gitignore keeps it out of Git.
A value already set in your terminal wins over the one in .env.
"""
import os
import sys

from dotenv import load_dotenv


def get_password(environ) -> str:
    value = environ.get("DB_PASSWORD", "")
    if not value:
        raise RuntimeError("DB_PASSWORD is not set. Copy .env.example to .env and fill it in.")
    if value == "change-me":
        raise RuntimeError("DB_PASSWORD still says change-me. Put your own value in .env.")
    return value


def main() -> int:
    load_dotenv()
    try:
        password = get_password(os.environ)
    except RuntimeError as error:
        print(f"[FAIL] {error}")
        return 1
    print(f"[ok] DB_PASSWORD loaded ({len(password)} characters, not printed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
