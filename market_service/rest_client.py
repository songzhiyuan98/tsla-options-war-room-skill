"""REST client for Twelve Data - pulls OHLCV candles."""

import asyncio
import aiohttp
from datetime import datetime
from . import config


async def fetch_candles(session: aiohttp.ClientSession, symbol: str, interval: str, outputsize: int = 30) -> list:
    """Fetch OHLCV candles for a symbol/interval pair."""
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": config.API_KEY,
    }
    try:
        async with session.get(f"{config.BASE_URL}/time_series", params=params) as resp:
            data = await resp.json()
            if "values" in data:
                return data["values"]
            return []
    except Exception as e:
        print(f"[REST] Error fetching {symbol} {interval}: {e}")
        return []


async def fetch_all_candles(session: aiohttp.ClientSession) -> dict:
    """Fetch candles for all symbols and intervals.

    Returns: {
        "TSLA": {"1min": [...], "5min": [...], "15min": [...]},
        "QQQ": {"5min": [...], "15min": [...]},
        "SPY": {"5min": [...]}
    }
    """
    tasks = {}

    # TSLA gets all intervals
    for interval in config.INTERVALS:
        tasks[f"TSLA_{interval}"] = fetch_candles(session, "TSLA", interval)

    # QQQ gets 5m and 15m
    for interval in ["5min", "15min"]:
        tasks[f"QQQ_{interval}"] = fetch_candles(session, "QQQ", interval)

    # SPY gets 5m only
    tasks["SPY_5min"] = fetch_candles(session, "SPY", "5min")

    # Run with small delays to respect rate limits (8 req/min)
    result = {}
    for key, coro in tasks.items():
        symbol, interval = key.split("_", 1)
        if symbol not in result:
            result[symbol] = {}
        result[symbol][interval] = await coro
        await asyncio.sleep(0.5)  # ~2 req/sec, well within 8/min

    return result
