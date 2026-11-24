from common import SLICE, NEEDED, load, top_five


def test_hand_slice():
    df = load(NEEDED)
    ten = df.loc[SLICE[0]:SLICE[1]]
    uk = ten[ten["Country"] == "United Kingdom"]
    assert len(ten) == 10 and len(uk) == 7
    top = top_five(uk)
    assert top["StockCode"].tolist() == ["21756", "21135", "22694", "20763", "22311"]
    assert round(top["revenue"].iloc[0], 2) == 41.65
