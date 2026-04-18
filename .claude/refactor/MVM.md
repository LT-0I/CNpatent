# MVM — Mechanism Verification Manifest

**老机制核验清单**。先核验，后采纳。本清单覆盖老 cnpatent / cnpatent-humanizer / cnpatent-noveltycheck 中所有可辨认的机制。

## 状态字段定义

- **未核验**：初始状态，尚未跑实验
- **核验中**：实验进行中（分支开着）
- **通过**：实验通过，新 skill 采纳（包装老代码或重写）
- **淘汰**：实验未通过，有数据支撑理由
- **免核验**：法定逻辑或显然正确，直接保留（需注明理由）
- **待淘汰**：已知有问题，但等替代品就位再去

---

## 一、cnpatent（主写作 skill）机制

### 结构性机制

| ID | 机制 | 位置 | 状态 | 核验方法 | PR |
|----|------|------|------|---------|-----|
| M-CP-01 | 6 个伪 agent（planner/writer A-D/reviewer）角色扮演 | cnpatent/agents/*.md | **淘汰（设计层）** | 已确定改为真 subagent | PR #7 |
| M-CP-02 | Phase 0 验证 `5_verified_outline.md` schema | cnpatent-planner.md | 通过（包装） | schema 验证已是明确需求 | PR #1 |
| M-CP-03 | 4 writer 并行生成章节 | cnpatent-writer-a/b/c/d | **通过（改真 subagent）** | PR #7/#8 实测并发性能 | PR #7 #8 |
| M-CP-04 | Reviewer 三 rubric（一致性/抗幻觉/去 AI） | cnpatent-reviewer.md | 未核验 | 造合成 bad case 验证召回 | PR #8 |
| M-CP-05 | 最多 2 轮 reviewer ↔ writer 循环 | cnpatent Phase 2 | 未核验 | 实验找 review 挂的比例 | PR #8 |

### 书写规则

| ID | 机制 | 位置 | 状态 | 核验方法 | PR |
|----|------|------|------|---------|-----|
| M-CP-10 | writing-rules.md 去 AI 词汇 ban list | cnpatent/writing-rules.md | 未核验 | 对 training-corpus 检查 FP/FN | PR #7 |
| M-CP-11 | quality-checklist.md 19 项 QA | cnpatent/quality-checklist.md | 未核验 | 每项单独评估有效性 | PR #8 |
| M-CP-12 | revision-workflow.md 4 级变动分类 | cnpatent/revision-workflow.md | **重写** | 新 revise skill 用新分类法（Finding 7） | PR #6 |
| M-CP-13 | v14_hard_constraints.md 硬约束 | cnpatent/v14_hard_constraints.md | 未核验 | 逐条检查是否与新机制冲突 | PR #7 |

### DOCX 处理

| ID | 机制 | 位置 | 状态 | 核验方法 | PR |
|----|------|------|------|---------|-----|
| M-CP-20 | docx-patterns.md：模板锚点、XML/Run 处理 | cnpatent/docx-patterns.md | **淘汰（硬编码）+ 重建** | 被 template-setup 动态生成取代（Finding 5） | PR #2 |
| M-CP-21 | cnpatent_docx.py：插公式、插图、段落锚点 | cnpatent/scripts/cnpatent_docx.py | **淘汰** | 模板专属 build_docx.py 取代 | PR #2 PR #11 |
| M-CP-22 | formula_renumber.py：两阶段公式编号防冲突 | cnpatent/scripts/formula_renumber.py | 未核验 | 核验两阶段算法有效性，通过则包装进 build_docx | PR #2 |
| M-CP-23 | deai_cleanup.py：正则兜底清理 | cnpatent/scripts/deai_cleanup.py | 未核验 | 在 humanize pipeline 中对比贡献度 | PR #9 |
| M-CP-24 | 交底书模板.docx（9 H1/H2 结构） | cnpatent/交底书模板.docx | **通过（作为内置默认模板）** | 作为 template-setup 自测标本 | PR #2 |

### 图片提示词

| ID | 机制 | 位置 | 状态 | 核验方法 | PR |
|----|------|------|------|---------|-----|
| M-CP-30 | Phase 5 静默生成图片 prompt md | cnpatent Phase 5 | 通过（迁移） | 迁到 `/cnpatent-build` 的图片 prompt 产出 | PR #11 |

---

## 二、cnpatent-humanizer 机制

### 词汇与打分

| ID | 机制 | 位置 | 状态 | 核验方法 | PR |
|----|------|------|------|---------|-----|
| M-HM-01 | 3-tier 词汇检测（必替/聚集/密度） | humanizer/three-tier-vocabulary.md | 未核验 | 在 training-corpus 实测 FP/FN 率 | PR #9 |
| M-HM-02 | 4 级加权打分（0-24/25-49/50-74/75-100） | humanizer/scoring-system.md | 未核验 | 与人评相关性（20 样本） | PR #9 |
| M-HM-03 | 约 135 Chinese 词条词表 | humanizer/three-tier-vocabulary.md | 未核验 | 每词条出现频率统计 | PR #9 |

### 检测器矩阵

| ID | 机制 | 位置 | 状态 | 核验方法 | PR |
|----|------|------|------|---------|-----|
| M-HM-10 | audit.py：Phase 1+2 检测 + 加权打分 | humanizer/scripts/audit.py | 未核验 | 依赖 M-HM-01 通过 | PR #9 |
| M-HM-11 | regex_clean.py：Step 9 硬编码清理 | humanizer/scripts/regex_clean.py | 未核验 | 消融实验（是否对最终分有贡献） | PR #9 |
| M-HM-12 | burstiness.py：句长方差 | humanizer/scripts/burstiness.py | 未核验 | 与人评相关性 | PR #9 |

### v1.3 骨架检测（opt-in）

| ID | 机制 | 位置 | 状态 | 核验方法 | PR |
|----|------|------|------|---------|-----|
| M-HM-20 | skeleton_sim.py：骨架相似度 | humanizer/scripts/skeleton_sim.py | 未核验 | 对已知 AI 文本的召回率 | PR #9 |
| M-HM-21 | argumentation_slots.py：论证槽识别 | humanizer/scripts/argumentation_slots.py | 未核验 | 独立消融 | PR #9 |
| M-HM-22 | reader_pass.py：reader subagent 后验 | humanizer/scripts/reader_pass.py | 未核验 | 有/无 reader 分数对比 | PR #9 |

### v1.5 七个 opt-in 检测器

| ID | 机制 | 位置 | 状态 | 核验方法 | PR |
|----|------|------|------|---------|-----|
| M-HM-30 | topic_switch.py | humanizer/scripts/topic_switch.py | 未核验 | 单独消融 | PR #9 |
| M-HM-31 | enumeration_check.py | humanizer/scripts/enumeration_check.py | 未核验 | 单独消融 | PR #9 |
| M-HM-32 | background_leak.py | humanizer/scripts/background_leak.py | 未核验 | 单独消融 | PR #9 |
| M-HM-33 | term_pronoun.py | humanizer/scripts/term_pronoun.py | 未核验 | 单独消融 | PR #9 |
| M-HM-34 | unprepared_concept.py | humanizer/scripts/unprepared_concept.py | 未核验 | 单独消融 | PR #9 |
| M-HM-35 | param_segment.py | humanizer/scripts/param_segment.py | 未核验 | 单独消融 | PR #9 |
| M-HM-36 | merge_short.py | humanizer/scripts/merge_short.py | 未核验 | 单独消融 | PR #9 |

### 规则文档

| ID | 机制 | 位置 | 状态 | 核验方法 | PR |
|----|------|------|------|---------|-----|
| M-HM-40 | chinese-specific-tells.md | humanizer/chinese-specific-tells.md | 未核验 | 规则条逐条对照 training-corpus 检查 | PR #9 |
| M-HM-41 | do-not-overcorrect.md 保护的法定短语 | humanizer/do-not-overcorrect.md | **免核验（法律语言）** | 基础保留 | PR #9 |
| M-HM-42 | protected-regions.md 8 类只读区域 | humanizer/protected-regions.md | 未核验 | 误改率实验 | PR #9 |
| M-HM-43 | section-rules.md 章节差异化规则 | humanizer/section-rules.md | 未核验 | 每章节规则独立验证 | PR #9 |
| M-HM-44 | patent-anti-patterns.md 模板型 AI 痕迹 | humanizer/patent-anti-patterns.md | 未核验 | 对 AI 生成文本的召回 | PR #9 |
| M-HM-45 | skeleton-patterns.md 骨架模式 | humanizer/skeleton-patterns.md | 未核验 | 依赖 M-HM-20 通过 | PR #9 |

### 编排

| ID | 机制 | 位置 | 状态 | 核验方法 | PR |
|----|------|------|------|---------|-----|
| M-HM-50 | 9 步重写流水线 | humanizer SKILL.md | 未核验 | 对整体效果的必要性实验 | PR #9 |
| M-HM-51 | Phase 4.5 reader agent 骨架复审 | humanizer Phase 4.5 | 未核验 | 依赖 M-HM-22 | PR #9 |
| M-HM-52 | Phase 5 gate（重写 vs patch） | humanizer Phase 5 | 未核验 | gate 判定准确率 | PR #9 |

---

## 三、cnpatent-noveltycheck 机制

### 法律判定

| ID | 机制 | 位置 | 状态 | 核验方法 | PR |
|----|------|------|------|---------|-----|
| M-NC-01 | 三步法判定（2023 审查指南） | noveltycheck-judge.md | **免核验（法规）** | 法律规定，直接保留 | PR #10 |
| M-NC-02 | cn-patent-law.md 新颖性/创造性规则 | noveltycheck/cn-patent-law.md | **免核验** | 引用法规 | PR #10 |

### 检索与去重

| ID | 机制 | 位置 | 状态 | 核验方法 | PR |
|----|------|------|------|---------|-----|
| M-NC-10 | 免费库 5 个搜索（GP/CNIPA/PS/arXiv/GS） | noveltycheck-screener.md | 未核验 | 每源独立测试召回率 | PR #10 |
| M-NC-11 | database-catalog.md 分类学 | noveltycheck/database-catalog.md | 未核验 | 结构有效性 review | PR #10 |
| M-NC-12 | search-methodology.md：IPC 估计、关键词构造 | noveltycheck/search-methodology.md | 未核验 | 与人工关键词对比 | PR #10 |
| M-NC-13 | Playwright 去重脚本 | noveltycheck/scripts/playwright/ | 未核验 | 在 3 个库上跑通 + 去重率 | PR #10 |
| M-NC-14 | 族合并逻辑 | noveltycheck/phase-b2-merge-rules.md | 未核验 | 对已知族的聚合正确率 | PR #10 |

### 卡片与指引

| ID | 机制 | 位置 | 状态 | 核验方法 | PR |
|----|------|------|------|---------|-----|
| M-NC-20 | phase-b1-ai-read-cards.md：AI 精读卡 | noveltycheck/phase-b1-ai-read-cards.md | **通过（升级为 L2 精读卡）** | Finding 2 已明确要升级 | PR #10 |
| M-NC-21 | templates.md：操作卡、回填表 | noveltycheck/templates.md | 未核验 | 用户可用性评估 | PR #10 |

### 编排

| ID | 机制 | 位置 | 状态 | 核验方法 | PR |
|----|------|------|------|---------|-----|
| M-NC-30 | Phase A-B-C-D 三阶段编排 | noveltycheck SKILL.md | **通过（拆成多 skill）** | 现有机制保留逻辑，拆分实现 | PR #10 |
| M-NC-31 | 绿灯自动触发 cnpatent | noveltycheck Phase D | **淘汰** | 决策：artifact-only 交接，不自动触发 | PR #12 |

---

## 四、资产（免核验）

| ID | 资产 | 位置 | 处理 |
|----|-----|------|------|
| A-01 | 交底书模板.docx | cnpatent/ | 作为 template-setup 自测标本 |
| A-02 | cn-patent-law.md | noveltycheck/ | 原样保留参考 |
| A-03 | 各 schema 的字段定义（文字说明） | 散布各 skill | 汇总到 cnpatent-kit/schemas/ |

---

## 五、实验方法统一约定

所有未核验项必须按如下格式产出实验报告到 `.claude/refactor/experiments/<机制-ID>_<日期>.md`：

```markdown
# 实验报告：<机制 ID> <机制名>

**日期**：YYYY-MM-DD
**分支**：refactor/<pr-xxx>
**执行者**：session-id or 人

## 核验问题
具体问题（如 "三级词表 Tier 1 必替词的 FP 率是多少？"）

## 方法
- 数据集：...（路径 + 样本量 + 构造方式）
- 实验设置：...
- 基线：...

## 结果
- 核心指标：...
- 副作用：...

## 结论
- 通过 / 淘汰 / 待定
- 理由：...

## 建议
- 若通过：如何包装进新 skill
- 若淘汰：是否需要替代机制
- 若待定：需要补的数据 / 实验
```

---

## 六、当前 MVM 统计

截至 2026-04-18（规划完成时）：

- **免核验**：5 项（法规 / 法定语言 / 显然资产）
- **已确定保留（通过）**：6 项
- **已确定淘汰**：4 项
- **待核验**：~45 项（绝大多数）
- **重写**：1 项（revision-workflow）

---

## 七、核验进度更新规则

开任何 PR 时：
1. 本 PR 涉及的 MVM 项先从"未核验"改为"核验中"
2. PR 完成后，每项按实验结果改为"通过"/"淘汰"
3. 每次状态变化 commit 此文件
4. 若发现漏项，补进对应表格
