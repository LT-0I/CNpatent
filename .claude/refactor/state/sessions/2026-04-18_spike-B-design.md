# Session: spike B 方案定稿（office-hours 路线）

- **日期**：2026-04-18（下午）
- **分支**：refactor/cnpatent
- **Session 类型**：gstack `/office-hours` + 四轮独立复核汇总
- **主产出**：[spike-B-design.md](../../spike-B-design.md)

---

## 本次 session 做了什么

1. 围绕"用 gstack + omc skill 设计重构期工作流"请求，生成初版工作流方案
2. 同 context 自审，提 10 个问题
3. 派独立 opus `critic` 做第三方复核：方向错 30%、砍九成 gstack skill、先立 golden test 基础设施
4. 派 OpenAI `codex exec` 做第四轮对抗审核：挑战更根本，提出"项目本身可能不该做，先 6 天 spike"
5. 用户提供关键情报：老 novelty 有效果但 token 爆炸；老 write 有 AI 味 + 学不会
6. 运行 `/office-hours` startup mode：Q2 + Q4 + Q5 + Premise lock，逼出最窄 wedge
7. 写完 design doc 落盘并更新 state

## 关键决策（全部已用户确认）

- **B 方案胜出**：手动 prompt engineering 4 份 section prompt + 共享 `patent-voice.md` 前缀 + 多 metric 三角，4.5h 内跑完
- **转向**：spike 目标 = 代理人定版风格（非用户个人 draft 风格）。用户明确说"我就是要符合专利申请风格的"
- **X3**：附图说明 spike 阶段跳过，refactor 阶段再补
- **样本**：去掉用户自己 2 份 draft（避免混风格），5 份全部来自付费库授权专利
- **切分**：2 iterate（核心 1 + 同类 1）+ 3 cold holdout（核心 1 + 同类 1 + 跨类 1）
- **Pass bar**：cold 3/3 过三 metric（句级 diff / 段落句长 KL / 连接词密度）
- **Extractor**：用户追加前置专利内容提取器需求，确认为 mini-extractor（PyMuPDF + 正则，~50 行，30-45 min）

## 5 条 premise（全部 agree）

- **P1** narrowest wedge = 手动 prompt engineering，不走学习回路
- **P2** B 冷测过 3/3 → 砍 PR #5 + #6，省 3.5 天
- **P3** canonical 章节按用户 4 分法（发明名称+技术领域 / 背景技术 / 发明内容 / 具体实施方式）
- **P4** novelty token 爆炸是 B 成功后的下一轮 wedge
- **P5** 付费库授权专利仅作语料，不写 `corrections.jsonl`（避免风格污染）

## 6 条 prose 规则（Q5 diff 提炼）

原句 vs 改句来自用户隧道路面 draft"架构缺反馈"段。6 条进 `patent-voice.md` 共享前缀：

- **R1** 因果 / 条件 / 递进必须显式连接词（当...时、因而、由于、使得、进而、从而）
- **R2** 同实体相邻第二次出现用代词（后者 / 前者 / 该 / 此）
- **R3** 两个 < 30 字、逻辑紧密短句合并成复句
- **R4** 话题切换显式标记
- **R5** 并列概念顺序服务于下文代词指向
- **R6** 长距离因果链在同一复句完成

## 下个 session 起手

- **若用户已拉到 5 份 PDF**：读 design doc 的「4.5h 执行时间表」，按 0-45 min 起步做 mini-extractor
- **若用户还没拉到**：提醒拉 PDF，重申 5 个搜索方向和 3 条铁律。不启动 spike
- **若用户要讨论别的**：先读 design doc 的 Success Criteria + Open Questions，对齐上下文

## 方法论副产物

本次 session 实操验证了一条原则：
**自审有盲区，独立 critic 提升一档，跨模型（codex）再提升一档，用户 domain insight（token 爆炸 / 学习失败经验）是终极杠杆**。四层组合出来的 wedge 比任何单层都窄且实用。office-hours 的 Q2 status quo baseline 是关键入口，前三轮都漏了。

## 阻塞 / 未决

- **阻塞**：等用户拉 5 份授权专利 PDF（按 design doc Dependencies 的 5 个搜索方向）
- **未决 Q1**：若 spike fail（cold ≤ 1/3），是否补跑"用户自己 draft 做 iterate"的中间点方案？（design doc Open Question #1）
- **未决 Q2**：3 metric 中 2 过 1 不过怎么判？需预先定义权重或取保守"全过才算过"（design doc Open Question #3）
- **未决 Q3**：P4 novelty 优化 wedge 在 spike 后多久启动？建议一周内

## 相关文件

- [spike-B-design.md](../../spike-B-design.md) 本次产出的 design doc
- [PR_PLAN.md](../../PR_PLAN.md) 原 14 PR，spike 结果出后按 P2 决定是否调整
- [FINDINGS.md](../../FINDINGS.md) P0 Finding #3（学习持久化）和 #4（测试策略）与本 spike 直接相关
- [DECISIONS.md](../../DECISIONS.md) spike 结果出后会补一条新决策（关于学习层砍不砍）
