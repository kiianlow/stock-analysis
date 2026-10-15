"""Valuation calculators for framework Gate 8 and the cash-secured put entry rules.

Subcommands:
    dcf          Two-stage DCF on free cash flow
    reverse-dcf  Growth rate the current price implies
    expected     Expected annual return (yield + growth + multiple change)
    scenarios    Probability-weighted value and upside/downside ratio
    csp          Cash-secured put breakeven and annualised yield
    wacc         Cost of equity (CAPM) and WACC

Examples:
    python scripts/valuation.py dcf --fcf 53.3e9 --growth 0.10 --years 10 --wacc 0.095 \
        --terminal 0.03 --net-debt -20e9 --shares 12.1e9
    python scripts/valuation.py reverse-dcf --price 347.64 --fcf 53.3e9 --wacc 0.095 \
        --terminal 0.03 --net-debt -20e9 --shares 12.1e9
    python scripts/valuation.py expected --yield 0.04 --growth 0.08 --entry 25 --exit 20 --years 5
    python scripts/valuation.py scenarios --price 347.64 --bull 480:0.25 --base 400:0.5 --bear 260:0.25
    python scripts/valuation.py csp --strike 200 --premium 4 --dte 30

Method notes:
- The DCF discounts free cash flow (operating cash flow - capex) at WACC and subtracts net debt.
  This is the common practitioner shortcut. Strictly, unlevered FCF adds back after-tax interest.
  For low-debt companies the gap is small. For leveraged companies, model unlevered FCF by hand.
- Terminal value uses Gordon growth on the final-year FCF.
"""
from __future__ import annotations

import argparse
import json


def capm(rf, beta, erp):
    return rf + beta * erp


def wacc(equity_value, debt_value, cost_equity, cost_debt, tax):
    total = equity_value + debt_value
    return equity_value / total * cost_equity + debt_value / total * cost_debt * (1 - tax)


def dcf(fcf0, growth, years, discount, terminal, net_debt, shares, fade_to=None):
    """Two-stage DCF. Growth fades linearly from `growth` to `fade_to` (default: constant)."""
    if discount <= terminal:
        raise ValueError("discount rate must exceed terminal growth")
    end_growth = growth if fade_to is None else fade_to
    flows, fcf = [], fcf0
    for t in range(1, years + 1):
        g = growth + (end_growth - growth) * (t - 1) / max(years - 1, 1)
        fcf = fcf * (1 + g)
        flows.append((t, g, fcf, fcf / (1 + discount) ** t))
    tv = flows[-1][2] * (1 + terminal) / (discount - terminal)
    pv_tv = tv / (1 + discount) ** years
    pv_flows = sum(f[3] for f in flows)
    ev = pv_flows + pv_tv
    equity = ev - net_debt
    return {
        "enterprise_value": ev, "equity_value": equity, "per_share": equity / shares,
        "pv_explicit": pv_flows, "pv_terminal": pv_tv, "terminal_share_of_value": pv_tv / ev,
        "terminal_warning": pv_tv / ev > 0.75,
        "flows": [{"year": t, "growth": round(g, 4), "fcf": f, "pv": pv} for t, g, f, pv in flows],
    }


def reverse_dcf(price, fcf0, discount, terminal, net_debt, shares, years=10, lo=-0.5, hi=1.0):
    """Constant growth over `years` that makes the DCF value equal the price. Bisection."""
    def gap(g):
        return dcf(fcf0, g, years, discount, terminal, net_debt, shares)["per_share"] - price
    f_lo, f_hi = gap(lo), gap(hi)
    if f_lo * f_hi > 0:
        return {"implied_growth": None, "note": "price outside the solvable range"}
    for _ in range(200):
        mid = (lo + hi) / 2
        f_mid = gap(mid)
        if abs(f_mid) < 1e-6:
            break
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return {"implied_growth": mid, "years": years, "check_value": price + gap(mid)}


def expected_return(start_yield, growth, entry_multiple, exit_multiple, years):
    multiple_change = (exit_multiple / entry_multiple) ** (1 / years) - 1
    return {"multiple_change_per_year": multiple_change,
            "expected_return": start_yield + growth + multiple_change,
            "note": "additive approximation, framework Gate 8.4"}


def scenarios(price, cases):
    total_p = sum(p for _, _, p in cases)
    if abs(total_p - 1) > 1e-6:
        raise ValueError(f"probabilities add to {total_p}, not 1")
    weighted = sum(v * p for _, v, p in cases)
    named = {name: v for name, v, _ in cases}
    out = {"probability_weighted_value": weighted,
           "upside_to_weighted_pct": (weighted / price - 1) * 100}
    if "base" in named and "bear" in named and named["bear"] < price:
        out["upside_downside_ratio"] = (named["base"] - price) / (price - named["bear"])
    return out


def csp(strike, premium, dte):
    return {"breakeven": strike - premium,
            "annualised_yield": premium / strike * 365 / dte,
            "max_loss_per_share": strike - premium,
            "collateral_per_contract": strike * 100}


def graham_number(eps, bvps):
    if eps <= 0 or bvps <= 0:
        return None
    return (22.5 * eps * bvps) ** 0.5


def _case(text):
    value, prob = text.split(":")
    return float(value), float(prob)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dcf")
    for name in ("fcf", "growth", "wacc", "terminal", "net-debt", "shares"):
        d.add_argument(f"--{name}", type=float, required=True)
    d.add_argument("--years", type=int, default=10)
    d.add_argument("--fade-to", type=float)

    r = sub.add_parser("reverse-dcf")
    for name in ("price", "fcf", "wacc", "terminal", "net-debt", "shares"):
        r.add_argument(f"--{name}", type=float, required=True)
    r.add_argument("--years", type=int, default=10)

    e = sub.add_parser("expected")
    e.add_argument("--yield", dest="start_yield", type=float, required=True)
    for name in ("growth", "entry", "exit"):
        e.add_argument(f"--{name}", type=float, required=True)
    e.add_argument("--years", type=int, default=5)

    s = sub.add_parser("scenarios")
    s.add_argument("--price", type=float, required=True)
    for name in ("bull", "base", "bear"):
        s.add_argument(f"--{name}", required=True, help="value:probability")

    c = sub.add_parser("csp")
    for name in ("strike", "premium"):
        c.add_argument(f"--{name}", type=float, required=True)
    c.add_argument("--dte", type=int, required=True)

    w = sub.add_parser("wacc")
    for name in ("rf", "beta", "erp", "equity-value", "debt-value", "cost-debt", "tax"):
        w.add_argument(f"--{name}", type=float, required=True)

    a = ap.parse_args()
    if a.cmd == "dcf":
        out = dcf(a.fcf, a.growth, a.years, a.wacc, a.terminal, a.net_debt, a.shares, a.fade_to)
    elif a.cmd == "reverse-dcf":
        out = reverse_dcf(a.price, a.fcf, a.wacc, a.terminal, a.net_debt, a.shares, a.years)
    elif a.cmd == "expected":
        out = expected_return(a.start_yield, a.growth, a.entry, a.exit, a.years)
    elif a.cmd == "scenarios":
        cases = [(n, *_case(getattr(a, n))) for n in ("bull", "base", "bear")]
        out = scenarios(a.price, cases)
    elif a.cmd == "csp":
        out = csp(a.strike, a.premium, a.dte)
    else:
        re_ = capm(a.rf, a.beta, a.erp)
        out = {"cost_of_equity": re_, "wacc": wacc(a.equity_value, a.debt_value, re_, a.cost_debt, a.tax)}
    print(json.dumps(out, indent=2, default=float))


if __name__ == "__main__":
    main()
