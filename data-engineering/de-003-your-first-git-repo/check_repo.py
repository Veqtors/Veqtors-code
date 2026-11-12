"""DE-03: check that a project folder keeps secrets and data out of Git.

Run it inside your lab (the folder with .git):

    uv run python check_repo.py

Each check prints ok or FAIL with the fix. Exit code 0 means all passed.
"""
import subprocess
import sys

# a sample path inside each thing that must stay out, and the name to show
MUST_IGNORE = {".venv/pyvenv.cfg": ".venv/", "data/example.csv": "data/", ".env": ".env"}


def git_lines(*args: str) -> list[str]:
    result = subprocess.run(["git", *args], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git failed")
    return result.stdout.splitlines()


def check_ignored(paths, ignored) -> tuple[bool, str]:
    missing = [paths[p] for p in paths if p not in ignored]
    if missing:
        return False, f"not ignored: {', '.join(missing)} (add them to .gitignore)"
    return True, ".venv, data/ and .env are all ignored"


def check_no_env_tracked(tracked) -> tuple[bool, str]:
    leaked = [p for p in tracked if p.split("/")[-1] == ".env"]
    if leaked:
        return False, (f"tracked: {', '.join(leaked)} (run git rm --cached on it, "
                       "and change that password: treat it as leaked)")
    return True, "no .env file is tracked"


def main() -> int:
    try:
        git_lines("rev-parse", "--git-dir")
    except (RuntimeError, FileNotFoundError):
        print("[FAIL] this folder is not a Git repository (run: git init)")
        return 1
    # --no-index: test the rules even for paths that don't exist yet
    ignored = set(subprocess.run(["git", "check-ignore", "--no-index", *MUST_IGNORE],
                                 capture_output=True, text=True).stdout.splitlines())
    checks = [
        ("gitignore", check_ignored(MUST_IGNORE, ignored)),
        ("secrets", check_no_env_tracked(git_lines("ls-files"))),
    ]
    for name, (ok, detail) in checks:
        print(f"[{'ok' if ok else 'FAIL'}] {name}: {detail}")
    return 0 if all(ok for _, (ok, _) in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
