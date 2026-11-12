"""DE-02: check that your data-engineering lab works.

Run it from the DE-01 project folder (the one with pyproject.toml):

    uv run python lab_check.py

Four checks, each printed as ok or FAIL with the reason. It uses only the
Python standard library, so it runs even before you have installed anything.
Exit code 0 means every check passed.
"""
import importlib.metadata as metadata
import re
import subprocess
import sys

MIN_PYTHON = (3, 11)
PACKAGES = ["pandas", "pyarrow", "openpyxl", "pytest"]


def check_python(version_info) -> tuple[bool, str]:
    found = f"{version_info[0]}.{version_info[1]}"
    needed = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
    ok = tuple(version_info[:2]) >= MIN_PYTHON
    return ok, f"Python {found} (needs {needed} or newer)"


def check_virtual_environment(prefix: str, base_prefix: str) -> tuple[bool, str]:
    if prefix != base_prefix:
        return True, f"running inside a virtual environment: {prefix}"
    return False, "not inside a virtual environment: sys.prefix is the system Python (start it with: uv run python lab_check.py)"


def check_packages(names, version_of) -> tuple[bool, str]:
    found, missing = [], []
    for name in names:
        try:
            found.append(f"{name} {version_of(name)}")
        except metadata.PackageNotFoundError:
            missing.append(name)
    if missing:
        return False, "missing: " + ", ".join(missing) + " (run: uv sync)"
    return True, ", ".join(found)


def check_tests(returncode: int, output: str) -> tuple[bool, str]:
    summary = [line for line in output.splitlines() if re.search(r"\d+ (passed|failed|error)", line)]
    shown = summary[-1].strip("= ").strip() if summary else "no test summary found"
    return returncode == 0, f"pytest: {shown}"


def run_pytest() -> tuple[int, str]:
    result = subprocess.run([sys.executable, "-m", "pytest", "-q"], capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def main() -> int:
    code, output = run_pytest()
    checks = [
        ("python", *check_python(sys.version_info)),
        ("environment", *check_virtual_environment(sys.prefix, sys.base_prefix)),
        ("packages", *check_packages(PACKAGES, metadata.version)),
        ("tests", *check_tests(code, output)),
    ]
    for name, ok, detail in checks:
        print(f"[{'ok' if ok else 'FAIL'}] {name}: {detail}")
    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
