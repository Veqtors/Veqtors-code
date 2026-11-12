import shutil
from pathlib import Path

import pytest

from break_it import run
from check_repo import check_ignored, check_no_env_tracked
from settings import get_password


def test_missing_or_placeholder_password_fails():
    with pytest.raises(RuntimeError):
        get_password({})
    with pytest.raises(RuntimeError, match="change-me"):
        get_password({"DB_PASSWORD": "change-me"})
    assert get_password({"DB_PASSWORD": "abc"}) == "abc"


def test_ignore_check_names_what_is_missing():
    ok, detail = check_ignored({".env": ".env", "data/x.csv": "data/"}, {"data/x.csv"})
    assert not ok and ".env" in detail
    assert check_ignored({".env": ".env"}, {".env"})[0]


def test_tracked_env_fails_anywhere_in_the_tree():
    assert check_no_env_tracked(["pyproject.toml", ".env.example"])[0]
    ok, detail = check_no_env_tracked(["config/.env"])
    assert not ok and "rm --cached" in detail


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_deleted_password_is_still_in_history(tmp_path: Path):
    found = run(tmp_path)
    assert len(found) == 2
    assert not (tmp_path / ".env").exists()
