"""Technical indicators and support/resistance zones from raw price data.

Usage:
    python scripts/technicals.py --daily data/GOOGL/2026-10-15/daily.csv \
        --weekly data/GOOGL/2026-10-15/weekly.txt --sma200 331.2 --out tech.json

Conventions (match the framework, Gate 10):
- RSI(14) and ATR(14) use Wilder smoothing, seeded with a simple average of the first 14 values.
- ADX(14) uses Wilder's sum-based smoothing.
- MACD(12,26,9) uses exponential averages seeded with the first close. Values converge with
  SMA-seeded charting platforms after roughly 60 to 80 bars.
- Bollinger Bands(20,2) use the population standard deviation.
- Support zones cluster candidate levels from independent method families. Strength is the
  number of distinct families inside a zone. Two Fibonacci levels in one zone count once.
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
from avload import crosscheck_daily_weekly, detect_splits, load_indicator, load_prices, ohlc_violations  # noqa: E402

FIB_RATIOS = (0.236, 0.382, 0.5, 0.618, 0.786)


# ---------------------------------------------------------------- indicators

def sma(series, period):
    return series.rolling(period).mean()


def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def rsi_wilder(close, period=14):
    close = close.astype(float)
    delta = close.diff()
    gains = delta.clip(lower=0).to_numpy()
    losses = (-delta.clip(upper=0)).to_numpy()
    out = np.full(len(close), np.nan)
    if len(close) <= period:
        return pd.Series(out, index=close.index)

    def to_rsi(avg_gain, avg_loss):
        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0
        return 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)

    avg_gain = gains[1:period + 1].mean()
    avg_loss = losses[1:period + 1].mean()
    out[period] = to_rsi(avg_gain, avg_loss)
    for i in range(period + 1, len(close)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        out[i] = to_rsi(avg_gain, avg_loss)
    return pd.Series(out, index=close.index)


def true_range(df):
    prev_close = df["close"].shift(1)
    ranges = pd.concat(
        [df["high"] - df["low"], (df["high"] - prev_close).abs(), (df["low"] - prev_close).abs()],
        axis=1,
    )
    return ranges.max(axis=1)


def atr_wilder(df, period=14):
    tr = true_range(df).to_numpy()
    out = np.full(len(df), np.nan)
    if len(df) <= period:
        return pd.Series(out, index=df.index)
    value = tr[1:period + 1].mean()
    out[period] = value
    for i in range(period + 1, len(df)):
        value = (value * (period - 1) + tr[i]) / period
        out[i] = value
    return pd.Series(out, index=df.index)


def adx_wilder(df, period=14):
    """Returns DataFrame with plus_di, minus_di, adx."""
    high, low = df["high"].to_numpy(float), df["low"].to_numpy(float)
    n = len(df)
    result = pd.DataFrame(np.nan, index=df.index, columns=["plus_di", "minus_di", "adx"])
    if n < 2 * period + 1:
        return result
    up = np.diff(high, prepend=np.nan)
    down = -np.diff(low, prepend=np.nan)
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    tr = true_range(df).to_numpy()

    tr_s = tr[1:period + 1].sum()
    p_s = plus_dm[1:period + 1].sum()
    m_s = minus_dm[1:period + 1].sum()
    plus_di = np.full(n, np.nan)
    minus_di = np.full(n, np.nan)
    dx = np.full(n, np.nan)
    for i in range(period, n):
        if i > period:
            tr_s = tr_s - tr_s / period + tr[i]
            p_s = p_s - p_s / period + plus_dm[i]
            m_s = m_s - m_s / period + minus_dm[i]
        plus_di[i] = 100.0 * p_s / tr_s if tr_s else 0.0
        minus_di[i] = 100.0 * m_s / tr_s if tr_s else 0.0
        total = plus_di[i] + minus_di[i]
        dx[i] = 100.0 * abs(plus_di[i] - minus_di[i]) / total if total else 0.0
    adx = np.full(n, np.nan)
    first = 2 * period - 1
    adx[first] = dx[period:first + 1].mean()
    for i in range(first + 1, n):
        adx[i] = (adx[i - 1] * (period - 1) + dx[i]) / period
    result["plus_di"], result["minus_di"], result["adx"] = plus_di, minus_di, adx
    return result


def macd(close, fast=12, slow=26, signal=9):
    line = ema(close, fast) - ema(close, slow)
    sig = ema(line, signal)
    return pd.DataFrame({"macd": line, "signal": sig, "hist": line - sig})


def bollinger(close, period=20, width=2.0):
    mid = sma(close, period)
    std = close.rolling(period).std(ddof=0)
    return pd.DataFrame({"upper": mid + width * std, "mid": mid, "lower": mid - width * std})


def classic_pivots(high, low, close):
    p = (high + low + close) / 3
    return {
        "P": p,
        "R1": 2 * p - low, "S1": 2 * p - high,
        "R2": p + (high - low), "S2": p - (high - low),
        "R3": high + 2 * (p - low), "S3": low - 2 * (high - p),
    }


def fibonacci_levels(swing_low, swing_high, uptrend=True):
    """Uptrend: retracement levels measured down from the high. Downtrend: up from the low."""
    span = swing_high - swing_low
    if uptrend:
        return {f"{r * 100:.1f}%": swing_high - r * span for r in FIB_RATIOS}
    return {f"{r * 100:.1f}%": swing_low + r * span for r in FIB_RATIOS}


def swing_points(df, k=3, kind="low"):
    col = df[kind]
    found = []
    for i in range(k, len(df) - k):
        window = col.iloc[i - k:i + k + 1]
        value = col.iloc[i]
        if (kind == "low" and value == window.min()) or (kind == "high" and value == window.max()):
            found.append((df.index[i].date().isoformat(), float(value)))
    return found


def volume_nodes(df, bins=24, top=3):
    """Approximate volume profile: each bar's volume assigned to its typical price."""
    typical = (df["high"] + df["low"] + df["close"]) / 3
    hist, edges = np.histogram(typical, bins=bins, weights=df["volume"])
    centers = (edges[:-1] + edges[1:]) / 2
    order = np.argsort(hist)[::-1][:top]
    return [{"price": float(centers[i]), "volume": float(hist[i])} for i in order]


def open_gaps(df):
    """Unfilled gaps. Gap up leaves support, gap down leaves resistance."""
    gaps = []
    highs, lows = df["high"].to_numpy(), df["low"].to_numpy()
    for i in range(1, len(df)):
        if lows[i] > highs[i - 1]:
            later = lows[i + 1:]
            if later.size == 0 or later.min() > highs[i - 1]:
                gaps.append({"date": df.index[i].date().isoformat(), "type": "up",
                             "bottom": float(highs[i - 1]), "top": float(lows[i])})
        elif highs[i] < lows[i - 1]:
            later = highs[i + 1:]
            if later.size == 0 or later.max() < lows[i - 1]:
                gaps.append({"date": df.index[i].date().isoformat(), "type": "down",
                             "bottom": float(highs[i]), "top": float(lows[i - 1])})
    return gaps


def round_step(price):
    if price < 10:
        return 0.5
    if price < 50:
        return 5.0
    if price < 200:
        return 10.0
    if price < 1000:
        return 50.0
    return 100.0


def weinstein_stage(weekly_close, price):
    """Heuristic stage call from the 30-week moving average. Confirm visually."""
    ma30 = sma(weekly_close, 30)
    if ma30.dropna().shape[0] < 27:
        return {"stage": None, "label": "not enough weekly history (need 56+ weeks)"}
    now = ma30.iloc[-1]
    slope = now / ma30.iloc[-6] - 1
    prior = now / ma30.iloc[-27] - 1
    above = price > now
    if slope > 0.005 and above:
        stage, label = 2, "Stage 2: price above a rising 30-week MA"
    elif slope < -0.005 and not above:
        stage, label = 4, "Stage 4: price below a falling 30-week MA"
    elif abs(slope) <= 0.005:
        stage = 1 if prior < 0 else 3
        label = ("Stage 1: flat 30-week MA after a decline" if stage == 1
                 else "Stage 3: flat 30-week MA after an advance")
    elif above:
        stage, label = 1, "Stage 1 to 2 transition: price above a still-falling 30-week MA"
    else:
        stage, label = 3, "Stage 3 risk or Stage 2 pullback: price below a still-rising 30-week MA"
    return {"stage": stage, "label": label, "ma30w": float(now),
            "ma30w_slope_5w_pct": round(float(slope) * 100, 2),
            "price_vs_ma30w_pct": round(float(price / now - 1) * 100, 2)}


# ---------------------------------------------------------------- zones

FAMILIES = {
    "swing": "swing high/low", "ma": "moving average", "volume": "volume node",
    "fib": "Fibonacci", "pivot": "pivot", "round": "round number", "gap": "gap",
}


def cluster_zones(candidates, price, half_width, side="support"):
    """candidates: list of (level, family, label). Returns zones nearest first."""
    if side == "support":
        pool = sorted([c for c in candidates if c[0] < price], key=lambda c: -c[0])
    else:
        pool = sorted([c for c in candidates if c[0] > price], key=lambda c: c[0])
    zones = []
    for level, family, label in pool:
        if zones and abs(zones[-1]["anchor"] - level) <= 2 * half_width:
            zone = zones[-1]
        else:
            zone = {"anchor": level, "levels": [], "families": set(), "labels": []}
            zones.append(zone)
        zone["levels"].append(level)
        zone["families"].add(family)
        zone["labels"].append(f"{label} {level:.2f}")
    out = []
    for z in zones:
        out.append({
            "low": round(min(z["levels"]), 2), "high": round(max(z["levels"]), 2),
            "strength": len(z["families"]),
            "methods": sorted(FAMILIES[f] for f in z["families"]),
            "detail": z["labels"],
            "distance_pct": round((max(z["levels"]) / price - 1) * 100, 2) if side == "support"
            else round((min(z["levels"]) / price - 1) * 100, 2),
        })
    return out


def pick_levels(zones, count=3):
    strong = [z for z in zones if z["strength"] >= 2]
    chosen = strong[:count]
    if len(chosen) < count:
        weak = [z for z in zones if z["strength"] < 2 and z not in chosen]
        for z in weak[: count - len(chosen)]:
            chosen.append({**z, "note": "weak, single method"})
        chosen.sort(key=lambda z: abs(z["distance_pct"]))
    return chosen


def last_complete_week(daily):
    last = daily.index[-1]
    iso = daily.index.isocalendar()
    keys = list(zip(iso["year"], iso["week"]))
    current = keys[-1]
    if last.weekday() == 4:
        target = current
    else:
        earlier = [k for k in keys if k != current]
        if not earlier:
            return None
        target = earlier[-1]
    mask = [k == target for k in keys]
    week = daily.loc[mask]
    return {"high": float(week["high"].max()), "low": float(week["low"].min()),
            "close": float(week["close"].iloc[-1]), "week_ending": week.index[-1].date().isoformat()}


# ---------------------------------------------------------------- main analysis

def analyse(daily, weekly=None, sma200=None):
    notes = []
    data_checks = {"ohlc_violations": ohlc_violations(daily)}
    if data_checks["ohlc_violations"]:
        notes.append(f"OHLC logic broken on {data_checks['ohlc_violations']}. Re-check the daily file.")
    if weekly is not None and len(weekly) > 0:
        data_checks["daily_vs_weekly"] = crosscheck_daily_weekly(daily, weekly)
        if data_checks["daily_vs_weekly"]["mismatches"]:
            notes.append("Daily data does not match the weekly series. Re-save the daily file before using it: "
                         + "; ".join(data_checks["daily_vs_weekly"]["mismatches"][:5]))
    splits_daily = detect_splits(daily)
    if splits_daily:
        cut = pd.Timestamp(splits_daily[-1][0])
        daily = daily.loc[daily.index >= cut]
        notes.append(f"Split-like jump in daily data at {splits_daily}. Daily data truncated to after it.")
    close = daily["close"]
    price = float(close.iloc[-1])
    as_of = daily.index[-1].date().isoformat()

    rsi = rsi_wilder(close)
    atr = atr_wilder(daily)
    adx = adx_wilder(daily)
    m = macd(close)
    bb = bollinger(close)
    s20, s50 = sma(close, 20), sma(close, 50)
    s200_val = float(sma(close, 200).iloc[-1]) if len(close) >= 200 else None
    s200_source = "computed from daily" if s200_val is not None else None
    if s200_val is None and sma200 is not None:
        s200_val, s200_source = float(sma200), "supplied (Alpha Vantage SMA endpoint)"
    if s200_val is None and weekly is not None and len(weekly) >= 40:
        s200_val = float(weekly["close"].rolling(40).mean().iloc[-1])
        s200_source = "proxy: 40-week SMA from weekly data"
        notes.append("SMA200 is a 40-week proxy. Pull the SMA endpoint for the exact value.")

    result = {
        "as_of": as_of, "price": price, "bars_daily": int(len(daily)),
        "sma20": _f(s20.iloc[-1]), "sma50": _f(s50.iloc[-1]),
        "sma200": s200_val, "sma200_source": s200_source,
        "price_vs_sma50_pct": _pct(price, s50.iloc[-1]),
        "price_vs_sma200_pct": _pct(price, s200_val) if s200_val else None,
        "rsi14": _f(rsi.iloc[-1]), "rsi14_prev": _f(rsi.iloc[-2]),
        "macd": _f(m["macd"].iloc[-1]), "macd_signal": _f(m["signal"].iloc[-1]),
        "macd_hist": _f(m["hist"].iloc[-1]), "macd_hist_prev": _f(m["hist"].iloc[-2]),
        "atr14": _f(atr.iloc[-1]), "atr14_pct": _pct_of(atr.iloc[-1], price),
        "adx14": _f(adx["adx"].iloc[-1]), "plus_di": _f(adx["plus_di"].iloc[-1]),
        "minus_di": _f(adx["minus_di"].iloc[-1]),
        "bb_upper": _f(bb["upper"].iloc[-1]), "bb_mid": _f(bb["mid"].iloc[-1]),
        "bb_lower": _f(bb["lower"].iloc[-1]),
        "bb_pct_b": _f((price - bb["lower"].iloc[-1]) / (bb["upper"].iloc[-1] - bb["lower"].iloc[-1])),
        "bb_width_pct": _pct_of(bb["upper"].iloc[-1] - bb["lower"].iloc[-1], bb["mid"].iloc[-1]),
    }

    candidates = []
    for date, level in swing_points(daily, k=3, kind="low"):
        candidates.append((level, "swing", f"daily swing low {date}"))
    for date, level in swing_points(daily, k=3, kind="high"):
        candidates.append((level, "swing", f"daily swing high {date}"))
    for name, series in (("SMA20", s20), ("SMA50", s50)):
        if not math.isnan(series.iloc[-1]):
            candidates.append((float(series.iloc[-1]), "ma", name))
    if s200_val:
        candidates.append((s200_val, "ma", "SMA200"))
    nodes = volume_nodes(daily)
    for node in nodes:
        candidates.append((node["price"], "volume", "volume node"))
    gaps = open_gaps(daily)
    for g in gaps:
        candidates.append((g["bottom"], "gap", f"gap {g['type']} {g['date']} bottom"))
        candidates.append((g["top"], "gap", f"gap {g['type']} {g['date']} top"))
    week = last_complete_week(daily)
    if week:
        piv = classic_pivots(week["high"], week["low"], week["close"])
        result["weekly_pivots"] = {k: round(v, 2) for k, v in piv.items()}
        result["weekly_pivots_from_week_ending"] = week["week_ending"]
        for k, v in piv.items():
            candidates.append((v, "pivot", f"weekly pivot {k}"))
    step = round_step(price)
    base = math.floor(price / step) * step
    for i in range(0, 6):
        candidates.append((base - i * step, "round", "round number"))
        candidates.append((base + (i + 1) * step, "round", "round number"))

    if weekly is not None and len(weekly) > 0:
        splits_weekly = detect_splits(weekly)
        wk = weekly
        if splits_weekly:
            cut = pd.Timestamp(splits_weekly[-1][0])
            wk = weekly.loc[weekly.index >= cut]
            notes.append(f"Split-like jump in weekly data at {splits_weekly[-1]}. Weekly data truncated to after it.")
        wclose = wk["adjusted_close"] if "adjusted_close" in wk.columns else wk["close"]
        result["stage"] = weinstein_stage(wclose, price)
        if result["stage"].get("ma30w"):
            candidates.append((result["stage"]["ma30w"], "ma", "30-week MA"))
        last_year = wk.loc[wk.index > wk.index[-1] - pd.Timedelta(days=365)]
        hi, lo = float(last_year["high"].max()), float(last_year["low"].min())
        hi_date, lo_date = last_year["high"].idxmax(), last_year["low"].idxmin()
        uptrend = lo_date < hi_date
        fib = fibonacci_levels(lo, hi, uptrend=uptrend)
        result["week52_high"], result["week52_low"] = hi, lo
        result["week52_high_date"], result["week52_low_date"] = hi_date.date().isoformat(), lo_date.date().isoformat()
        result["off_52w_high_pct"] = _pct(price, hi)
        result["fib_direction"] = "retracement of the advance (low came first)" if uptrend else "bounce levels off the decline (high came first)"
        result["fibonacci"] = {k: round(v, 2) for k, v in fib.items()}
        for k, v in fib.items():
            candidates.append((v, "fib", f"Fib {k}"))
        candidates.append((lo, "swing", "52-week low"))
        candidates.append((hi, "swing", "52-week high"))
        for date, level in swing_points(last_year, k=2, kind="low"):
            candidates.append((level, "swing", f"weekly swing low {date}"))
        for date, level in swing_points(last_year, k=2, kind="high"):
            candidates.append((level, "swing", f"weekly swing high {date}"))
    else:
        notes.append("No weekly data: stage, 52-week range and Fibonacci levels skipped.")

    half_width = max(0.01 * price, 0.5 * (result["atr14"] or 0))
    support = cluster_zones(candidates, price, half_width, side="support")
    resistance = cluster_zones(candidates, price, half_width, side="resistance")
    result["zone_half_width"] = round(half_width, 2)
    result["support_zones"] = support
    result["resistance_zones"] = resistance
    result["S"] = pick_levels(support)
    result["R"] = pick_levels(resistance)
    result["volume_nodes"] = nodes
    result["open_gaps"] = gaps
    result["data_checks"] = data_checks
    result["notes"] = notes
    return result


def _f(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(x) else round(x, 4)


def _pct(a, b):
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return None
    if not b or math.isnan(a) or math.isnan(b):
        return None
    return round((a / b - 1) * 100, 2)


def _pct_of(part, whole):
    try:
        part, whole = float(part), float(whole)
    except (TypeError, ValueError):
        return None
    if not whole or math.isnan(part) or math.isnan(whole):
        return None
    return round(part / whole * 100, 2)


def summary_markdown(r):
    lines = [f"Technicals as of {r['as_of']}, close {r['price']:.2f}", ""]
    st = r.get("stage") or {}
    lines.append(f"- Stage: {st.get('label', 'n/a')}")
    lines.append(f"- SMA20 {r['sma20']}, SMA50 {r['sma50']}, SMA200 {r['sma200']} ({r['sma200_source']})")
    lines.append(f"- RSI14 {r['rsi14']} (prev {r['rsi14_prev']}), MACD hist {r['macd_hist']} (prev {r['macd_hist_prev']})")
    lines.append(f"- ADX14 {r['adx14']} (+DI {r['plus_di']}, -DI {r['minus_di']}), ATR14 {r['atr14']} ({r['atr14_pct']}% of price)")
    lines.append(f"- Bollinger {r['bb_lower']} / {r['bb_mid']} / {r['bb_upper']}, %B {r['bb_pct_b']}")
    if "week52_high" in r:
        lines.append(f"- 52-week range {r['week52_low']:.2f} to {r['week52_high']:.2f}, {r['off_52w_high_pct']}% from high")
    lines.append("")
    for tag, zones in (("Support", r["S"]), ("Resistance", r["R"])):
        for i, z in enumerate(zones, 1):
            note = f" [{z['note']}]" if z.get("note") else ""
            lines.append(f"- {tag[0]}{i}: {z['low']:.2f} to {z['high']:.2f} ({z['distance_pct']}%), "
                         f"strength {z['strength']}: {', '.join(z['methods'])}{note}")
    for n in r["notes"]:
        lines.append(f"- Note: {n}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--daily", required=True)
    ap.add_argument("--weekly")
    ap.add_argument("--sma200", help="200-day SMA as a number, or a saved Alpha Vantage SMA file")
    ap.add_argument("--out")
    args = ap.parse_args()
    daily = load_prices(args.daily)
    weekly = load_prices(args.weekly) if args.weekly else None
    sma200 = None
    if args.sma200:
        try:
            sma200 = float(args.sma200)
        except ValueError:
            sma200 = float(load_indicator(args.sma200).iloc[-1, 0])
    result = analyse(daily, weekly, sma200)
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2, default=str))
    print(summary_markdown(result))


if __name__ == "__main__":
    main()
