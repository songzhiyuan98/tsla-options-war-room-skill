# TSLA Options War Room

一个基于 Claude Code 的 TSLA 短期期权交易决策系统。

由本地市场数据服务提供实时盘面，由交易状态层保存上下文，由中文多 Agent 顾问团队负责方向判断、入场规划、期权选择、止盈止损和持仓管理。

## 系统架构

```
Twelve Data API (WebSocket + REST)
         |
         v
  Local Market Service          <-- 后台常驻，维护实时数据
  (价格监控 / K线拉取 / 结构计算 / 事件检测)
         |
         v
  latest_snapshot.json          <-- 市场快照
  latest_event.json             <-- 关键事件
         |
         v
  Trade Memory Layer            <-- 交易状态记忆
  (持仓状态 / 交易日志)
         |
         v
  Claude Skill: War Room        <-- 多 Agent 期权顾问团队
  (方向判断 / 入场规划 / 风控)
         |
         v
  中文交易建议
```

## 核心特点

- **多 Agent 投委会**：10 个精英从业者角色（结构分析师、宏观顾问、多空辩论、期权策略、风控主管等），每个都有完整的专业背景和工作方法
- **对抗式方向判断**：任何涉及 PUT/CALL 方向的问题，内部必须完成多空对抗分析后才给结论
- **自然对话交互**：像跟一个资深交易顾问聊天，不像在读分析报告。系统内部复杂性对用户完全不可见
- **渐进式展开**：简短问题给简短回答，需要深度分析时无缝展开完整报告
- **实时数据驱动**：本地 market service 维护 TSLA/QQQ/SPY 实时数据，skill 自动读取
- **交易状态记忆**：跨会话记住持仓状态、交易日志，支持连续持仓管理

## 交易参数

| 参数 | 设定 |
|------|------|
| 标的 | TSLA（参考 QQQ / SPY） |
| 期权周期 | 7-10 DTE |
| 默认仓位 | 1 张核心仓 |
| 最大仓位 | 2 张 |
| 基础止盈 | 20%-35% |
| 强趋势止盈 | 40%-70% |
| 止损 | 结构止损 + 合约风险止损（25%-35%） |

## 快速开始

### 1. 安装 Skill

将 `SKILL.md` 和 `agents/` 目录复制到你的 Claude Code skills 目录：

```bash
cp -r SKILL.md agents/ ~/.claude/skills/tsla-options-war-room/
```

### 2. 配置数据服务

```bash
# 安装依赖
pip3 install -r requirements.txt

# 配置 API Key（需要 Twelve Data 账号，免费版即可）
cp .env.example .env
# 编辑 .env，填入你的 API key
```

### 3. 启动 Market Service

```bash
python3 run.py
```

服务会在后台运行，每 60 秒刷新 K 线数据，每 30 秒重建市场快照。盘中还会通过 WebSocket 接收实时价格。

### 4. 使用 Skill

在 Claude Code 中直接提问：

```
/tsla-options-war-room TSLA 现在能做期权吗？
```

或者直接问 TSLA 相关问题，skill 会自动触发。

如果 market service 没有运行，也可以手动提供截图或数据。

## 目录结构

```
tsla-options-war-room-skill/
|
|-- SKILL.md                        # 主 Skill 入口（交互控制 + 工作流程 + 规则）
|-- agents/                         # 10 个 Agent 角色定义
|   |-- market-monitor.md           # 资深盘中市场情报员
|   |-- clarifier.md                # 资深买方研究协调员
|   |-- market-structure.md         # 高级技术结构分析师
|   |-- macro-context.md            # 宏观 Beta 风险顾问
|   |-- bear-continuation.md        # 看空趋势交易主管
|   |-- bull-reversal.md            # 反弹与反转机会交易员
|   |-- pullback-entry.md           # 交易执行规划师
|   |-- options-strategy.md         # 短期期权结构顾问
|   |-- risk-manager.md             # 交易风控主管
|   |-- chief-advisor.md            # 首席投资顾问 / 委员会主席
|
|-- market_service/                 # 本地市场数据服务（Python）
|   |-- config.py                   # 配置（API key、轮询间隔、文件路径）
|   |-- websocket_client.py         # Twelve Data WebSocket 实时价格
|   |-- rest_client.py              # Twelve Data REST K线数据
|   |-- structure_calculator.py     # 技术指标计算（趋势/支撑阻力/VWAP/ATR/RVOL）
|   |-- snapshot_builder.py         # 市场快照构建器
|   |-- event_engine.py             # 关键事件检测引擎
|   |-- service.py                  # 主服务编排（WS + REST + 快照 + 事件）
|   |-- data/                       # 运行时数据（gitignored）
|       |-- latest_snapshot.json    # 最新市场快照
|       |-- latest_event.json       # 最新检测事件
|
|-- trade_memory/                   # 交易状态记忆层
|   |-- state_manager.py            # 状态读写工具
|   |-- trade_state.json            # 当前持仓状态（gitignored）
|   |-- trade_journal.jsonl         # 交易日志（gitignored）
|
|-- schemas/                        # 数据格式示例
|   |-- snapshot-sample.json
|   |-- event-sample.json
|   |-- trade-state-sample.json
|
|-- run.py                          # 服务启动入口
|-- requirements.txt                # Python 依赖
|-- .env.example                    # API Key 配置模板
```

## 数据格式

### latest_snapshot.json

```json
{
  "timestamp": "2026-03-30T16:12:04-07:00",
  "symbols": {
    "TSLA": {
      "last_price": 355.33,
      "change_pct": -0.64,
      "intraday_high": 355.64,
      "intraday_low": 352.14,
      "trend_1m": "neutral",
      "trend_5m": "bullish",
      "trend_15m": "bearish",
      "support": [352.14, 352.24, 352.39],
      "resistance": [356.86, 356.39, 356.2],
      "vwap": 353.94,
      "atr_5m": 0.89,
      "rvol": 3.71
    },
    "QQQ": { "last_price": 558.27, "trend_5m": "bullish", "trend_15m": "bearish" },
    "SPY": { "last_price": 632.0, "trend_5m": "bullish" }
  },
  "regime": { "market_regime": "chop", "tsla_relative_strength_vs_qqq": "neutral" }
}
```

### trade_state.json

```json
{
  "active_trade": {
    "symbol": "TSLA",
    "side": "PUT",
    "strike": 350,
    "expiry": "2026-04-10",
    "contracts": 1,
    "avg_cost": 6.5,
    "thesis": "周线下跌加速，等反弹到 360 做空",
    "invalidation": "TSLA 站稳 365 以上"
  }
}
```

空仓时 `active_trade` 为 `null`。

## Twelve Data API

本项目使用 [Twelve Data](https://twelvedata.com/) 作为市场数据源。

免费版支持：
- WebSocket 实时价格（1 连接）
- REST API（800 请求/天，8 请求/分钟）

注册后在 Dashboard 获取 API Key，填入 `.env` 文件即可。

## 注意事项

- 本系统仅供学习和研究用途，不构成投资建议
- 期权交易有重大亏损风险，请在充分了解风险后谨慎操作
- 系统的分析基于技术面数据，不考虑基本面和突发事件
- 建议在模拟账户中测试后再用于实盘
