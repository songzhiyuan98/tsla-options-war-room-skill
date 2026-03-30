#!/usr/bin/env python3
"""One-shot data fetch - pulls latest market data and builds snapshot.

Usage: python3 fetch_now.py
Called by the skill when snapshot is stale or missing.
Typically completes in 3-5 seconds.
"""

import asyncio
import aiohttp
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from market_service.rest_client import fetch_all_candles
from market_service.snapshot_builder import build_snapshot, save_snapshot
from market_service.event_engine import detect_events, save_event
from trade_memory.state_manager import init_empty_state


async def fetch():
    init_empty_state()

    async with aiohttp.ClientSession() as session:
        candles = await fetch_all_candles(session)

    snapshot = build_snapshot({}, candles)
    save_snapshot(snapshot)

    event = detect_events(snapshot)
    if event:
        save_event(event)

    # Print summary for verification
    tsla = snapshot.get("symbols", {}).get("TSLA", {})
    price = tsla.get("last_price", "N/A")
    trend_5m = tsla.get("trend_5m", "N/A")
    trend_15m = tsla.get("trend_15m", "N/A")
    regime = snapshot.get("regime", {}).get("market_regime", "N/A")

    print("TSLA ${} | 5m:{} 15m:{} | regime:{}".format(
        price, trend_5m, trend_15m, regime
    ))


if __name__ == "__main__":
    asyncio.run(fetch())
