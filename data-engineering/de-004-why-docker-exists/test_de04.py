import pytest

from rows import ROWS, conninfo


def test_ten_rows():
    assert len(ROWS) == 10


def test_conninfo_uses_defaults_and_port():
    assert conninfo({"DB_PASSWORD": "x"}).startswith("host=127.0.0.1 port=5432 ")
    assert "port=55432" in conninfo({"DB_PASSWORD": "x", "DB_PORT": "55432"})


@pytest.mark.parametrize("env", [{}, {"DB_PASSWORD": ""}, {"DB_PASSWORD": "change-me"}])
def test_missing_password_fails(env):
    with pytest.raises(RuntimeError):
        conninfo(env)


def test_bad_port_fails():
    with pytest.raises(RuntimeError):
        conninfo({"DB_PASSWORD": "x", "DB_PORT": "abc"})
