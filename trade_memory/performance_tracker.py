"""Performance tracking - measures system accuracy over time."""

import json
from pathlib import Path

JOURNAL_PATH = Path(__file__).parent / "trade_journal.jsonl"


def load_completed_trades():
    """Load all completed trades (EXIT entries) from journal."""
    if not JOURNAL_PATH.exists():
        return []

    trades = []
    with open(JOURNAL_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("type") == "EXIT" and "result" in entry:
                    trades.append(entry)
            except json.JSONDecodeError:
                continue
    return trades


def calc_performance():
    """Calculate overall performance stats.

    Returns a dict with:
        total_trades: number of completed trades
        wins: trades with positive P&L
        losses: trades with negative P&L
        win_rate: wins / total
        avg_pnl_pct: average P&L percentage
        total_pnl_dollar: total dollar P&L
        avg_holding_days: average days held
        thesis_accuracy: how often thesis was correct
        best_trade: highest P&L%
        worst_trade: lowest P&L%
        by_direction: breakdown by PUT vs CALL
    """
    trades = load_completed_trades()

    if not trades:
        return {
            "total_trades": 0,
            "message": "还没有完成的交易记录。",
        }

    results = [t["result"] for t in trades]
    pnls = [r["pnl_pct"] for r in results if r.get("pnl_pct") is not None]
    dollars = [r["pnl_dollar"] for r in results if r.get("pnl_dollar") is not None]
    days = [r["holding_days"] for r in results if r.get("holding_days") is not None]
    thesis_results = [r["thesis_result"] for r in results if r.get("thesis_result")]

    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]

    # Direction breakdown
    by_direction = {"PUT": [], "CALL": []}
    for t in trades:
        side = t.get("trade", {}).get("side", "")
        pnl = t.get("result", {}).get("pnl_pct")
        if side in by_direction and pnl is not None:
            by_direction[side].append(pnl)

    stats = {
        "total_trades": len(trades),
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": round(len(wins) / len(pnls) * 100, 1) if pnls else 0,
        "avg_pnl_pct": round(sum(pnls) / len(pnls), 1) if pnls else 0,
        "total_pnl_dollar": round(sum(dollars), 2) if dollars else 0,
        "avg_holding_days": round(sum(days) / len(days), 1) if days else 0,
        "best_trade": round(max(pnls), 1) if pnls else 0,
        "worst_trade": round(min(pnls), 1) if pnls else 0,
        "thesis_accuracy": {},
        "by_direction": {},
    }

    # Thesis accuracy
    if thesis_results:
        for result in ["correct", "incorrect", "partial", "stopped_out"]:
            count = thesis_results.count(result)
            if count > 0:
                stats["thesis_accuracy"][result] = count

    # Direction breakdown
    for side, pnl_list in by_direction.items():
        if pnl_list:
            side_wins = [p for p in pnl_list if p > 0]
            stats["by_direction"][side] = {
                "trades": len(pnl_list),
                "win_rate": round(len(side_wins) / len(pnl_list) * 100, 1),
                "avg_pnl_pct": round(sum(pnl_list) / len(pnl_list), 1),
            }

    return stats


def format_performance_report(stats):
    """Format performance stats into Chinese readable text."""
    if stats.get("total_trades", 0) == 0:
        return "目前还没有完成的交易记录，无法计算准确度。"

    lines = [
        "交易系统表现统计",
        "=" * 30,
        "",
        "总交易次数: {} 笔".format(stats["total_trades"]),
        "盈利: {} 笔 / 亏损: {} 笔".format(stats["wins"], stats["losses"]),
        "胜率: {}%".format(stats["win_rate"]),
        "",
        "平均收益: {}%".format(stats["avg_pnl_pct"]),
        "累计收益: ${}".format(stats["total_pnl_dollar"]),
        "最佳单笔: +{}%".format(stats["best_trade"]),
        "最差单笔: {}%".format(stats["worst_trade"]),
        "平均持仓: {} 天".format(stats["avg_holding_days"]),
    ]

    if stats.get("thesis_accuracy"):
        lines.append("")
        lines.append("方向判断准确度:")
        for result, count in stats["thesis_accuracy"].items():
            label = {
                "correct": "正确",
                "incorrect": "错误",
                "partial": "部分正确",
                "stopped_out": "止损出场",
            }.get(result, result)
            lines.append("  {}: {} 次".format(label, count))

    if stats.get("by_direction"):
        lines.append("")
        lines.append("按方向分:")
        for side, data in stats["by_direction"].items():
            lines.append("  {}: {} 笔, 胜率 {}%, 平均 {}%".format(
                side, data["trades"], data["win_rate"], data["avg_pnl_pct"]
            ))

    return "\n".join(lines)
