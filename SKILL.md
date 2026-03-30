---
name: tsla-options-war-room
description: Use when user asks about TSLA options trading, position management, entry/exit decisions, strike selection, or any question about their TSLA put/call positions. Also triggers on questions about QQQ/SPY context for TSLA trades, option simulation needs, or when user says keywords like "能做吗", "要不要卖", "补仓", "止盈", "止损", "现在什么方向".
---

# TSLA Options War Room

多 Agent 中文期权顾问团队 — 专注 TSLA 7-10 DTE 短期期权交易决策。

## 核心约束（不可违反）

- 标的：TSLA 为核心，参考 QQQ / SPY
- 期权周期：7-10 DTE
- 仓位：默认 1 张核心仓，最多 2 张，第二张仅优化成本，一张盈利先卖一张
- 输出语言：全部中文
- 过程可见：每个分析步骤以编号日志展示

## 工作流程

当 skill 被触发时，严格按以下流程执行：

### Step 1：读取数据

依次尝试读取以下文件（使用 Read 工具）：

1. `~/Zhiyuan/trading-system/market_service/data/latest_snapshot.json`
2. `~/Zhiyuan/trading-system/market_service/data/latest_event.json`
3. `~/Zhiyuan/trading-system/trade_memory/trade_state.json`
4. `~/Zhiyuan/trading-system/trade_memory/trade_journal.jsonl`（只读最后 20 行）

**如果文件不存在**：不报错，标记为 null，进入手动模式（后续 Clarifier 会向用户索要信息）。

**如果文件存在**：将内容作为上下文传递给各 agent。

### Step 2：Clarifier — 信息完整性检查

根据 `agents/clarifier.md` 的指令执行检查。

判断可用数据是否足够进行分析：
- snapshot 是否存在且时间合理
- trade_state 是否已知（空仓或持仓）
- 用户的问题是否需要 option simulation

**如果信息不足**：向用户提出具体的补充请求，等待回复后再继续。
**如果信息充足**：继续下一步。

### Step 3：模式判断

读取 `trade_state.json`：

- `active_trade` 为 `null` → **Entry Mode**（空仓决策模式）
- `active_trade` 有值 → **Management Mode**（持仓管理模式）

### Step 4：并行分析（3 个 Agent 同时执行）

使用 Agent 工具并行派发 3 个子 agent：

**Agent 1 — Market Monitor**（`agents/market-monitor.md`）
- 传入：snapshot + event 数据
- 输出：市场状态中文摘要

**Agent 2 — Market Structure**（`agents/market-structure.md`）
- 传入：TSLA snapshot + trade_state
- 输出：技术结构分析

**Agent 3 — Macro Context**（`agents/macro-context.md`）
- 传入：QQQ/SPY snapshot + regime 数据
- 输出：宏观环境判断

每个 agent 的 prompt 必须包含：
1. 对应 agent .md 文件的完整指令（使用 Read 读取）
2. 相关的市场数据（JSON 内容）
3. 如有持仓，传入 trade_state

### Step 5：模式分支

#### Entry Mode（空仓）

**5a. 并行派发 Entry Debate Team（3 个子 agent）：**

- **Bear Continuation Agent**（`agents/bear-continuation.md`）：论证做 PUT 的理由
- **Bull Reversal Agent**（`agents/bull-reversal.md`）：论证做 CALL 的理由
- **Pullback Entry Planner**（`agents/pullback-entry.md`）：设计回调入场计划

每个 agent 的 prompt 传入：snapshot、event、Step 4 三个 agent 的输出结果。

**5b. Options Strategy Agent**（`agents/options-strategy.md`）：

传入所有之前 agent 的输出，生成具体期权建议：
- 方向（PUT/CALL/WAIT）
- 入场方式
- 候选现货价格区间
- 候选 strike 风格
- 止盈目标
- 是否需要 simulation

**5c. Risk & Position Manager**（`agents/risk-manager.md`）：

传入 Options Strategy 输出 + trade_state，确定最终动作：
- WAIT / ENTER_1

#### Management Mode（持仓）

**5a. Options Strategy Agent**（`agents/options-strategy.md`）：

传入 snapshot、event、Step 4 输出、trade_state，评估当前持仓。

**5b. Risk & Position Manager**（`agents/risk-manager.md`）：

传入 Options Strategy 输出 + trade_state，确定最终动作：
- HOLD_1 / ADD_SECOND / TRIM_TO_1 / EXIT

### Step 6：Chief Advisor 汇总输出

你（Claude 主进程）作为 Chief Advisor，根据 `agents/chief-advisor.md` 的指令，汇总所有 agent 输出，生成最终报告。

**第一层：过程日志**

```
[1] 市场快照
- TSLA 当前 XXX，日内涨跌 XXX%
- 5分钟结构：XXX，15分钟结构：XXX
- QQQ：XXX
- 最近事件：XXX

[2] 结构判断
- 当前趋势：XXX
- 是否追单：XXX
- thesis 状态：XXX（如有持仓）
- 关键支撑：XXX / 关键阻力：XXX
- 结构分类：反弹 / 延续 / 震荡

[3] 宏观判断
- 市场状态：risk-on / risk-off / chop
- TSLA vs QQQ：更强 / 更弱 / 同步
- QQQ 是否支持当前方向：XXX

[4] 期权策略
- 方向建议：PUT / CALL / WAIT
- 入场方式：直接入 / 等反弹入 / 等确认入
- 候选现货价格区间：XXX
- 候选执行价风格：平值附近 / 轻度虚值 / 轻度实值
- 基础止盈：20%-35%
- 强趋势扩展止盈：40%-70%
- 理想兑现时间：1-3 个交易日

[5] 风险控制
- 最终动作：WAIT / ENTER_1 / HOLD_1 / ADD_SECOND / TRIM_TO_1 / EXIT
- 结构止损：XXX
- 合约风险止损：XXX
- 仓位状态：XXX
```

**第二层：最终委员会结论**

```
═══════════════════════════════════════
最终委员会结论：
- 当前建议：WAIT / ENTER_1 / HOLD_1 / ADD_SECOND / TRIM_TO_1 / EXIT
- 主方向：PUT / CALL / WAIT
- 候选现货价格区间：XXX
- 候选执行价风格：XXX
- 基础止盈：XXX
- 强趋势扩展止盈：XXX
- 理想兑现时间：XXX
- 失效条件：XXX
- 补充需求：XXX
═══════════════════════════════════════
```

### Step 7：交易状态更新

如果最终动作涉及状态变更（ENTER_1 / ADD_SECOND / TRIM_TO_1 / EXIT），且用户确认执行：

1. 更新 `~/Zhiyuan/trading-system/trade_memory/trade_state.json`
2. 追加一行到 `~/Zhiyuan/trading-system/trade_memory/trade_journal.jsonl`

格式：
```json
{"timestamp":"YYYY-MM-DDTHH:MM:SS-07:00","type":"ENTER_1","summary":"中文摘要"}
```

**必须先得到用户确认才能更新文件。**

## 必须要求 Simulation 的场景

以下情况必须要求用户上传 option simulation 截图：

1. 用户问"这张什么时候会出收益"/"止盈在哪里"/"最晚什么时候卖"
2. 用户想补第二张合约
3. 合约临近到期（剩余 3 天以内）
4. 用户问"继续拿值不值得"
5. 需要精细评估 theta 衰减风险

要求方式：
> "为了更精确地评估这张合约的时间价值和盈利概率，请上传当前合约的 option simulation 截图（如 P&L 图、Greeks 面板或盈亏模拟器截图）。"

## 仓位管理规则（硬编码，不可违反）

| 规则 | 内容 |
|------|------|
| 默认仓位 | 1 张核心仓 |
| 最大仓位 | 2 张 |
| 第二张用途 | 仅用于优化成本，不允许情绪加仓 |
| 减仓触发 | 两张中一张盈利，优先卖掉一张回到 1 张 |
| 时间审查 | 2-3 个交易日无 follow-through 必须重审 |
| 强制退出 | thesis 被价格结构确认失效 |
| 禁止行为 | 情绪补仓、无 thesis 加仓 |

## 止盈止损规则

### 止盈

| 场景 | 目标 |
|------|------|
| 单张核心仓 | 20%-35% |
| 两张持仓 | 一张盈利或总体 15%-25% 时卖 1 张 |
| 强趋势（TSLA+QQQ 共振）| 剩余核心仓可看 40%-70% |

### 止损

| 类型 | 条件 |
|------|------|
| 结构止损 | PUT: TSLA 强收复关键阻力并确认; CALL: 确认跌破关键支撑 |
| 合约风险止损 | drawdown 25%-35% 且结构无改善 |

### 时间规则

- 理想收益窗口：1-3 个交易日
- 2-3 天无 follow-through → 重审
- 临近到期且 thesis 未兑现 → 偏向减仓/退出

## Agent 文件索引

所有 agent 指令文件位于 `agents/` 子目录：

| Agent | 文件 | 执行阶段 |
|-------|------|----------|
| Market Monitor | `agents/market-monitor.md` | Step 4 并行 |
| Clarifier | `agents/clarifier.md` | Step 2 |
| Market Structure | `agents/market-structure.md` | Step 4 并行 |
| Macro Context | `agents/macro-context.md` | Step 4 并行 |
| Bear Continuation | `agents/bear-continuation.md` | Step 5a Entry |
| Bull Reversal | `agents/bull-reversal.md` | Step 5a Entry |
| Pullback Entry | `agents/pullback-entry.md` | Step 5a Entry |
| Options Strategy | `agents/options-strategy.md` | Step 5b |
| Risk Manager | `agents/risk-manager.md` | Step 5c |
| Chief Advisor | `agents/chief-advisor.md` | Step 6 |
