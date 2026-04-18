# Session 交接：计划复核

- **日期**：2026-04-18（晚于 `2026-04-18_planning-complete.md`）
- **Session 类型**：复核（plan-eng-review）
- **分支**：refactor/cnpatent
- **前置 commit**：8d93359（规划提交）
- **产物**：4 处 typo 修正 + 本笔记 + current.md "最近重大变更"追加

---

## 本 session 做了什么

用户要求"使用相关 skill 检查已生成的计划，是否符合讨论结果，不符合的地方进行修正"。

对 10 个文件对照讨论 summary 逐项核对：
- 7 个决策（D1A–D7A）+ 补充 A–E：**全部成文** ✓
- 10 个 Finding（5 P0 + 5 P1）：**全部成文** ✓
- 8 条设计原则、三阶段、目录结构、数据流、Run 生命周期、两层学习、并发锁：**全部成文** ✓
- 续跑机制（README 恢复协议 + exit 协议 + current.md + progress.jsonl + session 笔记）：**齐备** ✓

### 修正的不一致项（均为计数 typo，不动设计）

| 位置 | 原 | 改 | 理由 |
|------|----|----|-----|
| SKILLS.md L1 | `19 个主 + 1 个延后` | `22 个主 + 1 个延后` | 分组 3+2+5+1+4+3+2+2=22 |
| README.md L30 | `19 个 skill` | `22 个主 skill + 1 延后` | 同上 |
| README.md L31 | `14 个 PR` | `13 个主 PR + 1 延后` | 准确化 |
| ARCHITECTURE.md L92 | `17 个 phase skills` | `22 个 phase skills（+ 1 延后）` | 目录实际展开 22 项 |
| PR_PLAN.md L3 | `14 个主 PR + 1 个延后 PR` | `13 个主 PR（含 #6b）+ 1 个延后 PR` 合计 14 | 主 PR 含 #6b 是 13 |

### 未修的观察（未达错误级别，记录备查）

1. **PR_PLAN.md L3 估时语义**：原文"17.5 工作日"作为串行总和时数学上对不上（纯相加 20.5 天）。已在改写中加注"天然并行机会已吸收"说明。真正数值在 PR 执行中再校准。
2. **MVM.md L196 统计**："免核验：5 项" 与机制表 3 项 + 资产表 3 项的划分方式不完全一致。不影响执行（每项自身状态都明确），开 PR #1 时顺手重算。
3. **current.md L5 Git HEAD**：仍为 `（待首次 commit 后填入）`。原计划即是 "PR #1 开始时顺手改为 8d93359"。保留占位。

### 再次确认讨论中明确过的硬约束

- 老 3 skill 仅参考价值，重构时**不预设正确**，每项走 MVM 核验（决策 2A 补充）
- `corrections.jsonl` 单独不够"永久学会"，必须走两层 + 人审晋升（Finding 3）
- 模板学习**固化为 build_docx.py** 每模板一份（Finding 5 + 决策 5A）
- 代理人范本是**指令型**文档，不是 ground truth（Finding 6）
- 修订三路全解（Finding 7），每条带 `user_learn + ai_learn_propose + decision` 合取（Finding 10）
- 多模板 canonical 内核不动，**模板差异只在 template-setup + build 两个边界吸收**（Finding 8）
- 多 run：`.cnpatent/active_run` + `.cnpatent/runs.jsonl` + 每 skill 首动作声明契约（Finding 9）

全部落到文档，未漏。

---

## 下一个 session 应该

与前一 session 尾部一致：**开 PR #1**。

read 顺序：
1. `state/current.md`（本次已更新）
2. `state/progress.jsonl`（未变）
3. 本 session 笔记（本文件）
4. 最早规划笔记 `2026-04-18_planning-complete.md`（设计动机备查）
5. `PR_PLAN.md` 的 `PR #1` 章节

起手一句推荐：
> 已恢复到分支 `refactor/cnpatent`。当前 PR #1：kit 骨架 + MVM + schemas + run 基础设施。上次 session 复核了计划，修正了 4 处计数 typo，设计未动。下一步：按 PR #1 交付清单开工。继续吗？

---

## 给未来 session 的叮嘱（与前一 session 同，此处精简）

1. 不重开方案讨论。10 个 Finding + 7 个决策已封板。
2. 不跳 MVM。老机制引用前查 MVM 状态。
3. 不让 AI 重写 SKILL.md 学习。走 corrections → consolidate → learned-rules。
4. 不在主 context 跑 writer。用真 subagent。
5. 不删老 skill。归档 `_legacy/` 保留半年。
6. 不隐式推断 active_run。首动作前显式打印。
7. 结束前：更新 current.md + progress.jsonl + 写 session 笔记 + commit。

---

## 一句话总结

计划与讨论结果一致。修了 4 处计数 typo，设计面 zero drift。下个 session 按原计划开 PR #1。
