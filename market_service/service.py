"""Main market service - orchestrates WS, REST, snapshot, and events."""

import asyncio
import signal
import aiohttp
from datetime import datetime

from . import config
from .websocket_client import PriceMonitor
from .rest_client import fetch_all_candles
from .snapshot_builder import build_snapshot, save_snapshot
from .event_engine import detect_events, save_event


class MarketService:
    """Background service that maintains market data for TSLA War Room."""

    def __init__(self):
        self.price_monitor = PriceMonitor()
        self.candles: dict = {}
        self.latest_snapshot: dict = {}
        self._running = False

    async def run(self):
        """Start all service components."""
        self._running = True
        print(f"[Service] Starting TSLA Market Service...")
        print(f"[Service] Symbols: {config.SYMBOLS}")
        print(f"[Service] REST poll: every {config.REST_POLL_INTERVAL}s")
        print(f"[Service] Snapshot rebuild: every {config.SNAPSHOT_INTERVAL}s")
        print(f"[Service] Data dir: {config.DATA_DIR}")

        async with aiohttp.ClientSession() as session:
            # Initial REST pull
            print("[Service] Pulling initial candle data...")
            self.candles = await fetch_all_candles(session)
            print(f"[Service] Got candles for: {list(self.candles.keys())}")

            # Build initial snapshot
            self._rebuild_snapshot()

            # Run all tasks concurrently
            await asyncio.gather(
                self.price_monitor.run(),
                self._rest_poll_loop(session),
                self._snapshot_loop(),
            )

    async def _rest_poll_loop(self, session: aiohttp.ClientSession):
        """Periodically refresh candle data via REST."""
        while self._running:
            await asyncio.sleep(config.REST_POLL_INTERVAL)
            try:
                self.candles = await fetch_all_candles(session)
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[REST] Candles refreshed at {ts}")
            except Exception as e:
                print(f"[REST] Poll error: {e}")

    async def _snapshot_loop(self):
        """Periodically rebuild and save snapshot."""
        while self._running:
            await asyncio.sleep(config.SNAPSHOT_INTERVAL)
            self._rebuild_snapshot()

    def _rebuild_snapshot(self):
        """Build snapshot from current data and save to disk."""
        ws_prices = self.price_monitor.get_all_prices()
        snapshot = build_snapshot(ws_prices, self.candles)
        save_snapshot(snapshot)

        # Detect and save events
        event = detect_events(snapshot, self.latest_snapshot)
        if event:
            save_event(event)
            print(f"[Event] {event['event_type']}: {event['summary']}")

        self.latest_snapshot = snapshot

        tsla = snapshot.get("symbols", {}).get("TSLA", {})
        price = tsla.get("last_price", "N/A")
        regime = snapshot.get("regime", {}).get("market_regime", "N/A")
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[Snapshot] {ts} | TSLA ${price} | regime: {regime}")

    def stop(self):
        self._running = False
        self.price_monitor.stop()


async def main():
    service = MarketService()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, service.stop)

    try:
        await service.run()
    except asyncio.CancelledError:
        pass
    finally:
        service.stop()
        print("[Service] Stopped.")


if __name__ == "__main__":
    asyncio.run(main())
