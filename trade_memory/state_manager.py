"""Trade state, journal, and lifecycle management."""

import json
from datetime import datetime
from pathlib import Path

STATE_PATH = Path(__file__).parent / "trade_state.json"
JOURNAL_PATH = Path(__file__).parent / "trade_journal.jsonl"


def load_state():
    """Load current trade state."""
    if STATE_PATH.exists():
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"active_trade": None}


def save_state(state):
    """Save trade state to disk."""
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def append_journal(entry):
    """Append a structured entry to the trade journal.

    entry should be a dict with at least 'type' and 'summary'.
    Timestamp is auto-added.
    """
    if "timestamp" not in entry:
        entry["timestamp"] = datetime.now().astimezone().isoformat()
    with open(JOURNAL_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def read_journal(last_n=20):
    """Read the last N journal entries."""
    if not JOURNAL_PATH.exists():
        return []
    with open(JOURNAL_PATH) as f:
        lines = f.readlines()
    entries = []
    for line in lines[-last_n:]:
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def open_trade(side, strike, expiry, avg_cost, thesis, invalidation, contracts=1):
    """Record a new trade entry.

    Called when user confirms ENTER_1.
    Saves to trade_state.json and appends ENTER journal entry.
    """
    trade = {
        "symbol": "TSLA",
        "side": side,
        "strike": strike,
        "expiry": expiry,
        "opened_at": datetime.now().astimezone().isoformat(),
        "contracts": contracts,
        "avg_cost": avg_cost,
        "thesis": thesis,
        "invalidation": invalidation,
        "predictions": {
            "direction": side,
            "target_1": None,
            "target_2": None,
            "stop_loss": None,
            "expected_profit_pct": None,
            "confidence": None,
        },
    }
    save_state({"active_trade": trade})
    append_journal({
        "type": "ENTER_1",
        "side": side,
        "strike": strike,
        "expiry": expiry,
        "contracts": contracts,
        "avg_cost": avg_cost,
        "thesis": thesis,
        "summary": "开仓 {} {} {} PUT/CALL, 成本 ${}/张".format(
            contracts, "TSLA", strike, avg_cost
        ),
    })
    return trade


def add_second(strike, expiry, avg_cost, reason):
    """Record adding a second contract.

    Called when user confirms ADD_SECOND.
    """
    state = load_state()
    if not state.get("active_trade"):
        return None

    state["active_trade"]["contracts"] = 2
    # Update avg_cost to weighted average
    old_cost = state["active_trade"]["avg_cost"]
    state["active_trade"]["avg_cost"] = round((old_cost + avg_cost) / 2, 2)
    state["active_trade"]["second_added_at"] = datetime.now().astimezone().isoformat()
    save_state(state)

    append_journal({
        "type": "ADD_SECOND",
        "strike": strike,
        "avg_cost": avg_cost,
        "reason": reason,
        "summary": "补第二张, strike {}, 成本 ${}/张, 原因: {}".format(
            strike, avg_cost, reason
        ),
    })
    return state["active_trade"]


def trim_to_one(exit_price, reason):
    """Record trimming from 2 contracts to 1.

    Called when user confirms TRIM_TO_1.
    """
    state = load_state()
    if not state.get("active_trade"):
        return None

    state["active_trade"]["contracts"] = 1
    state["active_trade"]["trimmed_at"] = datetime.now().astimezone().isoformat()
    save_state(state)

    append_journal({
        "type": "TRIM_TO_1",
        "exit_price": exit_price,
        "reason": reason,
        "summary": "减仓到1张, 卖出价 ${}, 原因: {}".format(exit_price, reason),
    })
    return state["active_trade"]


def close_trade(exit_price, exit_cost, pnl_pct, pnl_dollar, reason, thesis_result):
    """Record a complete trade exit.

    Called when user provides actual trade results after EXIT.

    Args:
        exit_price: TSLA stock price at exit
        exit_cost: option contract sell price per share
        pnl_pct: actual P&L percentage
        pnl_dollar: actual P&L in dollars
        reason: why the trade was closed
        thesis_result: "correct" / "incorrect" / "partial" / "stopped_out"
    """
    state = load_state()
    trade = state.get("active_trade")
    if not trade:
        return None

    # Build complete trade record
    trade_record = {
        "type": "EXIT",
        "trade": {
            "symbol": trade.get("symbol", "TSLA"),
            "side": trade.get("side"),
            "strike": trade.get("strike"),
            "expiry": trade.get("expiry"),
            "opened_at": trade.get("opened_at"),
            "closed_at": datetime.now().astimezone().isoformat(),
            "contracts": trade.get("contracts"),
            "entry_cost": trade.get("avg_cost"),
            "exit_cost": exit_cost,
            "thesis": trade.get("thesis"),
            "invalidation": trade.get("invalidation"),
        },
        "result": {
            "exit_price_stock": exit_price,
            "pnl_pct": pnl_pct,
            "pnl_dollar": pnl_dollar,
            "reason": reason,
            "thesis_result": thesis_result,
            "holding_days": None,  # calculated below
        },
        "predictions": trade.get("predictions", {}),
        "summary": "平仓 {} {}, P&L {}% (${})，thesis: {}".format(
            trade.get("side"), trade.get("strike"),
            pnl_pct, pnl_dollar, thesis_result
        ),
    }

    # Calculate holding days
    if trade.get("opened_at"):
        try:
            opened = datetime.fromisoformat(trade["opened_at"])
            closed = datetime.now().astimezone()
            trade_record["result"]["holding_days"] = (closed - opened).days
        except (ValueError, TypeError):
            pass

    # Clear active trade
    save_state({"active_trade": None})

    # Write complete record to journal
    append_journal(trade_record)

    return trade_record


def init_empty_state():
    """Initialize empty trade state and journal if they don't exist."""
    if not STATE_PATH.exists():
        save_state({"active_trade": None})
    if not JOURNAL_PATH.exists():
        JOURNAL_PATH.touch()
