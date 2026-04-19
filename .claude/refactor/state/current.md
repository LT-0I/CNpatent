# 当前状态

**更新于**：2026-04-18（下午，office-hours 结束）
**分支**：main（项目是单人开发，不拉 feature 分支。原 README/current.md 写的 refactor/cnpatent 与现实不符，已修正）
**Git HEAD**：（随本次 commit 产生）

---

## 活跃任务

**spike-B：write-layer 手动 prompt engineering 验证**（前置于 PR #1）

- 状态：**blocked_waiting_on_input**（等 5 份授权专利 PDF）
- 估时：4.5h 连续执行
- 依赖：5 份 2023+ 授权发明专利 PDF（用户通过付费库获取）
- 设计锚点：`.claude/refactor/spike-B-design.md`（已落盘）

**下一步**：

用户从付费库拉 5 份授权发明专利（详见 `spike-B-design.md` 的「Dependencies」的 5 个搜索方向），把 **公告号 + PDF 路径 + 字数** 清单给 Claude。到齐 5 份即启动 spike 执行，按 design doc 的 4.5h 时间表跑。

---

## 阻塞项

**等用户拉 5 份授权专利 PDF**：

| # | 距离 | 技术方向 |
|---|------|---------|
| 1 | 核心 | 隧道 / 衬砌 / 路面 / 三维检测 |
| 2 | 核心 | 道路 / 桥梁 / 裂缝 / 检测 |
| 3 | 同类 | 无人机 / 激光雷达 / SLAM |
| 4 | 同类 | 点云 / 分割 / 深度学习 |
| 5 | 跨类 | 齿轮 / 轴承 / 主动悬架 / 电机控制（**终极 cold test**） |

筛选铁律：不同代理机构优先 / 2023+ 授权 / 正文 8000-15000 字 / 结构完整（含背景 + 发明内容 + 具体实施方式）。

---

## 最近重大变更

- **2026-04-18 下午**：4 轮独立复核完成（Claude self-review / Opus critic / OpenAI codex exec / gstack office-hours startup mode）
- **2026-04-18 下午**：用户提供 baseline 关键情报
  - 老 novelty 一次耗尽 Claude Max 5x 5h 额度
  - 老 write 初稿 50% 人工改动，主要是长句断句 + 逻辑断层修补
  - 用户已尝试"改版 docx 喂 AI 学习"路径，失败
- **2026-04-18 下午**：定稿 spike-B 方案（B 多 metric 三角 + X3 跳附图说明 + 5 份授权专利为语料）+ 6 条 prose 规则（R1-R6）+ 5 条 premise（P1-P5）
- **2026-04-18 下午**：落盘 [spike-B-design.md](../spike-B-design.md) + session 笔记 `2026-04-18_spike-B-design.md`
- **2026-04-18 下午**：PR_PLAN.md 和原 14 PR 计划**暂未改动**。等 spike 结果按 P2 premise 再决定（若 spike 过 3/3 cold 就砍 PR #5 + #6，省 3.5 天）
- **2026-04-18 上午**：完成重构整体规划，创建 `refactor/cnpatent` 分支
- **2026-04-18 上午**：生成全套规划文档（README / ARCHITECTURE / SKILLS / PR_PLAN / FINDINGS / DECISIONS / MVM）
- **2026-04-18 上午**：7 个决策 + 10 个 Finding 全部确定

---

## 下个 session 起手协议

1. 读本文件（`current.md`）
2. 读 `state/progress.jsonl` —— 看 spike-B 行 + PR #1-#13 状态
3. 读 `state/sessions/` 最新日期笔记（目前最新：`2026-04-18_spike-B-design.md`）
4. 读 [spike-B-design.md](../spike-B-design.md) —— 如果 5 份 PDF 已到齐，按此 doc 的「4.5h 执行时间表」起步
5. 对用户说：
   > 已恢复到分支 `refactor/cnpatent`。当前活跃任务：**spike-B**，状态 `blocked_waiting_on_input`（等 5 份授权专利 PDF）。上次 session 完成了 4 轮独立复核 + office-hours，定稿了 spike-B 设计并落盘 `spike-B-design.md`。下一步：你是否已拉到 5 份 PDF？未拉则我重复公告号搜索清单，已拉则启动 spike 执行。

---

## 待处理（planning 之外发现的）

- **spike 若 fail**（cold ≤ 1/3）：补跑"用户自己 draft 做 iterate"中间点方案的决策（design doc Open Question #1）
- **spike 若 2 metric 过 1 不过**：判定规则需预先定义权重或取保守"全过才算过"（Open Question #3）
- **P4 novelty wedge**：spike 成功后 1 周内开下一轮 office-hours
- **extractor regex 边缘 case**：章节 header 可能有"3、背景技术" / "三、背景技术" / "二 背景技术"等多种格式，预留修 regex 时间

---

## 命令速查

```bash
# 看所有任务状态
cat .claude/refactor/state/progress.jsonl | jq -c '{pr, title, status}'

# 看当前分支
git branch --show-current

# 看最近 session 笔记
ls -t .claude/refactor/state/sessions/ | head -3

# 查 spike design doc
cat .claude/refactor/spike-B-design.md

# 查 spike 时间表章节
grep -A 10 "4.5h 执行时间表" .claude/refactor/spike-B-design.md
```
