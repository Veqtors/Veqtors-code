import importlib.metadata as metadata

from lab_check import check_packages, check_python, check_tests, check_virtual_environment


def test_old_python_fails_and_new_passes():
    assert check_python((3, 14, 0))[0]
    assert check_python((3, 11, 0))[0]
    ok, detail = check_python((3, 9, 7))
    assert not ok and "3.9" in detail


def test_virtual_environment_is_detected_by_prefix():
    assert check_virtual_environment("C:/lab/.venv", "C:/Python314")[0]
    assert not check_virtual_environment("C:/Python314", "C:/Python314")[0]


def test_missing_package_is_named_with_the_fix():
    def version_of(name):
        if name == "pandas":
            return "3.1.1"
        raise metadata.PackageNotFoundError(name)

    ok, detail = check_packages(["pandas", "pyarrow"], version_of)
    assert not ok
    assert "pyarrow" in detail and "python -m pip install -r requirements.txt" in detail


def test_all_packages_present():
    ok, detail = check_packages(["a", "b"], lambda name: "1.0")
    assert ok and detail == "a 1.0, b 1.0"


def test_tests_check_reads_exit_code_and_last_line():
    assert check_tests(0, "..\n2 passed in 0.4s\n") == (True, "pytest: 2 passed in 0.4s")
    ok, detail = check_tests(1, "")
    assert not ok and "no test summary" in detail


def test_tests_check_ignores_warning_lines_after_the_summary():
    output = "====== 2 passed in 1.59s ======\n  from pydantic.v1 import (\n"
    assert check_tests(0, output) == (True, "pytest: 2 passed in 1.59s")
