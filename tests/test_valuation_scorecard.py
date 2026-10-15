import json
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import estimates  # noqa: E402
import scorecard  # noqa: E402
import valuation as v  # noqa: E402
from avload import AlphaVantageError, load_prices, read_payload  # noqa: E402

FRAMEWORK_EXAMPLE = {"valuation": 4, "growth": 4, "profitability": 5, "financial_strength": 4, "moat": 5,
                     "management": 4, "industry": 4, "earnings_quality": 4, "risk": 3, "technical": 3}


# ------------------------------------------------------------ valuation

def test_csp_framework_example():
    out = v.csp(200, 4, 30)
    assert out["breakeven"] == 196
    assert out["annualised_yield"] == pytest.approx(4 / 200 * 365 / 30)
    assert round(out["annualised_yield"] * 100, 1) == 24.3


def test_expected_return_framework_example():
    out = v.expected_return(0.04, 0.08, 25, 20, 5)
    assert out["multiple_change_per_year"] == pytest.approx((20 / 25) ** 0.2 - 1)
    assert round(out["expected_return"] * 100, 1) == 7.6


def test_dcf_equals_perpetuity_when_growth_constant():
    out = v.dcf(100, 0.03, 10, 0.09, 0.03, net_debt=0, shares=1)
    assert out["enterprise_value"] == pytest.approx(100 * 1.03 / 0.06)


def test_reverse_dcf_recovers_growth():
    price = v.dcf(50, 0.12, 10, 0.095, 0.03, net_debt=-20, shares=10)["per_share"]
    back = v.reverse_dcf(price, 50, 0.095, 0.03, net_debt=-20, shares=10)
    assert back["implied_growth"] == pytest.approx(0.12, abs=1e-6)


def test_scenarios_requires_probabilities_to_sum_to_one():
    with pytest.raises(ValueError):
        v.scenarios(100, [("bull", 150, 0.3), ("base", 110, 0.3), ("bear", 70, 0.3)])
    out = v.scenarios(100, [("bull", 150, 0.25), ("base", 120, 0.5), ("bear", 80, 0.25)])
    assert out["probability_weighted_value"] == pytest.approx(117.5)
    assert out["upside_downside_ratio"] == pytest.approx(1.0)


def test_cyclical_value_and_implied_eps():
    out = v.cyclical([100.0], norm_eps=10.0, multiple=10.0, discount=0.10, net_cash_per_share=5.0)
    assert out["pv_boom_fcf"] == pytest.approx(100 / 1.1)
    assert out["pv_franchise"] == pytest.approx(100 / 1.1)
    assert out["value_per_share"] == pytest.approx(200 / 1.1 + 5)
    implied = v.implied_normalised_eps(out["value_per_share"], [100.0], 10.0, 0.10, 5.0)
    assert implied == pytest.approx(10.0)
    assert v.normalised_eps(100.0, 0.25, 0.2, 10.0) == pytest.approx(2.0)


def test_wacc():
    assert v.capm(0.05, 1.2, 0.05) == pytest.approx(0.11)
    assert v.wacc(80, 20, 0.11, 0.06, 0.25) == pytest.approx(0.8 * 0.11 + 0.2 * 0.06 * 0.75)


# ------------------------------------------------------------ scorecard

def test_scorecard_framework_example_is_buy():
    out = scorecard.score(FRAMEWORK_EXAMPLE)
    assert out["total"] == 409 and out["final_rating"] == "Buy"


def test_scorecard_one_point_crosses_to_strong_buy():
    out = scorecard.score({**FRAMEWORK_EXAMPLE, "financial_strength": 5})
    assert out["total"] == 421 and out["final_rating"] == "Strong Buy"


def test_scorecard_overrides():
    assert scorecard.score({**FRAMEWORK_EXAMPLE, "valuation": 2})["final_rating"] == "Hold"
    assert scorecard.score(FRAMEWORK_EXAMPLE, kill_switch=True)["final_rating"] == "Sell"
    assert scorecard.score(FRAMEWORK_EXAMPLE, below_hurdle=True)["final_rating"] == "Hold"
    assert scorecard.score({**FRAMEWORK_EXAMPLE, "earnings_quality": 1})["final_rating"] == "Reduce"
    cheap_bad = {**FRAMEWORK_EXAMPLE, "valuation": 5, "moat": 2, "profitability": 2}
    assert scorecard.score(cheap_bad)["final_rating"] == "Hold"


def test_scorecard_boundaries():
    assert scorecard.raw_rating(420) == "Strong Buy"
    assert scorecard.raw_rating(419) == "Buy"
    assert scorecard.raw_rating(360) == "Buy"
    assert scorecard.raw_rating(359) == "Hold"
    assert scorecard.raw_rating(280) == "Hold"
    assert scorecard.raw_rating(220) == "Reduce"
    assert scorecard.raw_rating(219) == "Sell"


def test_scorecard_rejects_bad_input():
    with pytest.raises(ValueError):
        scorecard.score({**FRAMEWORK_EXAMPLE, "valuation": 6})
    with pytest.raises(ValueError):
        scorecard.score({k: v for k, v in FRAMEWORK_EXAMPLE.items() if k != "risk"})


# ------------------------------------------------------------ loaders and estimates

def test_loader_handles_saved_csv_wrapper(tmp_path):
    path = tmp_path / "weekly.txt"
    csv = "timestamp,open,high,low,close,volume\r\n2026-10-14,1,2,0.5,1.5,100\r\n2026-10-09,1,2,0.5,1.2,90\r\n"
    path.write_text(json.dumps({"result": csv}))
    df = load_prices(path)
    assert list(df.index.strftime("%Y-%m-%d")) == ["2026-10-09", "2026-10-14"]
    assert df["close"].iloc[-1] == 1.5


def test_loader_rejects_errors_and_previews(tmp_path):
    for body in ({"result": {"error": {"type": "rate_limit"}}},
                 {"result": {"preview": True, "sample_data": "x"}},
                 {"result": {"endpoint": "Realtime Options", "message": "This is a premium endpoint."}}):
        path = tmp_path / "x.json"
        path.write_text(json.dumps(body))
        with pytest.raises(AlphaVantageError):
            read_payload(path)


def test_estimates_flags_falling_next_year_eps():
    payload = {"estimates": [
        {"date": "2026-12-31", "horizon": "fiscal year", "eps_estimate_average": "20.63",
         "eps_estimate_average_90_days_ago": "14.23", "revenue_estimate_average": "498.7e9",
         "eps_estimate_analyst_count": "53"},
        {"date": "2027-12-31", "horizon": "fiscal year", "eps_estimate_average": "14.97",
         "revenue_estimate_average": "615.0e9", "eps_estimate_analyst_count": "53"}]}
    s = estimates.summarise(payload, price=347.64, today=date(2026, 10, 15))
    assert s["fiscal_years"][0]["forward_pe"] == round(347.64 / 20.63, 2)
    assert s["next_year_eps_growth_pct"] == round((14.97 / 20.63 - 1) * 100, 2)
    assert len(s["flags"]) == 2
