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
  latest_snapshot.json          <-- 市场快照（保存在本仓库 market_service/data/ 下）
  latest_event.json             <-- 关键事件
         |
         v
  Trade Memory Layer            <-- 交易状态记忆（保存在本仓库 trade_memory/ 下）
  (持仓状态 / 交易日志)
         |
         v
  Claude Skill: War Room        <-- skill 文件安装到 ~/.claude/skills/，运行时读取本仓库的数据
  (方向判断 / 入场规划 / 风控)
         |
         v
  中文交易建议
```

## 工作原理（两个位置）

这个系统涉及两个位置，理解这一点很重要：

**位置 1 -- 本仓库（你 clone 到的地方）**

这是数据和脚本的工作目录。market service 在这里运行，生成的市场快照和交易记录也保存在这里。

```
~/tsla-options-war-room-skill/       <-- 你 clone 到的位置
  market_service/data/               <-- 市场数据写在这里
  trade_memory/                      <-- 交易状态保存在这里
  run.py                             <-- 数据服务从这里启动
```

**位置 2 -- Claude Code skills 目录**

Skill 文件（SKILL.md + agents/）需要复制到 Claude Code 的 skills 目录，这样 Claude 才能识别和加载。

```
~/.claude/skills/tsla-options-war-room/    <-- skill 安装位置
  SKILL.md                                 <-- 主入口
  agents/                                  <-- 10 个 agent 角色定义
```

**两者的关系**：skill 被触发后，会去位置 1（本仓库）读取市场数据和交易状态。如果数据服务没有运行或文件不存在，skill 会自动降级为手动模式（让你提供截图或数据）。

## 核心特点

- **多 Agent 投委会**：10 个精英从业者角色，每个都有完整的专业背景和工作方法
- **对抗式方向判断**：任何涉及 PUT/CALL 方向的问题，内部必须完成多空对抗后才给结论
- **自然对话交互**：像跟一个资深交易顾问聊天，系统内部复杂性对用户完全不可见
- **渐进式展开**：简短问题给简短回答，需要时无缝展开完整报告
- **实时数据驱动**：本地 market service 维护 TSLA/QQQ/SPY 实时数据
- **交易状态记忆**：跨会话记住持仓状态和交易日志

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

### 第一步：Clone 仓库

```bash
# 建议 clone 到 home 目录下（skill 默认读这个路径）
cd ~
git clone https://github.com/songzhiyuan98/tsla-options-war-room-skill.git
cd tsla-options-war-room-skill
```

如果你 clone 到了其他位置，需要修改 `SKILL.md` 中"数据读取"部分的路径。

### 第二步：安装 Skill 到 Claude Code

```bash
# 创建 skill 目录并复制文件
mkdir -p ~/.claude/skills/tsla-options-war-room
cp SKILL.md ~/.claude/skills/tsla-options-war-room/
cp -r agents/ ~/.claude/skills/tsla-options-war-room/
```

安装后 Claude Code 会自动识别这个 skill。

### 第三步：配置数据服务

```bash
# 安装 Python 依赖
pip3 install -r requirements.txt

# 配置 Twelve Data API Key
cp .env.example .env
# 用你喜欢的编辑器打开 .env，填入 API key
# 例如：nano .env
```

Twelve Data 免费版即可，注册地址：https://twelvedata.com/

### 第四步：启动数据服务

```bash
# 在仓库目录下运行
cd ~/tsla-options-war-room-skill
python3 run.py
```

服务会常驻后台，每 60 秒刷新 K 线数据，每 30 秒重建市场快照。终端会显示实时状态：

```
[Service] Starting TSLA Market Service...
[REST] Candles refreshed at 10:15:30
[Snapshot] 10:15:30 | TSLA $355.33 | regime: chop
[Event] near_resistance: TSLA 接近阻力位 $356.86
```

### 第五步：开始使用

在 Claude Code 中提问即可，skill 会自动触发：

```
/tsla-options-war-room TSLA 现在能做期权吗？
```

或者直接问 TSLA 相关问题（不需要 slash command）。

如果数据服务没启动，你也可以手动发截图给 skill 分析。

## 目录结构

```
tsla-options-war-room-skill/
|
|-- SKILL.md                        # 主 Skill 入口（复制到 ~/.claude/skills/）
|-- agents/                         # Agent 角色定义（复制到 ~/.claude/skills/）
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
|-- market_service/                 # 本地市场数据服务（Python，在本仓库运行）
|   |-- config.py                   # 配置
|   |-- websocket_client.py         # Twelve Data WebSocket 实时价格
|   |-- rest_client.py              # Twelve Data REST K线数据
|   |-- structure_calculator.py     # 技术指标计算
|   |-- snapshot_builder.py         # 市场快照构建器
|   |-- event_engine.py             # 关键事件检测引擎
|   |-- service.py                  # 主服务编排
|   |-- data/                       # 运行时生成的数据（gitignored）
|       |-- latest_snapshot.json    # skill 读取这个文件获取市场数据
|       |-- latest_event.json       # skill 读取这个文件获取事件
|
|-- trade_memory/                   # 交易状态（在本仓库保存）
|   |-- state_manager.py            # 状态读写工具
|   |-- trade_state.json            # skill 读写持仓状态（gitignored）
|   |-- trade_journal.jsonl         # skill 追加交易日志（gitignored）
|
|-- schemas/                        # 数据格式示例（供参考）
|-- run.py                          # 数据服务启动入口
|-- requirements.txt                # Python 依赖
|-- .env.example                    # API Key 配置模板
|-- .gitignore                      # 忽略运行时数据和密钥
```

## 数据格式示例

### latest_snapshot.json（market service 自动生成）

```json
{
  "timestamp": "2026-03-30T16:12:04-07:00",
  "symbols": {
    "TSLA": {
      "last_price": 355.33,
      "change_pct": -0.64,
      "trend_5m": "bullish",
      "trend_15m": "bearish",
      "support": [352.14, 352.24],
      "resistance": [356.86, 356.39],
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

### trade_state.json（skill 读写）

```json
{ "active_trade": null }
```

有持仓时：

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

## 自定义路径

如果你没有把仓库 clone 到 `~/tsla-options-war-room-skill/`，需要修改 SKILL.md 中的数据路径。

打开 `~/.claude/skills/tsla-options-war-room/SKILL.md`，找到"数据读取"部分，把路径改成你的实际位置。

## 注意事项

- 本系统仅供学习和研究用途，不构成投资建议
- 期权交易有重大亏损风险，请在充分了解风险后谨慎操作
- 系统的分析基于技术面数据，不考虑基本面和突发事件
- 建议在模拟账户中测试后再用于实盘
- Twelve Data 免费版有请求限制（800/天，8/分钟），正常使用足够
