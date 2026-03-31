#!/usr/bin/env python3
"""Live market monitor - runs during trading hours.

Connects WebSocket for real-time TSLA/QQQ/SPY prices and
updates snapshot every 5 seconds. Also pulls candles via REST
every 60 seconds for structure calculation.

Usage:
    python3 live_monitor.py          # auto-detect market hours
    python3 live_monitor.py --force  # force start regardless of market hours

Start this when you're actively trading. Stop with Ctrl+C.
"""

import asyncio
import aiohttp
import signal
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from market_service import config
from market_service.websocket_client import PriceMonitor
from market_service.rest_client import fetch_all_candles
from market_service.snapshot_builder import build_snapshot, save_snapshot
from market_service.event_engine import detect_events, save_event


# US Eastern timezone offset (simplified - doesn't handle DST edge cases perfectly)
ET_OFFSET = timedelta(hours=-4)  # EDT


def is_market_open():
    """Check if US stock market is currently open (roughly)."""
    now_utc = datetime.now(timezone.utc)
    now_et = now_utc + ET_OFFSET

    # Weekend check
    if now_et.weekday() >= 5:
        return False

    # Market hours: 9:30 AM - 4:00 PM ET
    market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)

    return market_open <= now_et <= market_close


def is_extended_hours():
    """Check if we're in pre-market or after-hours."""
    now_utc = datetime.now(timezone.utc)
    now_et = now_utc + ET_OFFSET

    if now_et.weekday() >= 5:
        return False

    # Pre-market: 4:00 AM - 9:30 AM ET
    # After-hours: 4:00 PM - 8:00 PM ET
    hour = now_et.hour
    minute = now_et.minute

    pre_market = (4 <= hour < 9) or (hour == 9 and minute < 30)
    after_hours = (16 <= hour < 20)

    return pre_market or after_hours


class LiveMonitor:
    def __init__(self):
        self.price_monitor = PriceMonitor()
        self.candles = {}
        self.prev_snapshot = {}
        self._running = False
        self._snapshot_count = 0

    async def run(self):
        self._running = True

        async with aiohttp.ClientSession() as session:
            # Initial REST pull for candle data
            print("[Live] Pulling initial candle data...")
            self.candles = await fetch_all_candles(session)
            print("[Live] Candles loaded for: {}".format(list(self.candles.keys())))

            # Build initial snapshot
            self._update_snapshot()

            # Run WebSocket + periodic tasks
            print("[Live] Connecting WebSocket...")
            await asyncio.gather(
                self.price_monitor.run(),
                self._snapshot_loop(),
                self._candle_refresh_loop(session),
                self._status_loop(),
            )

    async def _snapshot_loop(self):
        """Rebuild snapshot every 5 seconds with latest WS prices."""
        while self._running:
            await asyncio.sleep(5)
            self._update_snapshot()

    async def _candle_refresh_loop(self, session):
        """Refresh candle data every 60 seconds for structure calculations."""
        while self._running:
            await asyncio.sleep(60)
            try:
                self.candles = await fetch_all_candles(session)
            except Exception as e:
                print("[Live] Candle refresh error: {}".format(e))

    async def _status_loop(self):
        """Print status every 30 seconds."""
        while self._running:
            await asyncio.sleep(30)
            prices = self.price_monitor.get_all_prices()
            tsla = prices.get("TSLA", {})
            price = tsla.get("last_price", "N/A")
            ts = datetime.now().strftime("%H:%M:%S")
            print("[Live] {} | TSLA ${} | snapshots: {}".format(
                ts, price, self._snapshot_count
            ))

    def _update_snapshot(self):
        ws_prices = self.price_monitor.get_all_prices()
        snapshot = build_snapshot(ws_prices, self.candles)
        save_snapshot(snapshot)

        event = detect_events(snapshot, self.prev_snapshot)
        if event:
            save_event(event)
            print("[Event] {} - {}".format(event["event_type"], event["summary"]))

        self.prev_snapshot = snapshot
        self._snapshot_count += 1

    def stop(self):
        self._running = False
        self.price_monitor.stop()


async def main():
    force = "--force" in sys.argv

    if not force and not is_market_open() and not is_extended_hours():
        print("[Live] Market is closed.")
        print("[Live] Use --force to start anyway, or use fetch_now.py for one-shot data.")
        return

    status = "open" if is_market_open() else "extended hours"
    print("[Live] Market status: {}".format(status))
    print("[Live] Starting real-time monitor...")
    print("[Live] Snapshot updates every 5 seconds")
    print("[Live] Press Ctrl+C to stop")
    print()

    monitor = LiveMonitor()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, monitor.stop)

    try:
        await monitor.run()
    except asyncio.CancelledError:
        pass
    finally:
        monitor.stop()
        print("\n[Live] Stopped.")


if __name__ == "__main__":
    asyncio.run(main())
