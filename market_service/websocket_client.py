"""WebSocket client for Twelve Data - real-time price updates."""

import json
import asyncio
import websockets
from datetime import datetime
from . import config


class PriceMonitor:
    """Maintains latest prices via Twelve Data WebSocket."""

    def __init__(self):
        self.prices: dict[str, dict] = {}
        self._running = False

    def get_price(self, symbol: str) -> dict:
        return self.prices.get(symbol)

    def get_all_prices(self) -> dict:
        return dict(self.prices)

    async def run(self):
        """Connect to WebSocket and maintain prices. Auto-reconnects."""
        self._running = True
        while self._running:
            try:
                await self._connect()
            except Exception as e:
                print(f"[WS] Connection error: {e}. Reconnecting in 5s...")
                await asyncio.sleep(5)

    async def _connect(self):
        subscribe_msg = {
            "action": "subscribe",
            "params": {
                "symbols": ",".join(config.SYMBOLS)
            }
        }

        async with websockets.connect(
            f"{config.WS_URL}?apikey={config.API_KEY}",
            ping_interval=20,
            ping_timeout=10,
        ) as ws:
            await ws.send(json.dumps(subscribe_msg))
            print(f"[WS] Subscribed to {config.SYMBOLS}")

            async for message in ws:
                try:
                    data = json.loads(message)
                    self._handle_message(data)
                except json.JSONDecodeError:
                    continue

    def _handle_message(self, data: dict):
        if "symbol" not in data or "price" not in data:
            return

        symbol = data["symbol"]
        self.prices[symbol] = {
            "last_price": float(data["price"]),
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "day_volume": int(data.get("day_volume", 0)),
        }

    def stop(self):
        self._running = False
