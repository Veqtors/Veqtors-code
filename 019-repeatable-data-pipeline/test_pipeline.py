import pytest
from dataset import ContractError, HEADER, parse


def fixture():
    return (",".join(HEADER) + "\n1,2011-01-01,1,0,1,0,0,6,0,1,0.2,0.3,0.4,0.1,2,3,5\n").encode()


@pytest.mark.parametrize("old,new,rule", [("cnt\n", "missing\n", "header"), (",0,0,6,", ",oops,0,6,", "integer syntax"), (",2,3,5", ",2,3,6", "cnt ="), ("2011-01-01", "2011-02-30", "date"), (",0.2,", ",NaN,", "numeric conversion"), (",0.2,", ",1.2,", "range"), (",0,0,6,", ",24,0,6,", "range")])
def test_rejects_contract_faults(old, new, rule):
    with pytest.raises(ContractError, match=rule):
        parse(fixture().replace(old.encode(), new.encode()))


def test_identity_calendar_and_duplicates():
    raw = fixture()
    df = parse(raw)
    assert df.weekday_mon0.iloc[0] == 5
    assert df.record_id.iloc[0].endswith(":1")
    with pytest.raises(ContractError, match="duplicate stable ID"):
        parse(raw + raw.splitlines()[1] + b"\n")


@pytest.mark.parametrize("suffix", [b",extra", b""])
def test_field_count(suffix):
    lines = fixture().splitlines()
    row = lines[1] + suffix if suffix else lines[1].rsplit(b",", 1)[0]
    with pytest.raises(ContractError, match="field count"):
        parse(lines[0] + b"\n" + row)
