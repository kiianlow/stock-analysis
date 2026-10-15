"""Consensus estimates and revision trend from Alpha Vantage EARNINGS_ESTIMATES.

Usage:
    python scripts/estimates.py --file estimates.json --price 347.64 [--today 2026-10-15]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from avload import load_json  # noqa: E402


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _chg(now, then):
    if now is None or then in (None, 0):
        return None
    return round((now / then - 1) * 100, 2)


def _row(r, price):
    avg = _f(r.get("eps_estimate_average"))
    out = {
        "period_end": r["date"], "horizon": r["horizon"],
        "eps_avg": avg, "eps_high": _f(r.get("eps_estimate_high")), "eps_low": _f(r.get("eps_estimate_low")),
        "analysts": _f(r.get("eps_estimate_analyst_count")),
        "revenue_avg": _f(r.get("revenue_estimate_average")),
        "eps_change_7d_pct": _chg(avg, _f(r.get("eps_estimate_average_7_days_ago"))),
        "eps_change_30d_pct": _chg(avg, _f(r.get("eps_estimate_average_30_days_ago"))),
        "eps_change_60d_pct": _chg(avg, _f(r.get("eps_estimate_average_60_days_ago"))),
        "eps_change_90d_pct": _chg(avg, _f(r.get("eps_estimate_average_90_days_ago"))),
        "revisions_up_30d": _f(r.get("eps_estimate_revision_up_trailing_30_days")) or 0,
        "revisions_down_30d": _f(r.get("eps_estimate_revision_down_trailing_30_days")) or 0,
    }
    if price and avg and avg > 0:
        out["forward_pe"] = round(price / avg, 2)
    return out


def summarise(payload, price=None, today=None):
    today = today or date.today()
    rows = payload.get("estimates", [])

    def when(r):
        return datetime.strptime(r["date"], "%Y-%m-%d").date()

    years = sorted([r for r in rows if r.get("horizon") == "fiscal year" and when(r) >= today], key=when)[:2]
    quarters = sorted([r for r in rows if r.get("horizon") == "fiscal quarter"
                       and when(r) >= today - timedelta(days=92)], key=when)[:2]
    out = {"as_of": today.isoformat(), "price": price,
           "fiscal_years": [_row(r, price) for r in years],
           "quarters": [_row(r, price) for r in quarters], "flags": []}
    fy = out["fiscal_years"]
    up = sum(r["revisions_up_30d"] for r in fy)
    down = sum(r["revisions_down_30d"] for r in fy)
    out["revision_balance_30d"] = {"up": up, "down": down,
                                   "direction": "rising" if up > down else ("falling" if down > up else "flat")}
    if len(fy) == 2 and fy[0]["eps_avg"] and fy[1]["eps_avg"]:
        eps_g = fy[1]["eps_avg"] / fy[0]["eps_avg"] - 1
        rev_g = (fy[1]["revenue_avg"] / fy[0]["revenue_avg"] - 1) if fy[0]["revenue_avg"] and fy[1]["revenue_avg"] else None
        out["next_year_eps_growth_pct"] = round(eps_g * 100, 2)
        out["next_year_revenue_growth_pct"] = round(rev_g * 100, 2) if rev_g is not None else None
        if abs(eps_g) > 0.15:
            out["flags"].append(
                f"EPS expected to change {eps_g:+.1%} next year (revenue {rev_g:+.1%}). "
                "Find the cause (one-off gains, charges) before using trailing or forward P/E." if rev_g is not None
                else f"EPS expected to change {eps_g:+.1%} next year. Find the cause before using either P/E.")
    for r in fy:
        if r["eps_change_90d_pct"] is not None and abs(r["eps_change_90d_pct"]) > 20:
            out["flags"].append(f"FY ending {r['period_end']}: consensus EPS moved {r['eps_change_90d_pct']}% in 90 days. "
                                "Check for a one-off item or guidance change.")
    return out


def summary_markdown(s):
    lines = [f"Consensus estimates as of {s['as_of']}"]
    for r in s["fiscal_years"]:
        lines.append(f"- FY {r['period_end']}: EPS {r['eps_avg']} (range {r['eps_low']} to {r['eps_high']}, "
                     f"{r['analysts']:.0f} analysts), forward P/E {r.get('forward_pe')}, "
                     f"30d change {r['eps_change_30d_pct']}%, 90d change {r['eps_change_90d_pct']}%")
    rb = s["revision_balance_30d"]
    lines.append(f"- Revisions last 30 days: {rb['up']:.0f} up, {rb['down']:.0f} down ({rb['direction']})")
    if "next_year_eps_growth_pct" in s:
        lines.append(f"- Next fiscal year EPS growth {s['next_year_eps_growth_pct']}%, revenue growth {s['next_year_revenue_growth_pct']}%")
    for f in s["flags"]:
        lines.append(f"- Flag: {f}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True)
    ap.add_argument("--price", type=float)
    ap.add_argument("--today")
    ap.add_argument("--out")
    a = ap.parse_args()
    today = datetime.strptime(a.today, "%Y-%m-%d").date() if a.today else None
    s = summarise(load_json(a.file), a.price, today)
    if a.out:
        Path(a.out).write_text(json.dumps(s, indent=2))
    print(summary_markdown(s))


if __name__ == "__main__":
    main()
