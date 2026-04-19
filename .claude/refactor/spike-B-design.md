# Design: cnpatent write-layer spike B

- **Date**: 2026-04-18
- **Branch**: refactor/cnpatent
- **Mode**: Intrapreneurship（内部专利写作工具）
- **Status**: APPROVED
- **Scope**: 验证能否用手动 prompt engineering + shared voice 前缀，将 AI write 输出与授权专利 gold 的句级 diff 降至 < 5%
- **执行窗口**: 4.5h，一个下午
- **上游**: 本 spike 为 PR_PLAN.md 原 14 PR 方案的前置验证，不替换主计划
- **经过**: 四轮独立复核（Claude self-review / Opus critic / OpenAI codex / gstack office-hours）后定稿

---

## Problem Statement

老 `cnpatent` skill 家族的 write 子系统输出 AI 味重，具体表现：

- 句子过长、逗号过少、用句号断开紧密因果链
- 段落内逻辑断层，读者需脑补连接关系
- 在背景技术 / 发明内容两段尤为突出
- 用户已尝试"改版 docx 喂回 AI 让它 in-context 学习"，**失败**

该失败经验直接证伪"AI 看示例即可自行学会 prose 规则"这一假设，同时给原 refactor 计划的 `corrections.jsonl → learned-rules.md` 学习回路架构提高了验证门槛。

---

## Status Quo Baseline

来自 Q2 回答：

| 维度 | 数值 |
|---|---|
| 单份专利总耗时 | ~140 min（idea 45 + AI 写 45 + 人工改 50） |
| AI 跑 vs 人工改（定稿阶段） | ≈ 1 : 1 |
| 老 novelty 一次 token 消耗 | 耗尽 Claude Max 5x 账号 5h 额度 |
| 老 write 初稿人工改动 | ~50%，主要为长句拆分 + 逻辑断层修补 |
| 已有真实产出 | 隧道路面三维检测 + 无人机 SLAM 激光惯性里程计 共 2 份 draft |

---

## Target & Narrowest Wedge

- **Target user** = 本人（intrapreneurship），自写、自用、自改
- **Wedge** = 手动 prompt engineering，4 份 section prompt + 共享 `patent-voice.md` 前缀 + 3 metric 三角验证
- **不做**：corrections.jsonl → learned-rules.md 学习回路；对话式模板核验；全套 22 skill 拆分；附图说明处理；novelty token 优化

---

## Constraints

- 执行时长 4.5h 上限
- 5 份授权发明专利 PDF 由用户通过付费库获取
- 一人操作，无多人协作
- 输出风格 = 代理人定版风格（授权版本），**非**用户个人 draft 风格
- Windows + bash，Python 3

---

## Premises（已确认）

- **P1** narrowest wedge = 手动 prompt engineering，不走学习回路
- **P2** B spike 冷测 3/3 cold 通过 → 砍 PR #5 + #6（learn + consolidate + revise 双把关），省 3.5 天
- **P3** canonical 章节按用户 4 分法（发明名称+技术领域 / 背景技术 / 发明内容 / 具体实施方式），附图说明 spike 阶段跳过
- **P4** novelty token 爆炸（Max 5x 5h 耗尽）是 B 成功后的下一轮 wedge，本轮不做
- **P5** 付费库 5 份授权专利仅作 iterate / holdout 语料，不写入 corrections.jsonl（避免风格污染）

---

## Prose 规则（shared voice 前缀内容）

来自对用户 Q5 原句 diff（隧道路面"架构缺反馈"段）提炼的 6 条可执行规则：

- **R1** 因果 / 条件 / 递进关系必须有显式连接词（当...时、因而、由于、使得、进而、从而）。禁止连续两个句号陈述同一因果链
- **R2** 同一实体相邻第二次出现用代词（后者 / 前者 / 该 / 此），禁止复述全称
- **R3** 两个 < 30 字、逻辑紧密的短句合并成复句（逗号连接）
- **R4** 话题切换时显式标记（后者 / 此时）
- **R5** 并列概念顺序服务于下文代词指向
- **R6** 长距离因果链（输入 → 机制 → 失败模式）在同一复句内完成

六条全部进 `patent-voice.md` 共享前缀，section prompt 不动，write 时全局生效。

---

## Approaches Considered

### A. 最小可跑

- 单 metric：句级 difflib ratio
- 2 iterate + 3 cold holdout
- 2-3h
- **Pros**：最快，贴用户原始时间约束
- **Cons**：失败时不知归因在 prose 层还是 structure 层

### B. 多 metric 三角（✅ 选）

- 3 metric：句级 diff + 段落句长分布 KL + 连接词密度
- 2 iterate + 3 cold holdout
- 4.5h（含 extractor）
- **Pros**：失败可归因到具体层；诊断能力强
- **Cons**：多 1.5h

### C. 横向盲评

- A/B blind 人工评 cold 哪版更像 gold
- 3h
- **Pros**：最贴"用户改不改得动稿"的真实指标
- **Cons**：主观、不可复现、无 delta 数据

### Cross-Model Perspective

四轮复核已覆盖：

- **Claude self-review**：识别出 10 个自身方案问题，其中 /qa 误用、/team 并行错、/learner 越权反写三条最重
- **Opus critic**：加 MVM 节奏错配、golden test 基础设施缺失、工作流过度工具化、gstack 九成 skill 不适配四条结构盲区
- **OpenAI codex**：挑战根本前提（canonical 不可变、先拆后验），建议 6 天 spike 替代 17.5 天重构
- **gstack office-hours**：在 codex 基础上进一步窄到 4.5h 单轮 spike，由用户提供 baseline 数据 + 付费库访问而成立

---

## Recommended Approach：B + 前置 extractor + X3

### 组件

**1. Mini-extractor**（前置，spike 专用最小版）

- 输入：5 份授权专利 PDF
- 实现：PyMuPDF 读全文 + 正则匹配章节头切块
- 输出：5 份 markdown，每份含发明名称 + 技术领域 + 背景技术 + 发明内容 + 具体实施方式
- **删**：说明书摘要、附图说明、权利要求书、附图图片
- 代码量：~50 行 Python
- **不是**完整 PR #4 的 ref-extract，只是 spike 够用的最小版

**2. Shared voice 前缀**

- 文件：`patent-voice.md`
- 内容：R1-R6 六条 prose 规则
- 加载：4 个 section writer 启动时统一读取

**3. 4 份 section prompt**

| 文件 | 负责 section |
|---|---|
| `writer-name-field.md` | 发明名称 + 技术领域 |
| `writer-background.md` | 背景技术 |
| `writer-invention.md` | 发明内容（目的 + 方案 + 效果） |
| `writer-implementation.md` | 具体实施方式 |

每份 prompt = 共享 voice 前缀 + 本 section 特有结构 / 内容要求。附图说明按 X3 决策**跳过**。

**4. 3 metric 脚本**

| metric | 实现 |
|---|---|
| 句级 diff | `difflib.SequenceMatcher` ratio。句子 = 中文句号 / 问号 / 感叹号切分 |
| 段落句长分布 KL | gold vs new 的段落内句长 histogram KL 散度 |
| 连接词密度 | 每千字"当 / 因而 / 由于 / 使得 / 进而 / 从而 / 以..."等显式连接词计数 |

### 样本切分

| 角色 | 份数 | 是哪份 |
|---|---|---|
| Iterate | 2 | 核心 1（#1 隧道 / 路面 / 三维）+ 同类 1（#3 无人机 / SLAM） |
| Cold holdout | 3 | 核心 2（#2 道路 / 裂缝）+ 同类 2（#4 点云 / 深度学习）+ 跨类（#5 机械 / 传感器） |

### Pass Bar

- **完全胜**：cold 3/3 全部三 metric 达阈值 → 砍 PR #5 + #6
- **半胜**：cold 2/3（跨类 #5 允许偏差，单独记录跨类 delta） → 需追加 iterate 样本或补学习回路
- **败**：cold ≤ 1/3 → 回归 refactor 原计划，上 corrections → learned-rules 架构

---

## 4.5h 执行时间表

| 时段 | 动作 |
|---|---|
| 0-45 min | mini-extractor（PyMuPDF + 正则）+ 单份 PDF 验证 section 切分 |
| 45-60 min | 批跑 5 份 PDF + 人工 QA，修正 regex 边缘 case |
| 60-90 min | 写 `patent-voice.md`（R1-R6）+ 4 份 section prompt 骨架 + 3 metric 脚本 |
| 90-180 min | iterate：核心 1 + 同类 1 两份，每次改 prompt 后重算 3 metric 至阈值内 |
| 180-240 min | cold holdout 3 份一次跑，算 3 metric |
| 240-270 min | spike report：哪份过 / 没过 / 失败归因（prose 层 or structure 层） |

---

## Success Criteria

- **过**：cold 3/3 三 metric 均通过 → B 胜，砍 PR #5 + #6，省 3.5 天
- **降级**：cold 2/3（跨类 #5 允许偏差）→ B 半胜，记录跨类 delta，iterate 样本扩充
- **fail**：cold ≤ 1/3 → 手动 prompt engineering 到顶，回归原 refactor 计划 PR #5 + #6

---

## Open Questions

1. Spike 失败（cold ≤ 1/3）时，是否需补跑一份"用户自己 draft 做 iterate" 版本，作为"个人风格 vs 代理人风格"的中间点数据？
2. P4 承诺"B 成功后开 novelty wedge"的单独 office-hours 轮次什么时候做？建议 spike 后 1 周内
3. 若 3 metric 中 2 过 1 不过（例如连接词密度达标但段落句长 KL 偏差大），怎么判定？需预先定义 metric 权重或取"全过才算过"的保守策略
4. mini-extractor 正则可能遇到"3、背景技术" / "三、背景技术" / "二 背景技术" / "Background Technology" 等多种 header 格式。预留修 regex 时间在 45-60 min 槽位内

---

## Distribution Plan

N/A。本项目为用户个人使用工具，不对外分发。

生产物在本地 `.claude/refactor/spike-B/`：

- `patent-voice.md`（6 条规则）
- `prompts/writer-*.md`（4 份 section prompt）
- `extractor.py`（mini-extractor）
- `metrics.py`（3 个 metric 脚本）
- `gold/`（5 份 extracted markdown）
- `iter_logs/`（每次 iterate 的 prompt diff + metric 快照）
- `cold_results.md`（spike report）

---

## Dependencies

- **阻塞**：5 份 2023 年后授权发明专利 PDF（公告号 + 原文），用户通过付费库获取
  - #1 核心：隧道 / 衬砌 / 路面 / 三维检测
  - #2 核心：道路 / 桥梁 / 裂缝 / 检测
  - #3 同类：无人机 / 激光雷达 / SLAM
  - #4 同类：点云 / 分割 / 深度学习
  - #5 跨类：齿轮 / 轴承 / 主动悬架 / 电机控制
  - **筛选铁律**：不同代理机构优先；正文 8000-15000 字；结构完整（含背景 / 发明内容 / 具体实施方式）
- **运行环境**：Python 3、PyMuPDF（pip install pymupdf）、difflib（内置）、numpy
- **时间窗**：约 5h 连续可用

---

## The Assignment

**拉 5 份授权专利 PDF 并给出公告号清单。**

- 优先不同代理机构（避免 iterate 集与 cold 集同风格）
- 2023 年后授权（法条口径稳定）
- 正文 8000-15000 字（结构完整，噪声少）

到齐 5 份才启动 spike。**这是唯一的前置阻塞项，用户侧动作，spike 不能代办。**

---

## What I noticed about how you think

- 你 Q2 第 4 点说"老 write 的毛病是长句少逗号 + 逻辑断层"，多数人停在"AI 味重"的泛泛表述，你一上来点到句读和段落级别
- 你 Q4 把我原设计的"5 天 spike"直接压成"2-3h 立马做"，并给出具体 4 section 切分 + 5% 验证指标。这不是含糊的"快点做"，是把粒度降到一天内的动作级
- 你没等我问 metric 定义就自己提出"用户修改部分小于 5%"，表明你已经在头脑里跑过"怎么知道成功"
- "我改了很多遍 docx 发给 AI 叫它学习、总是调教不好它"这句，你主动承认了一个核心架构假设的失败，比多数人被问"有什么不 work"时的回答诚实
- "另外，我要求你多一层专利内容提取器"，这是在已经对齐的方案上补了一个前置层，表明你在跑时间表时脑补了实际数据怎么进 pipeline

这是 operator 视角在思考 tooling，不是架构师视角。对本项目这是正确的视角。

---

## 后续衔接

本设计通过后：

1. **用户** 通过付费库拉 5 份 PDF，把公告号 + 原文 PDF 路径给我
2. **我** 启动 spike B（4.5h 内执行完）
3. **产物** spike report → 决定是否调整 `PR_PLAN.md`
   - 若 B 胜：修 `state/current.md`，砍 PR #5 + #6，推进剩余 PR
   - 若 B 败：回 PR_PLAN.md 原计划执行 PR #5 + #6
4. **P4 跟进** 若 B 胜，一周内开 novelty token wedge 的下一轮 office-hours
