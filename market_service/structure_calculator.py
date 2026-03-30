"""Technical structure calculations from OHLCV data."""

from datetime import datetime


def calc_trend(candles: list) -> str:
    """Determine trend from candles (most recent first from Twelve Data)."""
    if not candles or len(candles) < 5:
        return "unknown"

    closes = [float(c["close"]) for c in candles[:10]]
    # candles[0] is most recent
    recent_avg = sum(closes[:3]) / 3
    older_avg = sum(closes[5:8]) / 3 if len(closes) >= 8 else sum(closes[3:]) / max(len(closes) - 3, 1)

    diff_pct = (recent_avg - older_avg) / older_avg * 100

    if diff_pct > 0.3:
        return "bullish"
    elif diff_pct < -0.3:
        return "bearish"
    else:
        return "neutral"


def calc_support_resistance(candles: list, current_price: float) -> dict:
    """Find support and resistance levels from recent candle highs/lows."""
    if not candles or len(candles) < 5:
        return {"support": [], "resistance": []}

    highs = sorted(set(round(float(c["high"]), 2) for c in candles[:20]), reverse=True)
    lows = sorted(set(round(float(c["low"]), 2) for c in candles[:20]))

    resistance = [h for h in highs if h > current_price][:3]
    support = [l for l in lows if l < current_price][:3]

    return {"support": support, "resistance": resistance}


def calc_vwap(candles: list) -> float:
    """Approximate VWAP from available candles."""
    if not candles:
        return None

    total_pv = 0.0
    total_v = 0.0

    for c in candles:
        typical = (float(c["high"]) + float(c["low"]) + float(c["close"])) / 3
        vol = int(c.get("volume", 0))
        total_pv += typical * vol
        total_v += vol

    if total_v == 0:
        return None
    return round(total_pv / total_v, 2)


def calc_atr(candles: list, period: int = 14) -> float:
    """Calculate ATR from candles."""
    if not candles or len(candles) < period + 1:
        return None

    trs = []
    for i in range(min(period, len(candles) - 1)):
        h = float(candles[i]["high"])
        l = float(candles[i]["low"])
        prev_c = float(candles[i + 1]["close"])
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)

    if not trs:
        return None
    return round(sum(trs) / len(trs), 2)


def calc_rvol(candles: list) -> float:
    """Calculate relative volume (current vs average)."""
    if not candles or len(candles) < 10:
        return None

    volumes = [int(c.get("volume", 0)) for c in candles]
    if not volumes or volumes[0] == 0:
        return None

    avg_vol = sum(volumes[1:]) / len(volumes[1:]) if len(volumes) > 1 else volumes[0]
    if avg_vol == 0:
        return None

    return round(volumes[0] / avg_vol, 2)


def calc_intraday_range(candles: list) -> dict:
    """Calculate intraday high/low from 1min candles."""
    if not candles:
        return {"high": None, "low": None}

    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]

    return {
        "high": round(max(highs), 2),
        "low": round(min(lows), 2),
    }


def determine_regime(tsla_change_pct: float, qqq_change_pct: float) -> dict:
    """Determine market regime and TSLA relative strength."""
    regime = "unknown"
    relative_strength = "unknown"

    if qqq_change_pct is not None:
        if qqq_change_pct < -0.5:
            regime = "risk_off"
        elif qqq_change_pct > 0.5:
            regime = "risk_on"
        else:
            regime = "chop"

        diff = tsla_change_pct - qqq_change_pct
        if diff > 0.5:
            relative_strength = "stronger"
        elif diff < -0.5:
            relative_strength = "weaker"
        else:
            relative_strength = "neutral"
    else:
        if tsla_change_pct < -1.0:
            regime = "risk_off"
        elif tsla_change_pct > 1.0:
            regime = "risk_on"
        else:
            regime = "chop"

    return {
        "market_regime": regime,
        "tsla_relative_strength_vs_qqq": relative_strength,
    }
