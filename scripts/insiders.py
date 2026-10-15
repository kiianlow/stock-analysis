"""Insider buying and selling from Alpha Vantage INSIDER_TRANSACTIONS.

Usage:
    python scripts/insiders.py --file insiders.txt --ticker GOOGL --months 12

The field acquisition_or_disposal arrives in two styles:
- SEC Form 4 transaction codes (P purchase, S sale, A grant, F tax withholding, M exercise,
  C conversion, G gift, J other). Only P counts as a buy and only S as a sale.
- Plain A/D flags. Then a buy is A with a price above zero and a sale is D.
The style is detected from the codes present.

Only common or capital stock counts. Units (RSUs), options and preferred are excluded.
Rows dated after today are dropped and counted, because the feed contains some bad dates.
The feed does not mark 10b5-1 plans, so treat sales as noisy. Open-market buys matter more,
especially when several insiders buy in the same window.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from avload import load_json  # noqa: E402


ENTITY = re.compile(r"\b(L\.?L\.?C\.?|L\.?P\.?|GP|INC\.?|FUND|TRUST|HOLDINGS|PARTNERS|CAPITAL|VENTURES)\b", re.I)


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0


def is_entity(name):
    """Funds, partnerships and companies file Form 4s too. Their trades say little about management."""
    return bool(ENTITY.search(str(name or "")))


def summarise(payload, ticker=None, months=12, today=None):
    today = today or date.today()
    start = today - timedelta(days=int(months * 30.44))
    rows = payload.get("data", []) if isinstance(payload, dict) else payload
    codes = {str(r.get("acquisition_or_disposal", "")).upper() for r in rows}
    sec_style = bool(codes - {"A", "D", ""})
    buys, sells, future, other = [], [], 0, {}
    for r in rows:
        try:
            d = datetime.strptime(r["transaction_date"], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            continue
        if ticker and str(r.get("ticker", ticker)).upper() != ticker.upper():
            continue
        if d > today:
            future += 1
            continue
        if d < start:
            continue
        sec_type = str(r.get("security_type", "")).lower()
        if not ("common" in sec_type or "capital stock" in sec_type) or "unit" in sec_type:
            continue
        code = str(r.get("acquisition_or_disposal", "")).upper()
        shares, price = _f(r.get("shares")), _f(r.get("share_price"))
        rec = {"date": d.isoformat(), "who": r.get("executive"), "title": r.get("executive_title"),
               "code": code, "shares": shares, "price": price, "value": shares * price,
               "entity": is_entity(r.get("executive"))}
        if sec_style:
            if code == "P":
                buys.append(rec)
            elif code == "S":
                sells.append(rec)
            else:
                other[code] = other.get(code, 0) + 1
        elif code == "A" and price > 0:
            buys.append(rec)
        elif code == "D":
            sells.append(rec)

    def total(lst):
        return {"count": len(lst), "shares": sum(x["shares"] for x in lst), "value": sum(x["value"] for x in lst),
                "people": len({x["who"] for x in lst})}

    by_seller = {}
    for s in sells:
        by_seller[s["who"]] = by_seller.get(s["who"], 0.0) + s["value"]
    top = sorted(by_seller.items(), key=lambda kv: -kv[1])[:5]
    people_buys = [x for x in buys if not x["entity"]]
    people_sells = [x for x in sells if not x["entity"]]
    out = {"window": f"{start.isoformat()} to {today.isoformat()}",
           "code_style": "SEC Form 4 codes" if sec_style else "A/D flags",
           "buys": total(buys), "sells": total(sells),
           "individual_buys": total(people_buys), "individual_sells": total(people_sells),
           "entity_sells_value": sum(x["value"] for x in sells if x["entity"]),
           "other_codes_count": other, "future_dated_rows_dropped": future,
           "top_sellers": [{"who": k, "value": v} for k, v in top],
           "recent_buys": sorted(buys, key=lambda x: x["date"], reverse=True)[:10]}
    out["cluster_buying"] = out["individual_buys"]["people"] >= 3
    return out


def summary_markdown(s):
    b, se = s["individual_buys"], s["individual_sells"]
    lines = [f"Insider activity {s['window']} (common and capital stock, {s['code_style']})",
             f"- Open-market buys by individuals: {b['count']} by {b['people']} people, ${b['value'] / 1e6:.2f}M",
             f"- Sales by individuals: {se['count']} by {se['people']} people, ${se['value'] / 1e6:.2f}M",
             f"- Sales by funds and entities: ${s['entity_sells_value'] / 1e6:.2f}M (often not management, check the filer)",
             f"- Cluster buying (3+ buyers): {s['cluster_buying']}",
             f"- Other codes (grants, tax withholding, gifts): {s['other_codes_count']}"]
    if s["future_dated_rows_dropped"]:
        lines.append(f"- Dropped {s['future_dated_rows_dropped']} rows dated after today (feed error)")
    for t in s["top_sellers"]:
        lines.append(f"- Seller: {t['who']} ${t['value'] / 1e6:.2f}M")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True)
    ap.add_argument("--ticker")
    ap.add_argument("--months", type=int, default=12)
    ap.add_argument("--out")
    a = ap.parse_args()
    s = summarise(load_json(a.file), a.ticker, a.months)
    if a.out:
        Path(a.out).write_text(json.dumps(s, indent=2))
    print(summary_markdown(s))


if __name__ == "__main__":
    main()
