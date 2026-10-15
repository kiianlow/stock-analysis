import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fundamentals as f  # noqa: E402
from avload import load_statement  # noqa: E402


def year(**over):
    base = dict(revenue=1000.0, cogs=400.0, gross_profit=600.0, operating_income=200.0, ebit=200.0,
                sga=150.0, net_income=150.0, net_income_cont=150.0, interest_expense=10.0,
                pretax_income=190.0, income_tax=40.0, da=50.0, total_assets=2000.0,
                current_assets=800.0, current_liabilities=400.0, total_liabilities=1000.0,
                equity=1000.0, retained_earnings=500.0, cash_sti=300.0, receivables=100.0,
                inventory=50.0, payables=80.0, ppe_net=600.0, goodwill=0.0, intangibles=0.0,
                lt_investments=0.0, total_debt=400.0, long_term_debt=350.0, shares=100.0,
                cfo=250.0, capex=60.0, dividends=20.0, buybacks=30.0)
    base.update(over)
    return base


def frame(rows):
    idx = pd.to_datetime([f"{2020 + i}-12-31" for i in range(len(rows))])
    return f.finish_canonical(pd.DataFrame(rows, index=idx, columns=f.CANONICAL, dtype=float))


def test_altman_hand_computed():
    row = frame([year()]).iloc[0]
    out = f.altman(row, market_cap=3000.0)
    a, b, c, d, e = 400 / 2000, 500 / 2000, 200 / 2000, 3000 / 1000, 1000 / 2000
    assert out["z"] == pytest.approx(1.2 * a + 1.4 * b + 3.3 * c + 0.6 * d + 1.0 * e)
    assert out["z_zone"] == "safe"
    assert out["z_double_prime"] == pytest.approx(6.56 * a + 3.26 * b + 6.72 * c + 1.05 * 1.0)


def test_beneish_neutral_company():
    # Two identical years with cash flow equal to income: every index is 1 and TATA is 0.
    df = frame([year(cfo=150.0), year(cfo=150.0)])
    out = f.beneish(df)
    assert out["m"] == pytest.approx(-4.84 + 0.920 + 0.528 + 0.404 + 0.892 + 0.115 - 0.172 - 0.327)
    assert out["m"] == pytest.approx(-2.48)
    assert out["flag"] is False


def test_piotroski_all_pass():
    y1 = year(total_assets=2000.0, net_income=100.0, long_term_debt=400.0, current_assets=700.0,
              shares=110.0, gross_profit=550.0, cogs=450.0, revenue=1000.0)
    y2 = year(total_assets=2000.0, net_income=110.0, long_term_debt=380.0, current_assets=750.0,
              shares=105.0, gross_profit=580.0, cogs=440.0, revenue=1020.0, cfo=200.0)
    y3 = year(total_assets=2000.0, net_income=140.0, long_term_debt=300.0, current_assets=800.0,
              shares=100.0, gross_profit=650.0, cogs=450.0, revenue=1100.0, cfo=220.0)
    out = f.piotroski(frame([y1, y2, y3]))
    assert out["score"] == 9 and out["out_of"] == 9


def test_yearly_metrics_roic_and_fcf():
    flags = []
    rows = f.yearly_metrics(frame([year()]), flags)
    r = rows[0]
    tax = 40 / 190
    assert r["nopat"] == pytest.approx(200 * (1 - tax))
    assert r["invested_capital"] == pytest.approx(1000 + 400 - 300)
    assert r["roic"] == pytest.approx(200 * (1 - tax) / 1100)
    assert r["fcf"] == pytest.approx(190.0)
    assert r["net_debt_to_ebitda"] == pytest.approx(100 / 250)
    assert r["interest_coverage"] == pytest.approx(20.0)
    assert r["dso"] == pytest.approx(36.5)
    assert flags == []


def test_bad_tax_rate_uses_21_percent():
    flags = []
    rows = f.yearly_metrics(frame([year(income_tax=-50.0)]), flags)
    assert rows[0]["tax_rate_used"] == 0.21
    assert flags


def test_stronger_vs_bigger_pass():
    flags = []
    ys = [year(), year(revenue=1200.0, gross_profit=780.0, cogs=420.0, operating_income=300.0, ebit=300.0,
                   cfo=360.0, shares=95.0, net_income=220.0)]
    rows = f.yearly_metrics(frame(ys), flags)
    sb = f.stronger_vs_bigger(rows)
    assert sb["table"]["gross_margin"] == "stronger"
    assert sb["table"]["operating_margin"] == "stronger"
    assert sb["table"]["share_count"] == "stronger"
    assert sb["verdict"] == "pass"


def test_alpha_vantage_statement_parsing(tmp_path):
    payload = {"symbol": "TEST", "annualReports": [
        {"fiscalDateEnding": "2025-12-31", "reportedCurrency": "USD", "totalRevenue": "1000",
         "grossProfit": "600", "costOfRevenue": "400", "operatingIncome": "None"}],
        "quarterlyReports": []}
    path = tmp_path / "income.json"
    path.write_text(json.dumps({"result": json.dumps(payload)}))
    annual, quarterly = load_statement(path)
    assert annual.loc["2025-12-31", "totalRevenue"] == 1000
    assert np.isnan(annual.loc["2025-12-31", "operatingIncome"])
    assert quarterly.empty


def test_validation_flags_unbalanced_sheet():
    flags = []
    f.validate(frame([year(total_liabilities=500.0)]), flags)
    assert any("liabilities + equity" in x for x in flags)
