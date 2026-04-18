# Session 交接：整体规划完成

- **日期**：2026-04-18
- **Session 类型**：规划
- **持续轮次**：~15 轮对话
- **参与**：用户 + Claude (claude-opus-4-7[1m])
- **分支**：refactor/cnpatent（本 session 末尾新建）
- **产物**：.claude/refactor/ 下全套规划文档

---

## 本 session 做了什么

用户带着一个"cnpatent skill 家族臃肿、改起来补丁叠补丁"的痛点进来。经过多轮讨论，完成了 cnpatent 家族的完整重构规划。

### 讨论主线

1. **首轮方案**（gstack 风格 + 14 skill + kit + corrections.jsonl）
2. **用户 3 大质疑**：
   - 不能过度删除老机制 → 我方案改为 MVM 核验制
   - 查新卡片化一刀切会破新颖性判定 → 加 L2 精读层
   - corrections.jsonl 不足以"永久学会" → 改两层 + 人审晋升
3. **用户补充信息 1**（开发阶段 + PDF 训练循环 + 自动审核）
4. **用户补充信息 2**（docx 模板学习是架构级需求 + 代理人范本为指令型）
5. **用户补充信息 3**（修订模式 + 多模板中间产物）
6. **用户补充信息 4**（跨 session 续跑 + 并行识别 + 学习双把关）

每轮都修订方案。最终产出 10 个 Finding、7 个决策、19 个 skill、14 个 PR。

### 关键设计结晶

- **Strangler Fig 演进**：老 skill 不删，归档保留半年
- **Canonical 内核 + 边界吸收**：中间产物永远用一～六编号
- **两层学习 + 人审晋升**：corrections.jsonl → learned-rules.md（手动）
- **Fingerprint 模板 + 对话式核验**：一个模板一个 build_docx.py
- **三路修订 + 双把关**：tracked + 批注 + chat，user+AI 双决是否学
- **Run 生命周期显式化**：active_run + runs.jsonl + 每 skill 声明契约
- **训练循环延后**：阶段 A 不阻塞阶段 B 的数据攒够

### 决策全清单

| # | 题目 | 选 | 关键补充 |
|---|------|---|---------|
| 1 | consolidate 触发 | A 手动 | 类强化学习：PDF → AI 学习 |
| 2 | 老 skill 退役 | A 保留半年 | 老机制只参考，重写测试 |
| 3 | 训练规模 | B 20 份 | 延后，支持多格式 |
| 4 | extract 审核 | B 自动多轮 | 多循环可以，OCR 文件 |
| 5 | 模板识别兜底 | A 人审 | 对话式 + 样例标签 |
| 6 | 范本严格度 | A 软约束 | study 可选 |
| 7 | revise 解析 | A 三路全解析 | 学习双把关 |

---

## 10 个 Finding 摘要

| # | 级别 | 主题 |
|---|-----|------|
| 1 | P1 | 重构过度革命化 → MVM |
| 2 | P0 | 查新缺精读层 → L1/L2 |
| 3 | P0 | 学习持久化 → 两层 + 人审 |
| 4 | P0 | 测试策略 → training-corpus 即 golden |
| 5 | P0 | 模板耦合 → fingerprint + 一对一 build |
| 6 | P1 | 两类资料 → A 真实/B 指令 |
| 7 | P1 | 修订模式 → 三路合一 |
| 8 | P1 | 多模板中间产物 → canonical 内核 |
| 9 | P0 | Run 生命周期 → active_run + runs.jsonl |
| 10 | P1 | 学习双把关 → user + AI 合取 |

---

## 产出物

- `.claude/refactor/README.md` —— 入口 + 恢复协议
- `.claude/refactor/ARCHITECTURE.md` —— 架构图、目录、数据流
- `.claude/refactor/SKILLS.md` —— 19 个 skill 清单
- `.claude/refactor/PR_PLAN.md` —— 14 个 PR 详细交付
- `.claude/refactor/FINDINGS.md` —— 10 个 Finding
- `.claude/refactor/DECISIONS.md` —— 7 个决策 + 补充
- `.claude/refactor/MVM.md` —— 老机制核验清单
- `.claude/refactor/state/progress.jsonl` —— PR 机器可读状态
- `.claude/refactor/state/current.md` —— 当前活跃状态
- `.claude/refactor/state/sessions/2026-04-18_planning-complete.md` —— 本文件

---

## 下一个 session 应该

**开 PR #1**：
1. 读 current.md 确认状态
2. 读 PR_PLAN.md 的 PR #1 章节
3. 按 `PR #1 交付物` 列表执行
4. 每完成一项自己 review
5. 全部完成后：
   - 更新 MVM.md 里 PR #1 涉及的核验项
   - 更新 progress.jsonl 把 PR #1 标 completed
   - 更新 current.md 指向 PR #2（或并行项）
   - 写本日期的 session 笔记
   - commit

---

## 给未来 session 的叮嘱

1. **不要重开方案讨论**。方案已定。有新信息补 DECISIONS.md / FINDINGS.md 增量。
2. **不要跳 MVM**。老机制引用前先查 MVM 状态。
3. **不要让 AI 自己重写 SKILL.md 学习**。走 corrections.jsonl → consolidate → learned-rules.md。
4. **不要在主 context 跑 writer**。用真 subagent。
5. **不要删老 skill**。归档到 `_legacy/` 保留半年。
6. **不要隐式推断 active_run**。每个 skill 首动作前显式打印。
7. **结束 session 前务必**：更新 current.md、progress.jsonl、写 session 笔记、commit。

---

## 可能出问题的地方

- PR #2 的模板识别是最复杂的单一 PR，可能需要超过 3 天。估时可能低估。
- PR #9 的消融实验可能暴露大量老机制无效，情绪上要接受。
- PR #13 看训练数据何时到位，可能永远延后。
- 跨 session 恢复机制本身需要通过实际使用验证，文档再详尽也不保证实战可用。

---

## 一句话总结

规划阶段完成。接下来是 14 轮 PR 执行。每个 PR 都有明确交付物和验收门禁。每个 session 结束前记得更新状态文件。
