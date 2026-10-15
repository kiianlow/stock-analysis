import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import insiders  # noqa: E402

TODAY = date(2026, 10, 15)


def row(d, who, code, shares, price, sec="Class A Common Stock"):
    return {"transaction_date": d, "ticker": "TEST", "executive": who, "executive_title": "Officer",
            "security_type": sec, "acquisition_or_disposal": code, "shares": str(shares), "share_price": str(price)}


def test_sec_codes_count_only_purchases_and_sales():
    data = {"data": [
        row("2026-09-01", "DOE, JANE", "P", 100, 50),
        row("2026-09-02", "DOE, JANE", "S", 10, 55),
        row("2026-09-03", "ROE, RICK", "A", 500, 0),        # grant, not a buy
        row("2026-09-04", "ROE, RICK", "F", 50, 52),        # tax withholding, not a sale
        row("2026-09-05", "ROE, RICK", "S", 20, 60, sec="Class C Stock Units"),  # units excluded
        row("2027-01-25", "DOE, JANE", "S", 99, 99),        # future date dropped
        row("2026-09-06", "BIG FUND GP, L.L.C.", "S", 1000, 50),
    ]}
    s = insiders.summarise(data, "TEST", 12, TODAY)
    assert s["code_style"] == "SEC Form 4 codes"
    assert s["individual_buys"]["count"] == 1 and s["individual_buys"]["value"] == 5000
    assert s["individual_sells"]["count"] == 1 and s["individual_sells"]["value"] == 550
    assert s["entity_sells_value"] == 50000
    assert s["future_dated_rows_dropped"] == 1
    assert s["other_codes_count"] == {"A": 1, "F": 1}


def test_ad_flags_style():
    data = {"data": [row("2026-09-01", "DOE, JANE", "A", 100, 50), row("2026-09-02", "DOE, JANE", "A", 100, 0),
                     row("2026-09-03", "DOE, JANE", "D", 10, 55)]}
    s = insiders.summarise(data, "TEST", 12, TODAY)
    assert s["code_style"] == "A/D flags"
    assert s["individual_buys"]["count"] == 1
    assert s["individual_sells"]["count"] == 1
