"""Run every calculator on one ticker's data folder.

Usage:
    python scripts/analyze.py data/GOOGL/2026-10-15 --rf 0.0521

The folder holds files named by stem, any extension:
    daily, weekly, overview, income, balance, cashflow, estimates, insiders, manual

Writes summary.json and summary.md into the folder and prints the markdown.
Missing files are skipped and listed as data gaps.
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estimates as est  # noqa: E402
import fundamentals as fun  # noqa: E402
import insiders as ins  # noqa: E402
import technicals as tech  # noqa: E402
from avload import find_file, load_indicator, load_json, load_overview, load_prices, load_statement  # noqa: E402

STEMS = ("daily", "weekly", "sma200", "overview", "meta", "income", "balance", "cashflow",
         "estimates", "insiders", "manual")


def run(folder, rf=None, ticker=None):
    folder = Path(folder)
    files = {stem: find_file(folder, stem) for stem in STEMS}
    summary, sections, gaps, errors = {}, [], [], []
    overview = {}
    if files["overview"]:
        try:
            overview = load_overview(files["overview"])
        except Exception as exc:  # noqa: BLE001
            errors.append(f"overview: {exc}")
    for stem in ("meta", "manual"):
        if files[stem]:
            meta = json.loads(Path(files[stem]).read_text())
            defaults = {"Name": meta.get("company"), "Symbol": meta.get("ticker"), "Currency": meta.get("currency"),
                        "Sector": meta.get("sector"), "Industry": meta.get("industry"),
                        "MarketCapitalization": meta.get("market_cap")}
            overview = {**{k: v for k, v in defaults.items() if v is not None}, **overview}
    ticker = ticker or overview.get("Symbol") or folder.parent.name

    price = None
    sma200 = overview.get("200DayMovingAverage")
    if files["sma200"]:
        try:
            sma200 = float(load_indicator(files["sma200"]).iloc[-1, 0])
        except Exception as exc:  # noqa: BLE001
            errors.append(f"sma200: {exc}")
    if files["daily"]:
        try:
            daily = load_prices(files["daily"])
            weekly = load_prices(files["weekly"]) if files["weekly"] else None
            t = tech.analyse(daily, weekly, sma200)
            summary["technicals"], price = t, t["price"]
            sections.append(tech.summary_markdown(t))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"technicals: {exc}")
            traceback.print_exc()
    else:
        gaps.append("daily prices (technicals, support zones)")

    try:
        if files["manual"]:
            annual, quarterly, meta = fun.canonical_from_manual(files["manual"])
            price = price or meta.get("price")
        elif files["income"] and files["balance"] and files["cashflow"]:
            inc_a, inc_q = load_statement(files["income"])
            bal_a, bal_q = load_statement(files["balance"])
            cf_a, cf_q = load_statement(files["cashflow"])
            annual = fun.canonical_from_av({"income": inc_a, "balance": bal_a, "cash": cf_a})
            quarterly = fun.canonical_from_av({"income": inc_q, "balance": bal_q, "cash": cf_q})
        else:
            annual = None
            gaps.append("financial statements (Gates 3 to 6, valuation snapshot)")
        if annual is not None:
            f = fun.analyse(annual, quarterly, overview, price)
            summary["fundamentals"] = f
            sections.append(fun.summary_markdown(f))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"fundamentals: {exc}")
        traceback.print_exc()

    if files["estimates"]:
        try:
            e = est.summarise(load_json(files["estimates"]), price)
            summary["estimates"] = e
            sections.append(est.summary_markdown(e))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"estimates: {exc}")
    else:
        gaps.append("consensus estimates (forward P/E, revisions)")

    if files["insiders"]:
        try:
            i = ins.summarise(load_json(files["insiders"]), ticker)
            summary["insiders"] = i
            sections.append(ins.summary_markdown(i))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"insiders: {exc}")
    else:
        gaps.append("insider transactions")

    if rf is not None:
        summary["risk_free_10y"] = rf
        vs = (summary.get("fundamentals") or {}).get("valuation_snapshot") or {}
        lines = [f"US 10-year yield used as risk-free: {rf * 100:.2f}%"]
        if vs.get("fcf_yield_ttm") is not None:
            lines.append(f"- FCF yield minus 10-year: {(vs['fcf_yield_ttm'] - rf) * 100:+.2f} points")
        if vs.get("earnings_yield_ebit_ev") is not None:
            lines.append(f"- EBIT/EV minus 10-year: {(vs['earnings_yield_ebit_ev'] - rf) * 100:+.2f} points")
        sections.append("\n".join(lines))

    summary["data_gaps"], summary["errors"] = gaps, errors
    tail = []
    if gaps:
        tail.append("Data gaps: " + "; ".join(gaps))
    if errors:
        tail.append("Errors: " + "; ".join(errors))
    if tail:
        sections.append("\n".join(tail))
    md = f"# {ticker} calculator output\n\n" + "\n\n".join(sections) + "\n"
    (folder / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    (folder / "summary.md").write_text(md)
    return md


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--rf", type=float, help="US 10-year yield as a decimal, for example 0.0521")
    ap.add_argument("--ticker")
    a = ap.parse_args()
    print(run(a.folder, a.rf, a.ticker))


if __name__ == "__main__":
    main()
