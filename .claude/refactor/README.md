# cnpatent 重构计划

本目录是 cnpatent skill 家族（cnpatent / cnpatent-humanizer / cnpatent-noveltycheck）重构项目的完整规划与进度跟踪。

重构采用 **gstack 风格**：多个窄职责 skill、明确触发、评分门禁、阶段隔离、薄编排层。

---

## 若你是新会话，按以下顺序恢复上下文

**Step 1**：读 `state/current.md` → 最新状态和下一步  
**Step 2**：读 `state/progress.jsonl` → 每个 PR 的完成度  
**Step 3**：读 `state/sessions/` 下最新日期的 session 笔记 → 上一轮做了什么、说了什么  
**Step 4**：根据 `state/current.md` 指向的当前 PR，读 `PR_PLAN.md` 对应章节

然后对用户说：

> 已恢复。当前 PR #X: "<PR 标题>"，状态 <状态>。上次 session 做了：<一句话摘要>。下一步：<具体动作>。继续吗？

**不要在读完状态前贸然开工**。用户可能已经在别处改动了代码或决策。

---

## 文档总览

| 文件 | 内容 | 何时读 |
|------|------|-------|
| `README.md`（本文件） | 入口 + 恢复协议 | **每次进入先读** |
| `ARCHITECTURE.md` | 架构图、目录结构、数据流、设计原则 | 开任何 PR 前 |
| `SKILLS.md` | 19 个 skill 清单 + 职责 + 依赖 | 动 skill 文件前 |
| `PR_PLAN.md` | 14 个 PR 顺序 + 交付物 + 依赖 + 估时 | 挑下一个 PR 时 |
| `FINDINGS.md` | 10 个评审发现 + 修订方向 | 想了解设计动机 |
| `DECISIONS.md` | 用户决策 1-7 + rationale + 补充 | 拿捏设计偏向时 |
| `MVM.md` | 老机制核验清单 | PR #7 / #8 / #9 前 |

## 状态文件

| 文件 | 内容 | 谁写 |
|------|------|------|
| `state/current.md` | 当前 PR + 阻塞 + 下一步 + 最近变更 | 每个 session 结束前更新 |
| `state/progress.jsonl` | PR 机器可读状态，一行一 PR | PR 状态变化时追加/更新 |
| `state/sessions/YYYY-MM-DD_<topic>.md` | 每个 session 的交接笔记 | session 结束写一份 |

---

## 会话结束前必做（Exit Protocol）

**不做这四步，下个 session 就接不上**：

1. 更新 `state/current.md` —— active PR、阻塞、下一步、本次 session 改了什么
2. 若 PR 状态变了，更新 `state/progress.jsonl`（改对应行的 status 字段）
3. 写 `state/sessions/<date>_<topic>.md` —— 交接笔记，下个 session 的你会感谢你
4. `git commit` 这些变更（和当轮代码变更一起）

---

## 刚性规则（不可跨越）

- **不删老 skill**：三个老 skill 只归档到 `.claude/skills/_legacy/`，保留半年参考
- **先核验、后采纳**：任何引用老机制的地方必须先查 `MVM.md` 对应条目，通过核验才能复用
- **不手工改 SKILL.md 让 AI 去适配**：学到的规则走 `corrections.jsonl → /cnpatent-consolidate → learned-rules.md` 路径
- **canonical 内核不可变**：中间产物永远用 canonical 章节编号（一、二、三、四、五、六），模板差异在 boundary 吸收
- **决策必须留痕**：任何新决策加入 `DECISIONS.md`，带选项、选择、rationale
- **不跳门禁**：每个 PR 定义了 gate（测试/评分/回归），不过不能进下一个

---

## 快速索引（常用场景）

- 刚开工 → `state/current.md` + `PR_PLAN.md` 的对应 PR 章节
- 想了解为什么这么设计 → `FINDINGS.md`
- 改 skill 时不确定要不要保留某个老逻辑 → `MVM.md`
- 发现方案有矛盾 → `DECISIONS.md` 找历史决策
- 一个新 skill 要做什么 → `SKILLS.md`
- 调整 PR 顺序或范围 → `PR_PLAN.md`（改完同步更新 `state/progress.jsonl`）

---

## 重构项目自身的三种使用形态

这套文档也用了我们为 cnpatent 设计的同一套续跑机制：

**形态 1：连续推进**
一个人一个 session 跑一个 PR，结束前更新状态文件，下次继续。

**形态 2：跨 session 断点续跑**
session A 做到 PR #3 一半，隔几天回来。新 session 读 state/ 就知道恢复到哪。

**形态 3：多人协作 / 并行 PR**
两个人分别拉 PR #5 和 PR #8（互不依赖）。各自分支，各自更新自己的 PR 进度。merge 回主线时手动合并 progress.jsonl。
