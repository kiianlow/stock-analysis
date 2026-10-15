import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import analyze  # noqa: E402
import fundamentals as f  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def test_blank_manual_template_does_not_crash():
    annual, quarterly, meta = f.canonical_from_manual(ROOT / "templates" / "financials-manual.json")
    out = f.analyse(annual, quarterly, {"Sector": meta["sector"], "Industry": meta["industry"]})
    assert out["years"] == []
    assert any("No annual statements" in x for x in out["flags"])


def test_manual_path_end_to_end(tmp_path):
    year = {"revenue": 1000, "cogs": 400, "gross_profit": 600, "operating_income": 200, "net_income": 150,
            "pretax_income": 190, "income_tax": 40, "da": 50, "total_assets": 2000, "current_assets": 800,
            "current_liabilities": 400, "total_liabilities": 1000, "equity": 1000, "retained_earnings": 500,
            "cash_sti": 300, "total_debt": 400, "long_term_debt": 350, "shares": 100, "cfo": 250, "capex": 60}
    manual = {"ticker": "TEST.SI", "company": "Test", "currency": "SGD", "sector": "Industrials",
              "industry": "Machinery", "price": 30.0, "market_cap": 3000,
              "years": {"2024-12-31": year, "2025-12-31": {**year, "revenue": 1100, "gross_profit": 680, "cogs": 420}}}
    (tmp_path / "manual.json").write_text(json.dumps(manual))
    md = analyze.run(tmp_path)
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["fundamentals"]["years"][-1]["revenue_growth"] == 0.1
    assert "altman" in summary["fundamentals"]
    assert "daily prices" in " ".join(summary["data_gaps"])
    assert "TEST" in md
