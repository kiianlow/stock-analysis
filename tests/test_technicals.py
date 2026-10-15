import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import technicals as t  # noqa: E402


def frame(close, spread=1.0):
    idx = pd.bdate_range("2025-01-01", periods=len(close))
    close = pd.Series(close, index=idx, dtype=float)
    return pd.DataFrame({"open": close, "high": close + spread, "low": close - spread,
                         "close": close, "volume": 1000.0}, index=idx)


def test_rsi_wilder_hand_computed():
    # Expected values derived by hand from Wilder's definition, independent of the code.
    closes = [44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03,
              45.61, 46.28, 46.28, 46.00, 46.03]
    # First 14 changes: gains sum to 3.34, losses sum to 1.40.
    g, l = 3.34 / 14, 1.40 / 14
    expected_14 = 100 - 100 / (1 + g / l)
    g, l = (g * 13 + 0.00) / 14, (l * 13 + 0.28) / 14   # 46.28 -> 46.00
    expected_15 = 100 - 100 / (1 + g / l)
    g, l = (g * 13 + 0.03) / 14, (l * 13 + 0.00) / 14   # 46.00 -> 46.03
    expected_16 = 100 - 100 / (1 + g / l)
    rsi = t.rsi_wilder(pd.Series(closes))
    assert rsi.iloc[14] == pytest.approx(expected_14)
    assert round(rsi.iloc[14], 2) == 70.46
    assert rsi.iloc[15] == pytest.approx(expected_15)
    assert rsi.iloc[16] == pytest.approx(expected_16)
    assert rsi.iloc[:14].isna().all()


def test_rsi_alternating_moves():
    closes = [100 + (i % 2) for i in range(16)]  # changes: +1 at odd index, -1 at even index
    rsi = t.rsi_wilder(pd.Series(closes, dtype=float))
    assert rsi.iloc[14] == pytest.approx(50.0)  # 7 gains, 7 losses of 1
    gain, loss = (0.5 * 13 + 1) / 14, (0.5 * 13 + 0) / 14  # index 15 change is +1
    assert rsi.iloc[15] == pytest.approx(100 - 100 / (1 + gain / loss))


def test_rsi_only_gains_is_100():
    rsi = t.rsi_wilder(pd.Series(np.arange(1, 30, dtype=float)))
    assert rsi.dropna().eq(100.0).all()


def test_atr_constant_range():
    df = frame([10.0] * 30, spread=1.0)
    assert t.atr_wilder(df).iloc[-1] == pytest.approx(2.0)


def test_adx_perfect_uptrend_is_100():
    df = frame(np.arange(100, 160, dtype=float), spread=0.5)
    adx = t.adx_wilder(df)
    assert adx["adx"].iloc[-1] == pytest.approx(100.0)
    assert adx["minus_di"].iloc[-1] == pytest.approx(0.0)


def test_bollinger_and_macd_flat_series():
    close = pd.Series([50.0] * 60)
    bb = t.bollinger(close)
    assert bb["upper"].iloc[-1] == bb["lower"].iloc[-1] == 50.0
    assert t.macd(close)["macd"].iloc[-1] == pytest.approx(0.0)


def test_classic_pivots():
    p = t.classic_pivots(110, 90, 100)
    assert p == {"P": 100, "R1": 110, "S1": 90, "R2": 120, "S2": 80, "R3": 130, "S3": 70}


def test_fibonacci_levels():
    up = t.fibonacci_levels(100, 200, uptrend=True)
    assert up["38.2%"] == pytest.approx(161.8)
    assert up["50.0%"] == pytest.approx(150.0)
    assert up["61.8%"] == pytest.approx(138.2)
    down = t.fibonacci_levels(100, 200, uptrend=False)
    assert down["38.2%"] == pytest.approx(138.2)


def test_cluster_zones_counts_families_once():
    cands = [(98.0, "swing", "a"), (97.5, "ma", "b"), (97.8, "fib", "c"), (97.6, "fib", "d"), (90.0, "round", "e")]
    zones = t.cluster_zones(cands, price=100, half_width=1.0, side="support")
    assert zones[0]["low"] == 97.5 and zones[0]["high"] == 98.0
    assert zones[0]["strength"] == 3
    assert zones[1]["strength"] == 1 and zones[1]["low"] == 90.0


def test_weinstein_stage_directions():
    rising = pd.Series(np.linspace(100, 200, 80))
    assert t.weinstein_stage(rising, 205)["stage"] == 2
    falling = pd.Series(np.linspace(200, 100, 80))
    assert t.weinstein_stage(falling, 95)["stage"] == 4


def test_open_gap_detection():
    df = frame([10, 10, 10, 15, 15, 15], spread=0.5)
    gaps = t.open_gaps(df)
    assert len(gaps) == 1 and gaps[0]["type"] == "up"
    assert gaps[0]["bottom"] == 10.5 and gaps[0]["top"] == 14.5
