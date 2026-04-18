# PR 执行计划

13 个主 PR（含 #6b）+ 1 个延后 PR（#13），合计 14 个。估算 ~17.5 工作日（一人按主干串行，天然并行机会已吸收；纯相加约 20.5 天）。

## 顺序总览

| PR | 标题 | 依赖 | 估时 | 可并行于 |
|----|------|------|------|---------|
| #1 | kit 骨架 + MVM + schemas + run 基础设施 | — | 1 天 | — |
| **#2** | **`/cnpatent-template-setup` 对话式核验（关键）** | #1 | 3 天 | #3,#4,#5,#6,#6b |
| #3 | `/cnpatent-template-study`（可选产物） | #1 | 1 天 | #2,#4,#5,#6,#6b |
| #4 | `/cnpatent-ref-extract` 多格式 + 多轮自审 | #1 | 2 天 | #2,#3,#5,#6,#6b |
| #5 | `/cnpatent-learn`（双模式）+ `/cnpatent-consolidate` + 文件锁 | #1 | 1.5 天 | #2,#3,#4,#6,#6b |
| **#6** | **`/cnpatent-revise` 三路合一 + 双把关学习 flag** | #5 | 2 天 | #2,#3,#4,#6b |
| **#6b** | **`/cnpatent-runs` + `/cnpatent-resume`** | #1 | 0.5 天 | 并行 #2-#6 |
| #7 | `/cnpatent-write` 最小版（canonical section schema） | #1, #2, #3 | 1.5 天 | — |
| #8 | `/cnpatent-review` 机制核验 + 三 rubric + write 扩展到全章节 | #7 | 2 天 | #9, #10 |
| #9 | `/cnpatent-humanize` 机制核验 + 消融实验 | #7 | 2 天 | #8, #10 |
| #10 | 查新五件套（free/paid/shortlist/deepread/judge） | #1 | 2 天 | #8, #9 |
| #11 | `/cnpatent-build`（canonical → template 映射）+ 图片提示词 | #2, #7 | 1 天 | — |
| #12 | `/cnpatent-pipeline` + challenge + ideate + plan-outline + 老 skill 归档 | all above | 1 天 | — |
| #13 | **（延后）** `/cnpatent-train` 批量训练 | ≥20 份真实专利 | 等数据 | — |

**关键路径**：#1 → #2 → #7 → #11 → #12（模板贯穿全线）  
**总工期估算**：~17.5 工作日

---

## PR #1：kit 骨架 + MVM + schemas + run 基础设施

**目标**：立地基，不动老代码。

**交付物**：
- `cnpatent-kit/` 目录（空 .gitkeep 占位），包括：
  - `patent-voice.md` / `terminology-lock.md` / `de-ai-rules.md`（从老 skill 摘出参考初版）
  - `learned-rules.md`（空文件，带模板头注释）
  - `corrections.jsonl`（空）
  - `config.json`（最小默认值）
  - `schemas/*.schema.json`（全套 8 个）
  - `prompts/`、`recipes/`、`templates/`、`reference/`、`loaders/`、`tests/golden/` 骨架目录
- `.cnpatent/active_run` 和 `.cnpatent/runs.jsonl` 的契约定义（MD 文档）
- `.claude/refactor/MVM.md` 的老机制核验清单初稿（本项目已有）
- README 指向 `.claude/refactor/`

**测试/校验**：
- 全部 schema 用 json-schema validator 自检过 syntactic 合法
- 手动 `cat runs.jsonl` 能正常解析
- `git ls-files cnpatent-kit/` 列出预期结构

**Gotchas**：
- 不实现任何 skill，纯目录 + 契约
- 从老 skill 摘规则时**只摘**，不重写；注明出处（"来源：cnpatent-humanizer/three-tier-vocabulary.md v1.5"）

**验收门禁**：
- 目录结构 review 过
- 所有 schema 字段对应后续 PR 明确的使用场景

---

## PR #2：`/cnpatent-template-setup` 对话式核验 ★ 关键

**目标**：能对任意用户模板生成一对一 build 脚本，并通过对话修正识别错误。

**交付物**：
- `.claude/skills/cnpatent-template-setup/SKILL.md`（~250 行）
- `.claude/skills/cnpatent-template-setup/scripts/`：
  - `analyze_template.py` —— 扫描 docx 样式、锚点、placeholder
  - `generate_meta.py` —— 生成 template.meta.json
  - `generate_build_script.py` —— 从 meta 生成 build_docx.py
  - `generate_verification_sample.py` —— 生成带标签的 sample docx
- 一个内置默认模板作为自测标本
- Skill 交互循环在 SKILL.md 内说明
- 样例 `template.meta.json` schema 实例

**测试/校验**：
- 用老 `交底书模板.docx` 跑一遍，检查：
  - 9 个 H1/H2 全部识别
  - verification.md 可读
  - verification_sample.docx 在 Word 打开标签清晰
  - 生成的 build_docx.py 能产出基本合法 docx

**Gotchas**：
- 用户模板可能有 tracked changes / 批注 / 受保护区域，要 sanitize 后分析
- fingerprint 基于结构 JSON 的 sha256，不包含装饰性内容
- 对话循环要支持"我不懂，你继续试"和"这里错了，我给你说"两种语气

**验收门禁（决策 5A）**：
- 识别失败时**停下让用户改 meta.json**，不猜默认值
- sample.docx 每个样式都有可辨认标签

---

## PR #3：`/cnpatent-template-study`（可选）

**目标**：从代理人范本抽取 section 内容要求清单。

**交付物**：
- `.claude/skills/cnpatent-template-study/SKILL.md`
- 生成 `cnpatent-kit/reference/section-requirements.md`
- 若用户无范本，skill 可跳过（pipeline 会感知）

**测试/校验**：
- 手动提供一份代理人范本跑通
- 无范本时 `/cnpatent-pipeline` 不崩

**Gotchas**：
- 决策 6A：软约束，writer 参考但可合理偏离
- 决策 6 补充：此 skill 可选，pipeline 检测 `section-requirements.md` 存在才加载

---

## PR #4：`/cnpatent-ref-extract` 多格式 + 多轮自审

**目标**：从 PDF/docx 专利提取 canonical outline，token 敢花。

**交付物**：
- `.claude/skills/cnpatent-ref-extract/SKILL.md`
- `cnpatent-kit/loaders/{pdf,docx,text}_loader.py`
- `cnpatent-kit/prompts/extract-selfaudit.md`（多轮自审 prompt）
- 5 轮自审流程在 SKILL.md 中展开（Round 1 抽取 → 2 覆盖性 → 3 忠实性 → 4 补抽取 → 5 一致性）

**测试/校验**：
- 在一份已知正确的专利上跑，比对抽取 outline 与人工 outline
- 自审能抓出故意注入的遗漏/幻觉

**Gotchas**：
- 决策 4：自动审核，tokens 不是问题
- 上限 3 次补抽取，不收敛就 audit.md 记录并跳过该份

---

## PR #5：`/cnpatent-learn` + `/cnpatent-consolidate` + 文件锁

**目标**：学习回路的两层机制就位，即使暂无输入也能 smoke test。

**交付物**：
- `.claude/skills/cnpatent-learn/SKILL.md`（支持 Mode A 和 Mode B 双态）
- `.claude/skills/cnpatent-consolidate/SKILL.md`
- `cnpatent-kit/` 下 `corrections.jsonl` 写入逻辑（带 flock / msvcrt 锁）
- `learned-rules.md` 晋升写入逻辑
- Schema：`correction.schema.json`、`learned_rule.schema.json`
- 聚类算法（简单的 type+section+embedding 相似度）
- AskUserQuestion 的晋升人审流程

**测试/校验**：
- 手工造 10 条 correction，能聚类正确
- 晋升一条规则后，`learned-rules.md` 格式正确、可被 /cnpatent-write 加载
- 并发跑两个 learn 进程，后者应快停

**Gotchas**：
- 决策 1A：consolidate 完全手动，不自动触发
- Finding 10：respect revision_plan 的 `decision` 字段，不学 user 或 AI 标 false 的
- 锁文件清理：skill 结束 remove lock，崩溃时残留 lock 需要 setup 时清理

---

## PR #6：`/cnpatent-revise` 三路合一 + 双把关

**目标**：修订闭环打通，所有修改都能走学习通道或不走。

**交付物**：
- `.claude/skills/cnpatent-revise/SKILL.md`
- `cnpatent-kit/prompts/revise-parser.md`
- 解析 tracked changes + 批注（python-docx）
- chat 指令捕捉（从当前 session 上下文读）
- 生成 `revision_plan.json`（schema）
- 展示给用户过目（列表形式）+ 每项可勾选学习开关
- 应用修订 → 新版 docx

**测试/校验**：
- Word 里手动改一份 09_final.docx 为 signed.docx（含 tracked + 批注）
- 跑 revise，确认三路都被识别
- 用户否决一条学习，确认 correction 不进 jsonl

**Gotchas**：
- 决策 7A：三路全解析，缺了忽略不强制
- 多轮修订保留 v2 v3 ... 原件（决策 7 补充：磁盘占用允许）
- 只有 final v_n 喂 learn；中间版本标 superseded

---

## PR #6b：`/cnpatent-runs` + `/cnpatent-resume`

**目标**：run 生命周期可见性和切换能力（Finding 9）。

**交付物**：
- `.claude/skills/cnpatent-runs/SKILL.md`（~100 行）
- `.claude/skills/cnpatent-resume/SKILL.md`（~100 行）
- `.cnpatent/runs.jsonl` 读写工具
- 人类可读的 run 列表渲染
- AskUserQuestion 风格的选择器（当 resume 不带参数时）

**测试/校验**：
- 手工造两个 run 目录，runs 列出正确
- resume 切换 active_run 后，pipeline 感知正确

**Gotchas**：
- 与 PR #6 可并行
- 此 skill 不修改 state/<run-id>/ 内容，只动 active_run 和 runs.jsonl

---

## PR #7：`/cnpatent-write` 最小版（canonical schema）

**目标**：能写出符合 canonical schema 的章节（section 一/二/三 即可），真 subagent 并行。

**交付物**：
- `.claude/skills/cnpatent-write/SKILL.md`
- `cnpatent-kit/prompts/writer-section-1-3.md`（先完成这一个）
- 真 subagent 调度代码（SKILL.md 的指令形式）
- `section.schema.json` 的产物校验
- state/<run-id>/06_sections/ 写入
- 主 context 只保留路径，不保留内容

**测试/校验**：
- 给一份 dummy outline，能产出 section 1-3
- 章节符合 canonical schema
- 4 个写作同时跑不崩（即使暂时只写 1-3）

**Gotchas**：
- learned-rules.md 可能为空，要优雅处理
- 若 PR #3 已完成，section-requirements.md 作为参考加载
- PR #2 的 template.meta.json 的 section_mapping 决定 "我们的 canonical section 四" 该写什么

---

## PR #8：`/cnpatent-review` + write 扩展

**目标**：review 评分门禁可用；write 写全 6 个 canonical section。

**交付物**：
- `.claude/skills/cnpatent-review/SKILL.md`
- `cnpatent-kit/prompts/reviewer-rubric.md`（核验后的三 rubric）
- 三个分数：一致性 / 抗幻觉 / 去 AI（0-100）
- issue 列表 + 修订指令（返回给 writer）
- write 扩展到 section 4/5/6 的 prompts
- 跑 training-corpus 回归（每扩展一个 writer 后）

**测试/校验**：
- 人工造一份"一致性差"的 draft，review 应抓出
- 人工造一份有幻觉的 draft，review 应抓出
- 三分都 ≥ 75 时 gate 放行

**Gotchas**：
- 三 rubric 的老版本在 cnpatent/cnpatent-reviewer.md（参考），**必须核验有效性再写**
- review 和 write 循环：review 挂了回 write，但不是重写全部，是定点修该 section

---

## PR #9：`/cnpatent-humanize` 机制核验 + 消融

**目标**：通过实验判决老 humanizer 每个检测器的去留。

**交付物**：
- `.claude/skills/cnpatent-humanize/SKILL.md`
- 消融实验报告：`.claude/refactor/experiments/humanize-ablation.md`
  - 三级词表 FP/FN
  - 4 级打分与人评相关性
  - v1.3 skeleton 召回率
  - v1.5 七个检测器各自贡献
  - 保护区域误改率
- 通过核验的检测器保留（包装到新 humanize，不重写 Python）
- 不通过的记录到 MVM.md 的"已淘汰"段，给出理由

**测试/校验**：
- 在 training-corpus 的一个 held-out 子集上评 AI 痕迹分
- 对比老 humanizer 和新 humanize 的分数（不应退步）

**Gotchas**：
- **这里可能淘汰一些工作成果**，每个淘汰必须有实验数据支撑，不是感觉
- 保留的检测器不改 Python 代码，只包装调用
- AI 痕迹分 < 30 是目标 gate

---

## PR #10：查新五件套

**目标**：完整查新链路，token 可控。

**交付物**：
- `.claude/skills/cnpatent-novelty-free/SKILL.md`
- `.claude/skills/cnpatent-novelty-paid/SKILL.md`
- `.claude/skills/cnpatent-shortlist/SKILL.md`
- `.claude/skills/cnpatent-deepread/SKILL.md`（★ 新增）
- `.claude/skills/cnpatent-judge/SKILL.md`
- `cnpatent-kit/recipes/{incopat,cnki,google-patents}.recipe.yaml`
- Playwright 启动脚本
- 三步法判定 prompt

**测试/校验**：
- 给一份 outline，跑完整查新链路
- 总 token 消耗 < 30K（比现状 200K+ 降一个数量级）
- deepread 对 top 5 的精读卡覆盖：权利要求、关键实施例、差异点
- judge 的绿/黄/红判定有明确理由

**Gotchas**：
- IP 登录死脚本，失败快停不 retry
- recipe 选择器坏了要让用户改 recipe 不是改 skill
- shortlist 打分维度明确（相关性 / 时效 / 地域 / 技术路径）

---

## PR #11：`/cnpatent-build`

**目标**：canonical 章节 → 当前模板的 docx + 图片提示词。

**交付物**：
- `.claude/skills/cnpatent-build/SKILL.md`
- canonical → template section 映射执行器
- 调用 PR #2 生成的 `build_docx.py`
- 图片提示词 md 生成
- docx 结构校验（9 个 H1/H2、公式连号、无权利要求书、图引用匹配）

**测试/校验**：
- 完整跑一次 write → review → humanize → build
- 打开 docx 在 Word 中视觉验收
- 换模板重跑同份内容，换出来的 docx 正确

**Gotchas**：
- 公式重编号（formula_renumber 的逻辑要核验后保留或重写）
- 图片 placeholder 可能在多个章节引用，编号要一致
- 若缺图，prompt 产出占位提示词 + docx 插占位图

---

## PR #12：编排 + 剩余 skill + 归档

**目标**：端到端可用，老 skill 归档。

**交付物**：
- `.claude/skills/cnpatent-pipeline/SKILL.md`（含 run 生命周期检测）
- `.claude/skills/cnpatent-challenge/SKILL.md`
- `.claude/skills/cnpatent-ideate/SKILL.md`
- `.claude/skills/plan-cnpatent-outline/SKILL.md`
- 老 3 skill 移入 `.claude/skills/_legacy/`
- 各老 skill 头部加 deprecation 注释，指向新 skill

**测试/校验**：
- 端到端跑一份真实专利：从 idea → docx → 手改 → revise → learn
- 从 state/<run-id>/ 能完整追溯每一步
- 跨 session 恢复测试：做一半关了、开新 session 能接上

**Gotchas**：
- 老 skill 不删（保留半年，决策 2A）
- 新 skill 与老 skill 触发条件要错开，避免双触发

---

## PR #13：批量训练（延后）

**目标**：用 20 份真实专利一次性充实 learned-rules.md。

**交付物**：
- `.claude/skills/cnpatent-train/SKILL.md`
- 训练报告：`.claude/refactor/experiments/bootstrap-training.md`
- 一次性大批 correction 晋升后的 learned-rules.md snapshot

**前置**：
- 用户收集到 ≥20 份已授权专利 PDF/docx
- PR #1-#12 全部完成并 stable

**测试/校验**：
- 训练集 + held-out 20% 作为测试集
- held-out 集的 AI 写作 vs 真实专利，后 AI 痕迹分显著下降
- 一次性晋升 ≥10 条新规则

**Gotchas**：
- 训练集应覆盖不同技术领域，避免过拟合
- 晋升前跑完整 golden/regression
- 此 PR 不限时，等数据到位再跑

---

## 并行策略

```
串行主干:
  #1 → #2 ──────────────────────────→ #7 → #11 → #12

可完全并行于 #2 (都依赖 #1):
  #3, #4, #5, #6(需 #5), #6b

依赖 #7 可并行彼此:
  #8, #9, #10

延后:
  #13 等数据
```

一个人按顺序做大约 17.5 天。两人协作（一人主干、一人并行）能压到 ~11 天。

---

## 每个 PR 结束前必做

1. 更新 `.claude/refactor/state/progress.jsonl` 对应行的 `status` 和 `completed_at`
2. 更新 `.claude/refactor/state/current.md` 指向下一个 active PR
3. 写 `.claude/refactor/state/sessions/<date>_<pr-topic>.md` 交接笔记
4. 若发现了新的设计问题或决策，更新 `FINDINGS.md` 或 `DECISIONS.md`
5. 若老机制核验结果已出，更新 `MVM.md`
6. commit + push（推 remote 为了协作可见；也可用 `/ship` 自动化）

---

## PR 执行期的 gstack 工具（可选脚手架）

重构产物本身不依赖 gstack 运行时。但执行 PR 时可以借 gstack skill 加速：

| 时机 | 命令 | 用途 |
|------|------|------|
| 开工前 | `/plan-eng-review` | 复核本 PR 设计是否与 FINDINGS / DECISIONS 对齐 |
| 代码写完 | `/review` | 过一遍 diff，catch 漏掉的 gate、缺失的 schema 校验、未核验的老机制引用 |
| 新 skill 接入前 | `/qa` | 对新 skill 跑基本路径冒烟测试 |
| 推 PR | `/ship` | 自动跑 review + push + 创 PR |
| 新 skill 报错 | `/investigate` | 根因分析 |
| PR 收尾 | `/retro` | 归纳本 PR 的决策和新发现（可选） |

都是**可选**。不用也能按 PR_PLAN.md 走完流程。跨 session 恢复走本项目自己的 `state/current.md`，不用 gstack `/checkpoint`。

---

## 风险 & 缓解

| 风险 | 缓解 |
|------|------|
| PR #2 模板识别遇到奇葩模板 | 决策 5A 停下让用户改 meta；不猜 |
| PR #9 消融实验发现老检测器大量无效 | 这是好事，减负。务必保留实验报告 |
| PR #10 付费库 recipe 容易过时 | 每个 recipe 单独 test case，坏了只改 recipe |
| PR #6 三路修订解析冲突（tracked 要删、批注要扩写同一段） | revision_plan.json 展示冲突，不自作主张 |
| PR #12 跨 session 恢复失败 | 每次动作前打印 "当前 run"，可肉眼核对 |
| PR #13 延后太久 learn 路径生疏 | 在 PR #5-#6 时跑至少一次完整学习循环验证 |
