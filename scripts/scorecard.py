"""Weighted scorecard, rating map and overrides from the framework.

Usage:
    python scripts/scorecard.py --scores '{"valuation":4,"growth":4,"profitability":5,
        "financial_strength":4,"moat":5,"management":4,"industry":4,"earnings_quality":4,
        "risk":3,"technical":3}' [--kill-switch] [--below-hurdle]

Integer arithmetic on weight x score totals avoids float rounding at the rating boundaries.
"""
from __future__ import annotations

import argparse
import json

WEIGHTS = {
    "valuation": 15, "growth": 12, "profitability": 10, "financial_strength": 12, "moat": 12,
    "management": 8, "industry": 8, "earnings_quality": 10, "risk": 8, "technical": 5,
}
ORDER = ["Sell", "Reduce", "Hold", "Buy", "Strong Buy"]
THRESHOLDS = [(420, "Strong Buy"), (360, "Buy"), (280, "Hold"), (220, "Reduce")]

assert sum(WEIGHTS.values()) == 100


def raw_rating(total):
    for floor, label in THRESHOLDS:
        if total >= floor:
            return label
    return "Sell"


def cap(rating, ceiling):
    return ORDER[min(ORDER.index(rating), ORDER.index(ceiling))]


def score(scores, kill_switch=False, below_hurdle=False):
    missing = set(WEIGHTS) - set(scores)
    if missing:
        raise ValueError(f"missing scores: {sorted(missing)}")
    for k, v in scores.items():
        if k not in WEIGHTS:
            raise ValueError(f"unknown category: {k}")
        if v not in (1, 2, 3, 4, 5):
            raise ValueError(f"{k} must be an integer 1 to 5, got {v}")
    total = sum(WEIGHTS[k] * scores[k] for k in WEIGHTS)
    rating = raw_rating(total)
    final, overrides, notes = rating, [], []
    if kill_switch:
        final = "Sell"
        overrides.append("Gate 0 kill switch: Sell or avoid")
    else:
        if scores["valuation"] <= 2:
            final = cap(final, "Hold")
            overrides.append("Valuation 1 or 2: capped at Hold (great company, expensive price)")
        if (scores["moat"] + scores["profitability"]) / 2 <= 2:
            final = cap(final, "Hold")
            overrides.append("Moat and profitability average 2 or below: capped at Hold (bad company, good price)")
        if scores["earnings_quality"] == 1:
            final = cap(final, "Reduce")
            overrides.append("Earnings quality 1: capped at Reduce")
        if below_hurdle:
            final = cap(final, "Hold")
            overrides.append("Expected return below the index hurdle: capped at Hold")
    if scores["technical"] == 1:
        notes.append("Technical 1 (Stage 4): rating stands, but delay or stage the entry until a base forms")
    return {"total": total, "weighted_score": total / 100, "raw_rating": rating,
            "final_rating": final, "overrides": overrides, "notes": notes,
            "breakdown": {k: {"weight": WEIGHTS[k], "score": scores[k], "points": WEIGHTS[k] * scores[k]}
                          for k in WEIGHTS}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scores", required=True, help="JSON object of category: score")
    ap.add_argument("--kill-switch", action="store_true")
    ap.add_argument("--below-hurdle", action="store_true")
    a = ap.parse_args()
    print(json.dumps(score(json.loads(a.scores), a.kill_switch, a.below_hurdle), indent=2))


if __name__ == "__main__":
    main()
