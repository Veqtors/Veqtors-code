"""DE-03: commit a fake password, delete it, and see that Git still has it.

    uv run python break_it.py

Everything happens in a new temporary folder that is deleted at the end.
The password is fake: not-a-real-password. Your own project is not touched.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FAKE = "DB_PASSWORD=not-a-real-password"


def git(folder: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "user.name=Lab Reader", "-c", "user.email=reader@example.com",
         "-c", "core.autocrlf=false", *args],
        cwd=folder, capture_output=True, text=True, check=True,
    )
    return result.stdout


def run(folder: Path) -> list[str]:
    """Commit .env, delete it, commit again; return the history lines that still hold it."""
    git(folder, "init", "-q")
    (folder / "app.py").write_text("print('hello')\n")
    git(folder, "add", "app.py")
    git(folder, "commit", "-q", "-m", "Add app")
    (folder / ".env").write_text(FAKE + "\n")
    git(folder, "add", ".env")
    git(folder, "commit", "-q", "-m", "Add settings")
    git(folder, "rm", "-q", ".env")
    git(folder, "commit", "-q", "-m", "Remove .env")
    return [line for line in git(folder, "log", "-p").splitlines() if "not-a-real-password" in line]


def main() -> int:
    if shutil.which("git") is None:
        print("[FAIL] git is not installed (or not on PATH). Install Git, open a new terminal, try again.")
        return 1
    folder = Path(tempfile.mkdtemp(prefix="break-it-"))
    try:
        found = run(folder)
        files = sorted(p.name for p in folder.iterdir() if p.name != ".git")
        print(f"files in the folder now: {', '.join(files)}")
        print(f"lines in git log -p that still hold the password: {len(found)}")
        for line in found:
            print(f"  {line}")
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
