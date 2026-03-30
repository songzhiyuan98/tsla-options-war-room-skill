"""Trade state and journal management."""

import json
from datetime import datetime
from pathlib import Path

STATE_PATH = Path(__file__).parent / "trade_state.json"
JOURNAL_PATH = Path(__file__).parent / "trade_journal.jsonl"


def load_state() -> dict:
    """Load current trade state."""
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"active_trade": None}


def save_state(state: dict):
    """Save trade state to disk."""
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def append_journal(entry_type: str, summary: str):
    """Append an entry to the trade journal."""
    entry = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "type": entry_type,
        "summary": summary,
    }
    with open(JOURNAL_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def init_empty_state():
    """Initialize empty trade state and journal if they don't exist."""
    if not STATE_PATH.exists():
        save_state({"active_trade": None})
    if not JOURNAL_PATH.exists():
        JOURNAL_PATH.touch()
