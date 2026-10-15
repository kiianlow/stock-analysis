"""Fundamental metrics for framework Gates 3 to 6 and 8.

Two input modes:
1. Alpha Vantage files:
   python scripts/fundamentals.py --overview overview.json --income income.txt \
       --balance balance.txt --cashflow cashflow.txt --price 347.64 --out fund.json
2. Manual file for SGX or any company Alpha Vantage does not cover:
   python scripts/fundamentals.py --manual templates/financials-manual.json --price 41.20 --market-cap 117e9

All money values stay in the reporting currency. Ratios are plain decimals in JSON and percentages
in the printed summary.

Approximations, stated so nobody mistakes them for exact figures:
- Shares are period-end basic shares outstanding from the balance sheet (Alpha Vantage has no
  diluted count). Per-share growth is close to, but not the same as, diluted per-share growth.
- Invested capital = equity + total debt - cash and short-term investments (all cash treated as excess).
- NOPAT uses the effective tax rate when it sits between 0% and 50%, otherwise 21%.
- FCF = operating cash flow - capital expenditure. Stock-based compensation is not in Alpha Vantage
  data. Get it from the 10-K and subtract it by hand for FCF minus SBC.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from avload import load_overview, load_statement  # noqa: E402

CANONICAL = [
    "revenue", "cogs", "gross_profit", "operating_income", "ebit", "sga", "net_income",
    "net_income_cont", "interest_expense", "pretax_income", "income_tax", "da",
    "total_assets", "current_assets", "current_liabilities", "total_liabilities", "equity",
    "retained_earnings", "cash_sti", "receivables", "inventory", "payables", "ppe_net",
    "goodwill", "intangibles", "lt_investments", "total_debt", "long_term_debt", "shares",
    "cfo", "capex", "dividends", "buybacks",
]

AV_MAP = {
    "revenue": [("income", "totalRevenue")],
    "cogs": [("income", "costOfRevenue"), ("income", "costofGoodsAndServicesSold")],
    "gross_profit": [("income", "grossProfit")],
    "operating_income": [("income", "operatingIncome")],
    "ebit": [("income", "ebit"), ("income", "operatingIncome")],
    "sga": [("income", "sellingGeneralAndAdministrative")],
    "net_income": [("income", "netIncome")],
    "net_income_cont": [("income", "netIncomeFromContinuingOperations"), ("income", "netIncome")],
    "interest_expense": [("income", "interestExpense"), ("income", "interestAndDebtExpense")],
    "pretax_income": [("income", "incomeBeforeTax")],
    "income_tax": [("income", "incomeTaxExpense")],
    "da": [("cash", "depreciationDepletionAndAmortization"), ("income", "depreciationAndAmortization")],
    "total_assets": [("balance", "totalAssets")],
    "current_assets": [("balance", "totalCurrentAssets")],
    "current_liabilities": [("balance", "totalCurrentLiabilities")],
    "total_liabilities": [("balance", "totalLiabilities")],
    "equity": [("balance", "totalShareholderEquity")],
    "retained_earnings": [("balance", "retainedEarnings")],
    "cash_sti": [("balance", "cashAndShortTermInvestments"), ("balance", "cashAndCashEquivalentsAtCarryingValue")],
    "receivables": [("balance", "currentNetReceivables")],
    "inventory": [("balance", "inventory")],
    "payables": [("balance", "currentAccountsPayable")],
    "ppe_net": [("balance", "propertyPlantEquipment")],
    "goodwill": [("balance", "goodwill")],
    "intangibles": [("balance", "intangibleAssetsExcludingGoodwill")],
    "lt_investments": [("balance", "longTermInvestments")],
    "total_debt": [("balance", "shortLongTermDebtTotal")],
    "long_term_debt": [("balance", "longTermDebt"), ("balance", "longTermDebtNoncurrent")],
    "shares": [("balance", "commonStockSharesOutstanding")],
    "cfo": [("cash", "operatingCashflow")],
    "capex": [("cash", "capitalExpenditures")],
    "dividends": [("cash", "dividendPayout"), ("cash", "dividendPayoutCommonStock")],
    "buybacks": [("cash", "paymentsForRepurchaseOfCommonStock"), ("cash", "paymentsForRepurchaseOfEquity")],
}

FINANCIAL_HINTS = ("BANK", "INSURANCE", "REIT", "REAL ESTATE INVESTMENT", "CAPITAL MARKETS", "CREDIT SERVICES")


# ---------------------------------------------------------------- helpers

def num(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return np.nan
    return x


def div(a, b):
    a, b = num(a), num(b)
    if math.isnan(a) or math.isnan(b) or b == 0:
        return np.nan
    return a / b


def avg(cur, prev):
    cur, prev = num(cur), num(prev)
    if math.isnan(prev):
        return cur
    if math.isnan(cur):
        return prev
    return (cur + prev) / 2


def cagr(start, end, years):
    start, end = num(start), num(end)
    if years <= 0 or math.isnan(start) or math.isnan(end) or start <= 0 or end <= 0:
        return np.nan
    return (end / start) ** (1 / years) - 1


def clean(x, digits=4):
    if isinstance(x, (float, np.floating)):
        return None if math.isnan(x) or math.isinf(x) else round(float(x), digits)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, dict):
        return {k: clean(v, digits) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v, digits) for v in x]
    return x


# ---------------------------------------------------------------- canonical frames

def canonical_from_av(statements):
    """statements: dict name -> DataFrame (annual or quarterly) keyed income/balance/cash."""
    index = sorted(set().union(*[df.index for df in statements.values() if not df.empty]))
    out = pd.DataFrame(index=pd.DatetimeIndex(index), columns=CANONICAL, dtype=float)
    for key, sources in AV_MAP.items():
        series = pd.Series(np.nan, index=out.index)
        for stmt, field in sources:
            df = statements.get(stmt)
            if df is None or df.empty or field not in df.columns:
                continue
            series = series.fillna(df[field].reindex(out.index))
        out[key] = series
    return finish_canonical(out, statements.get("balance"))


def finish_canonical(df, balance_raw=None):
    df = df.copy()
    df["capex"] = df["capex"].abs()
    df["dividends"] = df["dividends"].abs()
    df["buybacks"] = df["buybacks"].abs()
    df["gross_profit"] = df["gross_profit"].fillna(df["revenue"] - df["cogs"])
    df["cogs"] = df["cogs"].fillna(df["revenue"] - df["gross_profit"])
    df["ebit"] = df["ebit"].fillna(df["operating_income"])
    df["net_income_cont"] = df["net_income_cont"].fillna(df["net_income"])
    if balance_raw is not None and not balance_raw.empty:
        short = balance_raw.reindex(df.index).get("shortTermDebt", pd.Series(0.0, index=df.index)).fillna(0)
        long_ = balance_raw.reindex(df.index).get("longTermDebt", pd.Series(0.0, index=df.index)).fillna(0)
        df["total_debt"] = df["total_debt"].fillna(short + long_)
    df["total_debt"] = df["total_debt"].fillna(df["long_term_debt"])
    return df


def canonical_from_manual(path):
    data = json.loads(Path(path).read_text())
    frames = {}
    for section in ("years", "quarters"):
        rows = data.get(section) or {}
        if not rows:
            frames[section] = pd.DataFrame(columns=CANONICAL, dtype=float)
            continue
        df = pd.DataFrame.from_dict(rows, orient="index")
        df.index = pd.to_datetime(df.index)
        df = df.reindex(columns=CANONICAL).apply(pd.to_numeric, errors="coerce").sort_index()
        frames[section] = finish_canonical(df)
    meta = {k: v for k, v in data.items() if k not in ("years", "quarters")}
    return frames["years"], frames["quarters"], meta


# ---------------------------------------------------------------- metrics

def tax_rate(row, flags, label):
    rate = div(row["income_tax"], row["pretax_income"])
    if math.isnan(rate) or rate < 0 or rate > 0.5:
        flags.append(f"{label}: effective tax rate unusable ({clean(rate)}), 21% used for NOPAT")
        return 0.21
    return rate


def yearly_metrics(df, flags):
    rows = []
    prev = None
    for date, r in df.iterrows():
        label = date.date().isoformat()
        t = tax_rate(r, flags, label)
        invested = num(r["equity"]) + num(r["total_debt"]) - num(r["cash_sti"])
        nopat = num(r["operating_income"]) * (1 - t)
        ebitda = num(r["operating_income"]) + num(r["da"])
        fcf = num(r["cfo"]) - num(r["capex"])
        net_debt = num(r["total_debt"]) - num(r["cash_sti"])
        p = prev if prev is not None else {}
        avg_assets = avg(r["total_assets"], p.get("total_assets"))
        avg_equity = avg(r["equity"], p.get("equity"))
        avg_ic = avg(invested, p.get("invested_capital"))
        m = {
            "date": label,
            "revenue": num(r["revenue"]),
            "revenue_growth": div(num(r["revenue"]) - num(p.get("revenue")), p.get("revenue")) if p else np.nan,
            "gross_margin": div(r["gross_profit"], r["revenue"]),
            "operating_margin": div(r["operating_income"], r["revenue"]),
            "net_margin": div(r["net_income"], r["revenue"]),
            "ebitda": ebitda,
            "fcf": fcf,
            "fcf_margin": div(fcf, r["revenue"]),
            "shares": num(r["shares"]),
            "fcf_per_share": div(fcf, r["shares"]),
            "eps_basic_approx": div(r["net_income"], r["shares"]),
            "tax_rate_used": t,
            "nopat": nopat,
            "invested_capital": invested,
            "roic": div(nopat, avg_ic) if avg_ic and avg_ic > 0 else np.nan,
            "roe": div(r["net_income"], avg_equity) if avg_equity and avg_equity > 0 else np.nan,
            "roa": div(r["net_income"], avg_assets),
            "asset_turnover": div(r["revenue"], avg_assets),
            "equity_multiplier": div(avg_assets, avg_equity),
            "net_debt": net_debt,
            "net_debt_to_ebitda": div(net_debt, ebitda),
            "interest_coverage": div(r["ebit"], r["interest_expense"]) if num(r["interest_expense"]) > 0 else np.nan,
            "current_ratio": div(r["current_assets"], r["current_liabilities"]),
            "quick_ratio": div(num(r["cash_sti"]) + np.nan_to_num(num(r["receivables"])), r["current_liabilities"]),
            "cfo_to_net_income": div(r["cfo"], r["net_income"]),
            "fcf_to_net_income": div(fcf, r["net_income"]),
            "accruals_ratio": div(num(r["net_income"]) - num(r["cfo"]), avg_assets),
            "dso": div(r["receivables"], r["revenue"]) * 365,
            "dio": div(r["inventory"], r["cogs"]) * 365,
            "dpo": div(r["payables"], r["cogs"]) * 365,
            "capex_to_da": div(r["capex"], r["da"]),
            "capex_to_cfo": div(r["capex"], r["cfo"]),
            "goodwill_intangibles_to_assets": div(np.nan_to_num(num(r["goodwill"])) + np.nan_to_num(num(r["intangibles"])), r["total_assets"]),
            "dividends": num(r["dividends"]),
            "buybacks": num(r["buybacks"]),
            "fcf_payout": div(np.nan_to_num(num(r["dividends"])), fcf) if fcf > 0 else np.nan,
            "total_assets": num(r["total_assets"]),
            "equity": num(r["equity"]),
        }
        ccc_parts = [m["dso"], m["dio"], m["dpo"]]
        m["cash_conversion_cycle"] = (np.nan_to_num(m["dso"]) + np.nan_to_num(m["dio"]) - np.nan_to_num(m["dpo"])
                                      if not all(math.isnan(x) for x in ccc_parts) else np.nan)
        rows.append(m)
        prev = m
    return rows


def validate(df, flags, label="annual"):
    for date, r in df.iterrows():
        d = date.date().isoformat()
        for key in ("revenue", "operating_income", "net_income", "total_assets", "equity", "cfo", "capex"):
            if math.isnan(num(r[key])):
                flags.append(f"{label} {d}: missing {key}")
        ta, tl, eq = num(r["total_assets"]), num(r["total_liabilities"]), num(r["equity"])
        if not any(math.isnan(x) for x in (ta, tl, eq)) and ta:
            gap = abs(ta - (tl + eq)) / ta
            if gap > 0.03:
                flags.append(f"{label} {d}: assets differ from liabilities + equity by {gap:.1%} "
                             "(minority interest or a data error, check the filing)")
        rev, gp, cogs = num(r["revenue"]), num(r["gross_profit"]), num(r["cogs"])
        if not any(math.isnan(x) for x in (rev, gp, cogs)) and rev:
            gap = abs(gp - (rev - cogs)) / rev
            if gap > 0.01:
                flags.append(f"{label} {d}: gross profit differs from revenue - COGS by {gap:.1%}")


def altman(row, market_cap):
    ta, tl = num(row["total_assets"]), num(row["total_liabilities"])
    a = div(num(row["current_assets"]) - num(row["current_liabilities"]), ta)
    b = div(row["retained_earnings"], ta)
    c = div(row["ebit"], ta)
    d_mkt = div(market_cap, tl)
    d_book = div(row["equity"], tl)
    e = div(row["revenue"], ta)
    z = 1.2 * a + 1.4 * b + 3.3 * c + 0.6 * d_mkt + 1.0 * e
    z2 = 6.56 * a + 3.26 * b + 6.72 * c + 1.05 * d_book

    def zone(v, safe, grey):
        if math.isnan(v):
            return None
        return "safe" if v > safe else ("grey" if v >= grey else "distress")
    return {"z": z, "z_zone": zone(z, 2.99, 1.81), "z_double_prime": z2, "z2_zone": zone(z2, 2.60, 1.10),
            "inputs": {"A_wc_ta": a, "B_re_ta": b, "C_ebit_ta": c, "D_mktcap_tl": d_mkt, "D_book_tl": d_book, "E_sales_ta": e}}


def piotroski(df):
    """Latest year vs prior. Needs three balance sheets for beginning-of-year assets."""
    if len(df) < 3:
        return {"score": None, "note": "needs 3 years of data"}
    t, t1, t2 = df.iloc[-1], df.iloc[-2], df.iloc[-3]
    roa_t = div(t["net_income"], t1["total_assets"])
    roa_t1 = div(t1["net_income"], t2["total_assets"])
    lev_t = div(t["long_term_debt"], avg(t["total_assets"], t1["total_assets"]))
    lev_t1 = div(t1["long_term_debt"], avg(t1["total_assets"], t2["total_assets"]))
    tests = {
        "roa_positive": roa_t > 0 if not math.isnan(roa_t) else None,
        "cfo_positive": num(t["cfo"]) > 0 if not math.isnan(num(t["cfo"])) else None,
        "roa_improving": (roa_t > roa_t1) if not (math.isnan(roa_t) or math.isnan(roa_t1)) else None,
        "cfo_above_net_income": (num(t["cfo"]) > num(t["net_income"])) if not math.isnan(num(t["cfo"])) else None,
        "leverage_falling": (lev_t < lev_t1) if not (math.isnan(lev_t) or math.isnan(lev_t1)) else None,
        "current_ratio_rising": _cmp(div(t["current_assets"], t["current_liabilities"]),
                                     div(t1["current_assets"], t1["current_liabilities"])),
        "no_dilution": (num(t["shares"]) <= num(t1["shares"])) if not math.isnan(num(t["shares"]) + num(t1["shares"])) else None,
        "gross_margin_rising": _cmp(div(t["gross_profit"], t["revenue"]), div(t1["gross_profit"], t1["revenue"])),
        "asset_turnover_rising": _cmp(div(t["revenue"], t1["total_assets"]), div(t1["revenue"], t2["total_assets"])),
    }
    known = [v for v in tests.values() if v is not None]
    return {"score": sum(bool(v) for v in known), "out_of": len(known),
            "tests": {k: (None if v is None else bool(v)) for k, v in tests.items()}}


def _cmp(a, b):
    if math.isnan(a) or math.isnan(b):
        return None
    return a > b


def beneish(df):
    if len(df) < 2:
        return {"m": None, "note": "needs 2 years of data"}
    t, p = df.iloc[-1], df.iloc[-2]
    notes = []

    def ratio(a, b, name):
        v = div(a, b)
        if math.isnan(v):
            notes.append(f"{name} set to 1.0 (missing or zero data)")
            return 1.0
        return v

    sec_t = np.nan_to_num(num(t["lt_investments"]))
    sec_p = np.nan_to_num(num(p["lt_investments"]))
    dsri = ratio(div(t["receivables"], t["revenue"]), div(p["receivables"], p["revenue"]), "DSRI")
    gm_t = div(num(t["revenue"]) - num(t["cogs"]), t["revenue"])
    gm_p = div(num(p["revenue"]) - num(p["cogs"]), p["revenue"])
    gmi = ratio(gm_p, gm_t, "GMI")
    aq_t = 1 - div(num(t["current_assets"]) + num(t["ppe_net"]) + sec_t, t["total_assets"])
    aq_p = 1 - div(num(p["current_assets"]) + num(p["ppe_net"]) + sec_p, p["total_assets"])
    aqi = ratio(aq_t, aq_p, "AQI")
    sgi = ratio(t["revenue"], p["revenue"], "SGI")
    dep_t = div(t["da"], num(t["da"]) + num(t["ppe_net"]))
    dep_p = div(p["da"], num(p["da"]) + num(p["ppe_net"]))
    depi = ratio(dep_p, dep_t, "DEPI")
    sgai = ratio(div(t["sga"], t["revenue"]), div(p["sga"], p["revenue"]), "SGAI")
    lv_t = div(num(t["current_liabilities"]) + np.nan_to_num(num(t["long_term_debt"])), t["total_assets"])
    lv_p = div(num(p["current_liabilities"]) + np.nan_to_num(num(p["long_term_debt"])), p["total_assets"])
    lvgi = ratio(lv_t, lv_p, "LVGI")
    tata = div(num(t["net_income_cont"]) - num(t["cfo"]), t["total_assets"])
    if math.isnan(tata):
        notes.append("TATA set to 0 (missing data)")
        tata = 0.0
    m = (-4.84 + 0.920 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi + 0.115 * depi
         - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi)
    m_growth_neutral = m - 0.892 * sgi + 0.892
    return {"m": m, "flag": bool(m > -1.78), "strict_flag": bool(m > -2.22),
            "m_growth_neutral": m_growth_neutral,
            "flag_growth_neutral": bool(m_growth_neutral > -1.78),
            "components": {"DSRI": dsri, "GMI": gmi, "AQI": aqi, "SGI": sgi, "DEPI": depi,
                           "SGAI": sgai, "LVGI": lvgi, "TATA": tata}, "notes": notes}


def quarterly_growth(q):
    """Year-on-year revenue growth for the latest 8 quarters, matched by date."""
    out = []
    if q.empty:
        return out
    q = q.sort_index()
    for date in q.index[-8:]:
        target = date - pd.DateOffset(years=1)
        window = q.loc[(q.index >= target - pd.Timedelta(days=20)) & (q.index <= target + pd.Timedelta(days=20))]
        if window.empty:
            continue
        prior = window.iloc[0]
        out.append({"quarter": date.date().isoformat(),
                    "revenue": num(q.loc[date, "revenue"]),
                    "yoy_growth": div(num(q.loc[date, "revenue"]) - num(prior["revenue"]), prior["revenue"]),
                    "gross_margin": div(q.loc[date, "gross_profit"], q.loc[date, "revenue"]),
                    "operating_margin": div(q.loc[date, "operating_income"], q.loc[date, "revenue"])})
    return out


def check_quarterly(q, annual, flags):
    """Catch feed errors: repeated quarterly values and quarters that do not add up to the annual figure."""
    if q.empty:
        return
    q = q.sort_index()
    for key in ("revenue", "operating_income", "net_income", "cfo", "capex"):
        s = q[key].dropna()
        for i in range(1, len(s)):
            if s.iloc[i] != 0 and s.iloc[i] == s.iloc[i - 1]:
                flags.append(f"Quarterly {key} repeats exactly ({s.iloc[i]:,.0f}) at {s.index[i - 1].date()} and "
                             f"{s.index[i].date()}. Likely a feed error. Prefer annual figures and check the 10-Q.")
    if annual is None or annual.empty or len(q) < 4:
        return
    end = q.index[-1]
    match = annual.loc[(annual.index >= end - pd.Timedelta(days=10)) & (annual.index <= end + pd.Timedelta(days=10))]
    if match.empty:
        return
    a = match.iloc[-1]
    last4 = q.iloc[-4:]
    for key in ("revenue", "net_income", "cfo", "capex"):
        total, yearly = num(last4[key].sum()), num(a[key])
        if not (math.isnan(total) or math.isnan(yearly)) and yearly and abs(total - yearly) / abs(yearly) > 0.01:
            flags.append(f"Last four quarters of {key} sum to {total:,.0f} but the annual report says {yearly:,.0f}. "
                         "Annual figures are used for the year. Treat TTM numbers built from quarters with care.")


def ttm(q):
    if q.empty or len(q) < 4:
        return {}
    last4 = q.sort_index().iloc[-4:]
    span = (last4.index[-1] - last4.index[0]).days
    out = {k: float(last4[k].sum()) if last4[k].notna().all() else np.nan
           for k in ("revenue", "gross_profit", "operating_income", "net_income", "cfo", "capex", "da")}
    out["fcf"] = num(out["cfo"]) - num(out["capex"])
    out["period_end"] = last4.index[-1].date().isoformat()
    out["span_check_days"] = span
    latest = q.sort_index().iloc[-1]
    for k in ("total_debt", "cash_sti", "equity", "shares"):
        out[f"latest_{k}"] = num(latest[k])
    return out


def stronger_vs_bigger(rows):
    if len(rows) < 2:
        return {"verdict": None, "note": "needs 2+ years"}
    first, last = rows[0], rows[-1]
    years = len(rows) - 1

    def direction(a, b, band):
        if math.isnan(a) or math.isnan(b):
            return "n/a"
        return "stronger" if b - a > band else ("weakening" if a - b > band else "just bigger")

    rev_cagr = cagr(first["revenue"], last["revenue"], years)
    fcfps_cagr = cagr(first["fcf_per_share"], last["fcf_per_share"], years)
    share_cagr = cagr(first["shares"], last["shares"], years)
    nd_change = num(last["net_debt_to_ebitda"]) - num(first["net_debt_to_ebitda"])
    table = {
        "gross_margin": direction(first["gross_margin"], last["gross_margin"], 0.01),
        "operating_margin": direction(first["operating_margin"], last["operating_margin"], 0.01),
        "roic": direction(first["roic"], last["roic"], 0.01),
        "fcf_per_share_vs_revenue": ("n/a" if math.isnan(rev_cagr) or math.isnan(fcfps_cagr) else
                                     "stronger" if fcfps_cagr > rev_cagr + 0.02 else
                                     "weakening" if fcfps_cagr < rev_cagr - 0.02 else "just bigger"),
        "share_count": ("n/a" if math.isnan(share_cagr) else
                        "stronger" if share_cagr < -0.005 else
                        "weakening" if share_cagr > 0.005 else "just bigger"),
        "debt_funding_growth": ("n/a" if math.isnan(nd_change) else
                                "weakening" if nd_change > 0.5 else
                                "just bigger" if nd_change > 0.1 else "stronger"),
        "customer_retention": "manual",
        "market_share": "manual",
    }
    counts = {k: sum(v == k for v in table.values()) for k in ("stronger", "just bigger", "weakening")}
    verdict = "pass" if counts["stronger"] >= 5 else ("fail" if counts["weakening"] >= 3 else "mixed")
    return {"period": f"{first['date']} to {last['date']}", "revenue_cagr": rev_cagr,
            "fcf_per_share_cagr": fcfps_cagr, "share_count_cagr": share_cagr,
            "table": table, "counts": counts, "verdict": verdict,
            "note": "Customer retention and market share need manual input. Add them before final verdict."}


def analyse(annual, quarterly, overview=None, price=None, market_cap=None):
    flags = []
    annual = annual.dropna(subset=["revenue"]).iloc[-5:]
    validate(annual, flags, "annual")
    check_quarterly(quarterly, annual, flags)
    rows = yearly_metrics(annual, flags)
    overview = overview or {}
    sector = f"{overview.get('Sector') or ''} {overview.get('Industry') or ''}".upper()
    financial = any(h in sector for h in FINANCIAL_HINTS)
    market_cap = market_cap or overview.get("MarketCapitalization")
    t = ttm(quarterly)
    if not market_cap and price and t and not math.isnan(num(t.get("latest_shares"))):
        market_cap = price * t["latest_shares"]
        flags.append(f"Market cap = price x period-end shares at {t['period_end']} "
                     "(no overview). Check the latest share count in the 10-Q cover page.")
    result = {
        "company": overview.get("Name"), "symbol": overview.get("Symbol"),
        "sector": overview.get("Sector"), "industry": overview.get("Industry"),
        "currency": overview.get("Currency"), "financial_sector": financial,
        "years": rows, "quarterly_growth": quarterly_growth(quarterly), "ttm": t,
        "stronger_vs_bigger": stronger_vs_bigger(rows),
    }
    if rows:
        result["revenue_cagr_full"] = cagr(rows[0]["revenue"], rows[-1]["revenue"], len(rows) - 1)
    if annual.empty:
        flags.append("No annual statements with revenue. Altman, Beneish and Piotroski skipped.")
        result["altman"] = result["beneish"] = {"note": "no annual data"}
    elif financial:
        result["altman"] = {"note": "not valid for banks, insurers or REITs"}
        result["beneish"] = {"note": "not designed for financial companies"}
        flags.append("Financial-sector company: use the bank, insurer or REIT metrics in framework 8.9")
    else:
        result["altman"] = altman(annual.iloc[-1], market_cap) if market_cap else {"note": "market cap needed"}
        result["beneish"] = beneish(annual)
    result["piotroski"] = piotroski(annual)

    if price and t:
        mc = market_cap
        ev = num(mc) + num(t.get("latest_total_debt")) - num(t.get("latest_cash_sti"))
        eps_ttm = div(t.get("net_income"), t.get("latest_shares"))
        result["valuation_snapshot"] = {
            "price": price, "market_cap": mc, "enterprise_value": ev,
            "ttm_period_end": t.get("period_end"),
            "eps_ttm_calc": eps_ttm, "pe_trailing_calc": div(price, eps_ttm) if eps_ttm > 0 else np.nan,
            "pe_trailing_overview": overview.get("TrailingPE") or overview.get("PERatio"),
            "pe_forward_overview": overview.get("ForwardPE"),
            "eps_ttm_overview": overview.get("DilutedEPSTTM") or overview.get("EPS"),
            "fcf_ttm": t.get("fcf"),
            "fcf_yield_ttm": div(t.get("fcf"), mc),
            "ev_to_ebit_ttm": div(ev, t.get("operating_income")),
            "earnings_yield_ebit_ev": div(t.get("operating_income"), ev),
            "ev_to_sales_ttm": div(ev, t.get("revenue")),
            "price_to_fcf_ttm": div(mc, t.get("fcf")),
        }
    result["flags"] = flags
    return clean(result)


def pct(x):
    return "n/a" if x is None else f"{x * 100:.1f}%"


def summary_markdown(r):
    lines = [f"Fundamentals: {r.get('company') or r.get('symbol') or ''} ({r.get('currency') or ''})", ""]
    lines.append("| Year | Revenue | Growth | Gross m. | Op m. | FCF m. | ROIC | ROE | ND/EBITDA | Int cov | CFO/NI | Shares |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for y in r["years"]:
        lines.append(
            f"| {y['date']} | {y['revenue'] / 1e9:.2f}B | {pct(y['revenue_growth'])} | {pct(y['gross_margin'])} | "
            f"{pct(y['operating_margin'])} | {pct(y['fcf_margin'])} | {pct(y['roic'])} | {pct(y['roe'])} | "
            f"{y['net_debt_to_ebitda'] if y['net_debt_to_ebitda'] is not None else 'n/a'} | "
            f"{y['interest_coverage'] if y['interest_coverage'] is not None else 'n/a'} | "
            f"{y['cfo_to_net_income']} | {y['shares'] / 1e6 if y['shares'] else 'n/a'}M |")
    lines.append("")
    if r["quarterly_growth"]:
        lines.append("Quarterly YoY revenue growth: " + ", ".join(
            f"{q['quarter']} {pct(q['yoy_growth'])}" for q in r["quarterly_growth"]))
    sb = r["stronger_vs_bigger"]
    lines.append(f"Stronger vs bigger ({sb.get('period')}): {sb.get('verdict')} {sb.get('counts')}")
    for k, v in (sb.get("table") or {}).items():
        lines.append(f"- {k}: {v}")
    alt = r.get("altman", {})
    if "z" in alt:
        lines.append(f"Altman Z {alt['z']} ({alt['z_zone']}), Z'' {alt['z_double_prime']} ({alt['z2_zone']})")
    pio = r.get("piotroski", {})
    lines.append(f"Piotroski F {pio.get('score')}/{pio.get('out_of')}")
    ben = r.get("beneish", {})
    if ben.get("m") is not None:
        lines.append(f"Beneish M {ben['m']} (flag above -1.78: {ben['flag']}), growth-neutral M {ben['m_growth_neutral']} "
                     f"(flag: {ben['flag_growth_neutral']})")
        if ben["notes"]:
            lines.append(f"- Beneish inputs defaulted: {'; '.join(ben['notes'])}")
    vs = r.get("valuation_snapshot")
    if vs:
        lines.append(f"Valuation (TTM to {vs['ttm_period_end']}): market cap {vs['market_cap'] / 1e9:.1f}B, "
                     f"EV {vs['enterprise_value'] / 1e9:.1f}B, FCF yield {pct(vs['fcf_yield_ttm'])}, "
                     f"EV/EBIT {vs['ev_to_ebit_ttm']}, P/FCF {vs['price_to_fcf_ttm']}, "
                     f"EPS TTM {vs['eps_ttm_calc']}, trailing P/E {vs['pe_trailing_calc']}")
    for f in r["flags"]:
        lines.append(f"- Flag: {f}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--overview")
    ap.add_argument("--income")
    ap.add_argument("--balance")
    ap.add_argument("--cashflow")
    ap.add_argument("--manual")
    ap.add_argument("--price", type=float)
    ap.add_argument("--market-cap", type=float)
    ap.add_argument("--out")
    args = ap.parse_args()

    overview = load_overview(args.overview) if args.overview else {}
    if args.manual:
        annual, quarterly, meta = canonical_from_manual(args.manual)
        overview = {**{"Name": meta.get("company"), "Symbol": meta.get("ticker"),
                       "Currency": meta.get("currency"), "Sector": meta.get("sector"),
                       "Industry": meta.get("industry")}, **overview}
    else:
        if not (args.income and args.balance and args.cashflow):
            ap.error("give --income, --balance and --cashflow, or --manual")
        inc_a, inc_q = load_statement(args.income)
        bal_a, bal_q = load_statement(args.balance)
        cf_a, cf_q = load_statement(args.cashflow)
        annual = canonical_from_av({"income": inc_a, "balance": bal_a, "cash": cf_a})
        quarterly = canonical_from_av({"income": inc_q, "balance": bal_q, "cash": cf_q})
    result = analyse(annual, quarterly, overview, args.price, args.market_cap)
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2, default=str))
    print(summary_markdown(result))


if __name__ == "__main__":
    main()
