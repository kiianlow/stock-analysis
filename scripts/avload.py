"""Load Alpha Vantage data saved to disk.

Accepts three shapes:
1. Files the chat saves for large connector results: {"result": "<csv or json text>"}
2. Raw JSON exactly as Alpha Vantage returned it (written by hand from an inline result)
3. Raw CSV text

Every loader raises AlphaVantageError when the file holds an error, a rate-limit
message, a premium-only message or a truncated preview instead of real data.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np
import pandas as pd


class AlphaVantageError(RuntimeError):
    """The file does not contain usable Alpha Vantage data."""


_ERROR_KEYS = ("error", "Error Message", "Note", "Information")


def _decode(value):
    if isinstance(value, str):
        stripped = value.strip()
        if stripped[:1] in ("{", "["):
            return json.loads(stripped)
        return stripped
    return value


def read_payload(path):
    """Return the Alpha Vantage payload as a dict, list or CSV string."""
    text = Path(path).read_text(encoding="utf-8").strip()
    if not text:
        raise AlphaVantageError(f"{path}: file is empty")
    payload = _decode(text)
    while isinstance(payload, dict) and set(payload) == {"result"}:
        payload = _decode(payload["result"])
    if isinstance(payload, dict):
        for key in _ERROR_KEYS:
            if key in payload:
                raise AlphaVantageError(f"{path}: Alpha Vantage returned '{key}': {payload[key]}")
        message = str(payload.get("message", ""))
        if "premium" in message.lower():
            raise AlphaVantageError(f"{path}: premium-only endpoint, no real data: {message[:120]}")
        if payload.get("preview") is True:
            raise AlphaVantageError(
                f"{path}: truncated preview, not full data. Re-pull with return_full_data=true."
            )
    return payload


def load_prices(path):
    """Daily, weekly or monthly OHLCV as a DataFrame indexed by date, oldest first."""
    payload = read_payload(path)
    if isinstance(payload, str):
        df = pd.read_csv(io.StringIO(payload))
        df.columns = [c.strip().lower() for c in df.columns]
        date_col = "timestamp" if "timestamp" in df.columns else df.columns[0]
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.set_index(date_col)
    elif isinstance(payload, dict):
        key = next((k for k in payload if "time series" in k.lower()), None)
        if key is None:
            raise AlphaVantageError(f"{path}: no time series found. Keys: {list(payload)[:6]}")
        df = pd.DataFrame.from_dict(payload[key], orient="index")
        df.index = pd.to_datetime(df.index)
        df.columns = [c.split(". ", 1)[-1].strip().lower() for c in df.columns]
    else:
        raise AlphaVantageError(f"{path}: unexpected payload type {type(payload).__name__}")
    df = df.rename(columns={"adjusted close": "adjusted_close"})
    df = df.apply(pd.to_numeric, errors="coerce").sort_index()
    df.index.name = "date"
    missing = {"open", "high", "low", "close", "volume"} - set(df.columns)
    if missing:
        raise AlphaVantageError(f"{path}: missing price columns {sorted(missing)}")
    return df


def ohlc_violations(df):
    """Rows where prices break OHLC logic. Catches copying errors in hand-saved data."""
    bad = (
        (df["high"] < df[["open", "close"]].max(axis=1) - 1e-9)
        | (df["low"] > df[["open", "close"]].min(axis=1) + 1e-9)
        | (df[["open", "high", "low", "close"]] <= 0).any(axis=1)
        | df[["open", "high", "low", "close", "volume"]].isna().any(axis=1)
    )
    return [d.date().isoformat() for d in df.index[bad]]


def crosscheck_daily_weekly(daily, weekly, price_tol=0.011, volume_tol=0.001):
    """Rebuild each complete week from daily bars and compare with the weekly series.
    The weekly file is saved by the connector, so a mismatch points to a copying error in daily data."""
    mismatches, checked = [], 0
    iso = daily.index.isocalendar()
    groups = daily.groupby([iso["year"].to_numpy(), iso["week"].to_numpy()])
    keys = sorted(groups.groups)
    for key in keys[1:]:  # first week in the daily window may be partial
        week = groups.get_group(key)
        end = week.index[-1]
        if end not in weekly.index:
            continue
        w = weekly.loc[end]
        built = {"open": week["open"].iloc[0], "high": week["high"].max(), "low": week["low"].min(),
                 "close": week["close"].iloc[-1], "volume": week["volume"].sum()}
        checked += 1
        for col in ("open", "high", "low", "close"):
            if abs(built[col] - w[col]) > price_tol:
                mismatches.append(f"{end.date()} {col}: daily {built[col]} vs weekly {w[col]}")
        if w["volume"] and abs(built["volume"] - w["volume"]) / w["volume"] > volume_tol:
            mismatches.append(f"{end.date()} volume: daily {built['volume']:.0f} vs weekly {w['volume']:.0f}")
    return {"weeks_checked": checked, "mismatches": mismatches}


def load_indicator(path):
    """Alpha Vantage indicator (SMA, RSI...) as a Series per output column, oldest first."""
    payload = read_payload(path)
    key = next((k for k in payload if k.startswith("Technical Analysis")), None)
    if key is None:
        raise AlphaVantageError(f"{path}: no indicator data found")
    df = pd.DataFrame.from_dict(payload[key], orient="index")
    df.index = pd.to_datetime(df.index)
    return df.apply(pd.to_numeric, errors="coerce").sort_index()


def detect_splits(df, threshold=1.8):
    """Dates where the close jumped by a split-like ratio. Unadjusted series need this check."""
    ratio = df["close"] / df["close"].shift(1)
    mask = (ratio > threshold) | (ratio < 1 / threshold)
    return [(d.date().isoformat(), round(float(r), 3)) for d, r in ratio[mask].items()]


def _reports_to_df(reports):
    if not reports:
        return pd.DataFrame()
    df = pd.DataFrame(reports)
    currency = None
    if "reportedCurrency" in df.columns:
        currency = df["reportedCurrency"].dropna().iloc[0] if df["reportedCurrency"].notna().any() else None
        df = df.drop(columns=["reportedCurrency"])
    df["fiscalDateEnding"] = pd.to_datetime(df["fiscalDateEnding"])
    df = df.set_index("fiscalDateEnding").sort_index()
    df = df.apply(lambda col: pd.to_numeric(col.replace({"None": np.nan, "": np.nan}), errors="coerce"))
    df.attrs["currency"] = currency
    return df


def load_statement(path):
    """INCOME_STATEMENT, BALANCE_SHEET or CASH_FLOW as (annual, quarterly) DataFrames."""
    payload = read_payload(path)
    if not isinstance(payload, dict) or "annualReports" not in payload:
        raise AlphaVantageError(f"{path}: not a financial statement payload")
    return _reports_to_df(payload.get("annualReports")), _reports_to_df(payload.get("quarterlyReports"))


def load_overview(path):
    """COMPANY_OVERVIEW as a dict. Numeric strings become floats, 'None' and '-' become None."""
    payload = read_payload(path)
    if not isinstance(payload, dict) or "Symbol" not in payload:
        raise AlphaVantageError(f"{path}: not a company overview payload")
    out = {}
    for key, value in payload.items():
        if value in ("None", "-", "", None):
            out[key] = None
            continue
        try:
            out[key] = float(value)
        except (TypeError, ValueError):
            out[key] = value
    return out


def load_json(path):
    payload = read_payload(path)
    if not isinstance(payload, (dict, list)):
        raise AlphaVantageError(f"{path}: expected JSON")
    return payload


def find_file(folder, stem):
    """First file in folder whose name starts with stem (daily.csv, daily.txt, daily.json)."""
    matches = sorted(Path(folder).glob(f"{stem}.*"))
    return matches[0] if matches else None
