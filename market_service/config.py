import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")

API_KEY = os.getenv("TWELVE_DATA_API_KEY")
BASE_URL = "https://api.twelvedata.com"
WS_URL = "wss://ws.twelvedata.com/v1/quotes/price"

SYMBOLS = ["TSLA", "QQQ", "SPY"]
INTERVALS = ["1min", "5min", "15min"]

# Twelve Data free tier: 8 requests/min, 800/day
REST_POLL_INTERVAL = 60  # seconds between REST pulls
SNAPSHOT_INTERVAL = 30   # seconds between snapshot rebuilds

DATA_DIR = Path(__file__).parent / "data"
SNAPSHOT_PATH = DATA_DIR / "latest_snapshot.json"
EVENT_PATH = DATA_DIR / "latest_event.json"
