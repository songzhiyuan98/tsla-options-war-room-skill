"""Builds latest_snapshot.json from WS prices + REST candles."""

import json
from datetime import datetime
from . import config
from .structure_calculator import (
    calc_trend, calc_support_resistance, calc_vwap,
    calc_atr, calc_rvol, calc_intraday_range, determine_regime,
)


def build_snapshot(ws_prices: dict, candles: dict) -> dict:
    """Build the complete market snapshot.

    Args:
        ws_prices: {symbol: {last_price, timestamp, day_volume}}
        candles: {symbol: {interval: [candle, ...]}}
    """
    snapshot = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "symbols": {},
        "regime": {},
    }

    # Build TSLA section
    tsla_price_data = ws_prices.get("TSLA", {})
    tsla_candles = candles.get("TSLA", {})
    tsla_1m = tsla_candles.get("1min", [])
    tsla_5m = tsla_candles.get("5min", [])
    tsla_15m = tsla_candles.get("15min", [])

    last_price = tsla_price_data.get("last_price")
    if not last_price and tsla_5m:
        last_price = float(tsla_5m[0]["close"])

    prev_close = _get_prev_close(tsla_5m)
    change_pct = _calc_change_pct(last_price, prev_close) if last_price and prev_close else None

    intraday = calc_intraday_range(tsla_1m)

    snapshot["symbols"]["TSLA"] = {
        "last_price": last_price,
        "change_pct": change_pct,
        "intraday_high": intraday["high"],
        "intraday_low": intraday["low"],
        "trend_1m": calc_trend(tsla_1m),
        "trend_5m": calc_trend(tsla_5m),
        "trend_15m": calc_trend(tsla_15m),
        "support": calc_support_resistance(tsla_5m, last_price)["support"] if last_price else [],
        "resistance": calc_support_resistance(tsla_5m, last_price)["resistance"] if last_price else [],
        "vwap": calc_vwap(tsla_1m),
        "atr_5m": calc_atr(tsla_5m),
        "rvol": calc_rvol(tsla_5m),
    }

    # Build QQQ section
    qqq_price_data = ws_prices.get("QQQ", {})
    qqq_candles = candles.get("QQQ", {})
    qqq_5m = qqq_candles.get("5min", [])
    qqq_15m = qqq_candles.get("15min", [])

    qqq_price = qqq_price_data.get("last_price")
    if not qqq_price and qqq_5m:
        qqq_price = float(qqq_5m[0]["close"])

    qqq_prev_close = _get_prev_close(qqq_5m)
    qqq_change_pct = _calc_change_pct(qqq_price, qqq_prev_close) if qqq_price and qqq_prev_close else None

    snapshot["symbols"]["QQQ"] = {
        "last_price": qqq_price,
        "change_pct": qqq_change_pct,
        "trend_5m": calc_trend(qqq_5m),
        "trend_15m": calc_trend(qqq_15m),
    }

    # Build SPY section
    spy_price_data = ws_prices.get("SPY", {})
    spy_candles = candles.get("SPY", {})
    spy_5m = spy_candles.get("5min", [])

    spy_price = spy_price_data.get("last_price")
    if not spy_price and spy_5m:
        spy_price = float(spy_5m[0]["close"])

    snapshot["symbols"]["SPY"] = {
        "last_price": spy_price,
        "trend_5m": calc_trend(spy_5m),
    }

    # Regime
    snapshot["regime"] = determine_regime(
        change_pct or 0.0,
        qqq_change_pct,
    )

    return snapshot


def save_snapshot(snapshot: dict):
    """Write snapshot to disk."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)


def _get_prev_close(candles_5m: list) -> float:
    """Estimate previous close from 5m candles (use last available close from earlier session)."""
    if not candles_5m or len(candles_5m) < 2:
        return None
    # Use the oldest candle's open as a rough proxy for session start
    return float(candles_5m[-1]["open"])


def _calc_change_pct(current: float, prev: float) -> float:
    if prev == 0:
        return 0.0
    return round((current - prev) / prev * 100, 2)
