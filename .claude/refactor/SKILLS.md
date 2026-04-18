# Skill 清单（22 个主 + 1 个延后）

每个 skill 目标：SKILL.md 150-300 行，单一职责，窄触发。

---

## 安装层（一次性，换模板时重跑）

### `/cnpatent-setup`
- **职责**：一次性 config（路径、付费库凭证、输出目录）
- **输入**：用户交互
- **输出**：`cnpatent-kit/config.json`
- **依赖**：无
- **PR**：#1 起步时加上，核心在 #2 之前跑通
- **注意**：不含模板学习，那是 template-setup 的事

### `/cnpatent-template-setup` ★ 核心
- **职责**：对话式学习用户的 docx 模板，生成一对一的 build 脚本
- **输入**：用户 `template.docx`
- **输出**：`cnpatent-kit/templates/<fingerprint>/` 下的 5 个文件
  - `template.docx`（副本）
  - `template.meta.json`（结构描述 + canonical 映射）
  - `build_docx.py`（模板专属渲染脚本）
  - `verification.md`（人类可读识别报告）
  - `verification_sample.docx`（带标签的样例 docx）
- **依赖**：`/cnpatent-setup`
- **PR**：#2
- **交互模式**：循环核验
  1. 分析模板 → 初版 meta.json + build_docx.py
  2. 生成 sample 和 verification.md
  3. 用户在本 session 里指出错误
  4. 更新 meta + 重生成
  5. 循环直到用户 ok
- **核心设计**：用户可多次切换模板；active 模板由 `kit/config.json` 记录

### `/cnpatent-template-study`（可选）
- **职责**：处理代理人给的交底书范本（指令型文档），提取每段的内容要求
- **输入**：代理人范本 docx/pdf
- **输出**：`cnpatent-kit/reference/section-requirements.md`
- **依赖**：无
- **PR**：#3
- **说明**：用户不一定有范本。无范本时 writer 靠 prompt 内置要求兜底，不崩

---

## 输入层

### `/cnpatent-ideate`
- **职责**：从开源材料（论文、结题报告）提取若干候选 idea
- **输入**：用户提供的材料（PDF/docx/文本）
- **输出**：`state/<run-id>/00_ideas.json`（3-5 个候选）
- **依赖**：`loaders/`
- **PR**：#12（编排期一起做）
- **说明**：用户已有成型 idea 时跳过此 skill

### `/cnpatent-ref-extract`
- **职责**：从已有专利文件提取 canonical outline（训练/比对用）
- **输入**：PDF/docx 专利
- **输出**：`state/<run-id>/extracted_outline.md`（符合 verified_outline schema）
- **依赖**：`loaders/`
- **PR**：#4
- **特点**：多轮自审（覆盖性 + 忠实性 + 一致性 cross-check），上限 5 轮
- **token 预算**：单份 30-50K（决策 4 确认自动审核可多轮，tokens 不是问题）

---

## 查新层

### `/cnpatent-novelty-free`
- **职责**：免费库自动检索（Google Patents / CNIPA / PATENTSCOPE / arXiv / Google Scholar）
- **输入**：idea 或 outline
- **输出**：`state/<run-id>/01_free_hits.jsonl`（L0 结构化结果，不进主 context）
- **依赖**：`recipes/`、`loaders/`
- **PR**：#10
- **token 预算**：检索结果直写 jsonl，不经 AI

### `/cnpatent-novelty-paid`
- **职责**：付费库 Playwright 检索（incoPat / CNKI 等，IP 登录）
- **输入**：idea、recipe 选择
- **输出**：`state/<run-id>/02_paid_hits.jsonl`
- **依赖**：`recipes/` YAML + Playwright
- **PR**：#10
- **哲学**：死脚本，AI 不解读 DOM。失败 → 快停，不 retry
- **IP 登录**：用户自己保证 IP 生效，AI 只负责点"IP 登录"按钮

### `/cnpatent-shortlist`
- **职责**：L1 卡片（~200 字/条）筛选，50 → 8
- **输入**：01 + 02 的 hits
- **输出**：`state/<run-id>/03_shortlist.jsonl`（带 diff_flag）
- **依赖**：无
- **PR**：#10
- **评分维度**：相关性、时效、地域法系、技术路径贴近度

### `/cnpatent-deepread` ★ 新增
- **职责**：L2 精读卡（2-3KB/条），对 shortlist top-3~5 拉全文
- **输入**：shortlist 结果
- **输出**：`state/<run-id>/03b_deep_reads/<ref_id>.md`（含权利要求、关键实施例、与我方差异要点）
- **依赖**：`loaders/`
- **PR**：#10
- **Cache**：同一 ref_id 不重复拉取
- **token 预算**：top 5 × 2.5KB ≈ 12K（三步法判定必须）

### `/cnpatent-judge`
- **职责**：2023 审查指南三步法判定
- **输入**：verified outline + deep_reads
- **输出**：`state/<run-id>/04_judgment.md`（绿/黄/红 + 理由）
- **依赖**：无（法定逻辑，免核验）
- **PR**：#10
- **Gate**：绿 → 进下一阶段；黄 → 提示补搜；红 → 建议重新选 idea 或调整范围

---

## 规划层

### `/plan-cnpatent-outline`（可选）
- **职责**：plan-mode 评审大纲，在写之前吵架
- **输入**：verified_outline
- **输出**：`state/<run-id>/05b_outline_review.md`
- **依赖**：无
- **PR**：#12
- **风格**：参照 gstack `/plan-eng-review`，交互式评分 + 修订建议

---

## 书写层

### `/cnpatent-write` ★ 核心
- **职责**：按 canonical 结构生成章节，4 个并行真 subagent
- **输入**：verified_outline + 当前 active template meta + learned-rules
- **输出**：`state/<run-id>/06_sections/*.md`（canonical 编号 01-06）
- **依赖**：`cnpatent-kit/prompts/writer-*.md`、`learned-rules.md`、`section-requirements.md`（可选）
- **PR**：#7（最小版）、#8（扩展到全章节）
- **核心实现**：
  ```
  for section in canonical_sections:
      Agent(subagent_type="executor",
            prompt=load_prompt(section)
                 + outline
                 + patent_voice
                 + de_ai_rules
                 + learned_rules
                 + (section_requirements if exists)
                 + template_meta.section_mapping[section])
  ```
- **主 context 只存路径，不存章节内容**

### `/cnpatent-review`
- **职责**：三 rubric 评审（一致性 / 抗幻觉 / 去 AI），独立不自审
- **输入**：`06_sections/`、outline
- **输出**：`state/<run-id>/07_review.json`（三个 0-100 分 + 具体 issue 列表）
- **依赖**：核验过的 reviewer-rubric.md
- **PR**：#8
- **Gate**：三个分都 ≥75 才放行；否则回 write 重改指定 section

### `/cnpatent-humanize`
- **职责**：包装通过核验的去 AI 检测器
- **输入**：`06_sections/`（审核通过后的）
- **输出**：`state/<run-id>/08_humanized/*.md` + AI 痕迹分
- **依赖**：核验后保留的 Python 检测器（见 MVM.md）
- **PR**：#9
- **Gate**：AI 痕迹分 < 30
- **设计**：SKILL.md 只管编排，调用现有 Python 脚本（挑通过 MVM 核验的用）

### `/cnpatent-build`
- **职责**：canonical → 当前 active template 映射 → 调 build_docx.py 渲染 docx + 图片提示词
- **输入**：`08_humanized/`、active template
- **输出**：`state/<run-id>/09_final.docx`、`10_image_prompts.md`
- **依赖**：`cnpatent-kit/templates/<fingerprint>/build_docx.py`
- **PR**：#11
- **校验**：9 个 H1/H2 结构、无权利要求书、公式连号、图引用一致

---

## 修订学习层 ★

### `/cnpatent-revise`
- **职责**：三路修订（tracked changes + 批注 + chat）合一
- **输入**：`09_final.docx`、`09_final.signed.docx`、本 session chat 指令
- **输出**：
  - `09_final.v2.docx`（应用修订后）
  - `09_revision_history.jsonl`（每轮 plan 留痕）
- **依赖**：python-docx、`revise-parser.md` prompt
- **PR**：#6
- **学习把关（Finding 10）**：每条修订项带 `user_learn` + `ai_learn_propose` + `decision`
- **循环**：v2 → v3 → ... 直到用户 accept

### `/cnpatent-learn`
- **职责**：多态 diff，产出 correction 追加到 jsonl
- **两种模式**：
  - Mode A：训练比对 `(extracted_outline, ai_draft, original_pdf_sections) → corrections`
  - Mode B：修订差异 `(09_final, v_final, revision_plan) → corrections`
- **输入**：两种 mode 之一
- **输出**：append 到 `cnpatent-kit/corrections.jsonl`
- **依赖**：锁文件 + correction schema
- **PR**：#5
- **过滤**：Mode B 时 respect revision_plan 的 `decision=false`，不学

### `/cnpatent-consolidate`
- **职责**：聚类 correction，人审晋升为 learned-rule
- **输入**：`corrections.jsonl`（active 状态的）
- **输出**：
  - 新增规则追加到 `learned-rules.md`
  - 晋升的 correction 标 `status: promoted`
- **依赖**：golden/regression 测试集
- **PR**：#5
- **流程**：
  1. 读 jsonl，按 (type, section, 语义相似) 聚类
  2. 过滤 ≥3 条、平均 conf ≥0.7 的簇
  3. 为每簇起草规则描述 + 展示支撑证据（correction id 列表）
  4. AskUserQuestion 逐条晋升（决策 1A：必须手动触发）
  5. 跑 golden/regression，挂了禁止晋升
  6. 通过的写入 learned-rules.md，带 id + source + approved_by + date

---

## 编排层

### `/cnpatent-pipeline`
- **职责**：端到端编排 + run 生命周期 + 模板选择 + gate 判定
- **输入**：用户启动
- **输出**：完整专利（调度其他所有 skill）
- **依赖**：所有 phase skills
- **PR**：#12
- **启动流程**：
  1. 检测 `.cnpatent/active_run`，无则新建或恢复
  2. 打印 "当前 run: ..." 锚点
  3. 检测 templates 数量 > 1 时 AskUserQuestion 选 active
  4. 按当前 phase 决定下一步调谁
  5. 每一 phase 跑完跑 gate，不过停下
  6. 每次用户触发前更新 runs.jsonl 的 last_active 和 phase

### `/cnpatent-challenge`（可选）
- **职责**：对抗模式，故意找能破坏我方新颖性的反证
- **输入**：verified_outline
- **输出**：反证列表 + 对我方方案的建议调整
- **依赖**：novelty skills
- **PR**：#12

---

## Run 管理层 ★

### `/cnpatent-runs`
- **职责**：列出所有 run 及状态
- **输入**：可选 filter（`--status active` 等）
- **输出**：人类可读的 run 列表
- **依赖**：`.cnpatent/runs.jsonl`
- **PR**：#6b（可并行 #6）
- **示例输出**：
  ```
  active    2026-04-18-fluid-coupling-a1b2  (流体耦合齿轮)  write 阶段   今天 14:22
  paused    2026-04-15-pcb-thermal-c3d4     (PCB热管理)    humanize    昨天 18:00
  completed 2026-04-10-motor-ctrl-e5f6      (电机控制)     delivered   2026-04-10
  ```

### `/cnpatent-resume`
- **职责**：切换 active_run 到指定 run
- **输入**：run-id 或 title 模糊匹配；空则 AskUserQuestion 列表选
- **输出**：更新 `.cnpatent/active_run`
- **依赖**：`.cnpatent/runs.jsonl`
- **PR**：#6b

---

## 训练层（延后到阶段 B）

### `/cnpatent-train`
- **职责**：批量训练编排，`ref-extract → write → learn` 流水线
- **输入**：目录，含 N 份已授权专利 PDF/docx
- **输出**：大批 correction 写入 jsonl
- **依赖**：`ref-extract`、`write`、`learn`
- **PR**：#13（延后，等用户攒到 ≥20 份真实专利）
- **触发**：用户手动，不自动
- **后续**：跑完手动触发 `/cnpatent-consolidate` 一次性大批晋升

---

## Skill 之间的依赖图

```
                      /cnpatent-setup
                             │
           ┌─────────────────┴──────────────────┐
           ▼                                    ▼
  /cnpatent-template-setup         /cnpatent-template-study (可选)
           │                                    │
           │                                    │
           │        /cnpatent-runs ─── /cnpatent-resume
           │            │
           └────────────┼─ active_run 读写
                        │
           /cnpatent-pipeline (总编排)
                        │
     ┌──────────┬──────┴──────┬──────────┬──────────┐
     ▼          ▼             ▼          ▼          ▼
  ideate    novelty-*    plan-outline  write   revise
     │         │             │          │        │
     │         ▼             │          ▼        ▼
     │      shortlist        │      review    learn
     │         │             │          │        │
     │         ▼             │          ▼        ▼
     │      deepread         │      humanize  consolidate
     │         │             │          │
     │         ▼             │          ▼
     │       judge           │        build
     │         │             │          │
     │         └─────────────┴──────────┘
     │                       │
     │                       ▼
     │                   交付 docx
     │
     └── （独立）challenge


(训练模式，阶段 B)
     PDF 语料
         │
         ▼
     /cnpatent-train
         ├── /cnpatent-ref-extract
         ├── /cnpatent-write (最小版)
         └── /cnpatent-learn (Mode A)
```
