"""Event engine - detects key market events from snapshot data."""

import json
from datetime import datetime
from . import config


EVENT_TYPES = [
    "near_resistance",
    "near_support",
    "put_rebound_zone_detected",
    "call_reversal_zone_detected",
    "trend_continuation_confirmed",
    "structure_invalidated",
    "profit_zone_reached",
    "high_volume_alert",
]


def detect_events(snapshot: dict, prev_snapshot: dict = None) -> dict:
    """Analyze snapshot for key events. Returns the most significant event or None."""
    tsla = snapshot.get("symbols", {}).get("TSLA", {})

    if not tsla or not tsla.get("last_price"):
        return None

    price = tsla["last_price"]
    resistance = tsla.get("resistance", [])
    support = tsla.get("support", [])
    trend_5m = tsla.get("trend_5m", "unknown")
    trend_15m = tsla.get("trend_15m", "unknown")
    rvol = tsla.get("rvol")

    events = []

    # High volume alert
    if rvol and rvol >= 2.0:
        events.append({
            "event_type": "high_volume_alert",
            "priority": 1,
            "summary": f"TSLA 成交量异常放大，RVOL {rvol}x",
            "reason": [f"RVOL 达到 {rvol}x，显著高于平均水平"],
        })

    # Near resistance
    for r in resistance[:2]:
        if abs(price - r) / r < 0.005:  # within 0.5%
            events.append({
                "event_type": "near_resistance",
                "priority": 2,
                "summary": f"TSLA 接近阻力位 ${r}",
                "zone": [r - 1, r + 1],
                "reason": [f"价格 ${price} 接近阻力 ${r}"],
            })

    # Near support
    for s in support[:2]:
        if abs(price - s) / s < 0.005:
            events.append({
                "event_type": "near_support",
                "priority": 2,
                "summary": f"TSLA 接近支撑位 ${s}",
                "zone": [s - 1, s + 1],
                "reason": [f"价格 ${price} 接近支撑 ${s}"],
            })

    # Put rebound zone - price bouncing to resistance in a downtrend
    if trend_5m == "bearish" and trend_15m == "bearish":
        for r in resistance[:2]:
            if 0 < (r - price) / price < 0.02:  # within 2% below resistance
                qqq = snapshot.get("symbols", {}).get("QQQ", {})
                qqq_trend = qqq.get("trend_5m", "unknown")
                if qqq_trend in ("bearish", "neutral"):
                    events.append({
                        "event_type": "put_rebound_zone_detected",
                        "priority": 3,
                        "summary": f"TSLA 反弹到阻力区，QQQ 未转强",
                        "zone": [price, r],
                        "reason": [
                            "价格反弹接近阻力区",
                            "5分钟和15分钟结构仍偏空",
                            "QQQ 没有转强",
                        ],
                    })

    # Trend continuation confirmed - both timeframes aligned with volume
    if trend_5m == trend_15m and trend_5m != "neutral" and rvol and rvol >= 1.5:
        events.append({
            "event_type": "trend_continuation_confirmed",
            "priority": 2,
            "summary": f"TSLA {trend_5m} 趋势延续确认，放量 {rvol}x",
            "reason": [
                f"5分钟和15分钟趋势一致：{trend_5m}",
                f"RVOL {rvol}x 确认方向",
            ],
        })

    if not events:
        return None

    # Return highest priority event
    events.sort(key=lambda e: e["priority"], reverse=True)
    best = events[0]
    best["symbol"] = "TSLA"
    best["timestamp"] = datetime.now().astimezone().isoformat()
    return best


def save_event(event: dict):
    """Write event to disk."""
    if event is None:
        return
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.EVENT_PATH, "w") as f:
        json.dump(event, f, indent=2, ensure_ascii=False)
