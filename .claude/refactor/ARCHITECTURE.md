# 架构设计

## 一、核心设计原则

1. **薄编排 + 真 subagent**：编排 skill 只做 gate 判定和 state 路径传递，不装领域知识；书写/评审由 `Agent(subagent_type=executor)` 真并行子任务跑，每个独立 context。
2. **Strangler Fig 演进**：老 skill 不删、不原地改；新 skill 包装现有脚本与规则 md，验证通过再渐进替换。老 skill 归档 `.claude/skills/_legacy/`。
3. **Canonical 内核 + 边界吸收差异**：中间产物永远用 canonical 章节编号（一～六）。模板差异在 `/cnpatent-template-setup`（入）和 `/cnpatent-build`（出）两个边界吸收。
4. **学习走数据，不走代码**：规则演进通过 `corrections.jsonl` → 人审晋升 → `learned-rules.md`；**永远不让 AI 重写 SKILL.md**。
5. **Artifact-only 跨 skill 通信**：所有交接走 `.cnpatent/state/<run-id>/` 下的文件，schema 化；下游不继承上游 context。
6. **评分 + 门禁**：每阶段产物都有分数和阈值，不过不前进。
7. **Run 隔离 + active_run 显式**：一个安装跑多专利，每个专利一个 run-id 目录；当前会话的 active run 用 `.cnpatent/active_run` 显式记录。
8. **笨工具胜过聪明推理**：Playwright 跑 YAML recipe 死脚本；AI 只解读结构化输出，不碰 DOM。

---

## 二、三阶段结构

| 阶段 | 何时做 | 内容 | 数据依赖 |
|------|--------|------|---------|
| **C 安装期** | 软件安装、换模板时 | `/cnpatent-template-setup`（对话式）+ `/cnpatent-template-study`（可选） | 用户模板 docx、代理人范本 |
| **A 开发期** | 立刻可推进，不等训练数据 | 查新、书写、修订、学习全管线 | 单份 idea 或开源材料 |
| **B 训练期** | 用户攒到 20 份真实专利再跑 | 批量 `/cnpatent-train`，bootstrap `learned-rules.md` | ≥20 份已授权专利 PDF/docx |

阶段 A 不阻塞于 B。没训练数据时 `learned-rules.md` 为空，靠 prompts + 模板要求撑住质量；随用随学。

---

## 三、完整目录结构

```
C:\Users\13080\Desktop\CNpatent\                项目根
│
├── .claude/skills/
│   ├── cnpatent-kit/                           ← 共享库（被 import，不是 skill）
│   │   ├── patent-voice.md                     语气基础规则
│   │   ├── terminology-lock.md                 术语一致性
│   │   ├── de-ai-rules.md                      基础去 AI 规则（稳定不涨）
│   │   ├── learned-rules.md                    晋升规则（人审后只追加）
│   │   ├── corrections.jsonl                   原始 correction 日志 (append-only)
│   │   ├── corrections.jsonl.lock              运行时锁文件
│   │   ├── learned-rules.md.lock               运行时锁文件
│   │   ├── config.json                         active_template 等全局配置
│   │   │
│   │   ├── schemas/                            canonical 数据契约
│   │   │   ├── idea.schema.json
│   │   │   ├── hit.schema.json                 查新命中卡片
│   │   │   ├── verified_outline.schema.json    canonical 大纲
│   │   │   ├── section.schema.json             canonical 章节
│   │   │   ├── correction.schema.json          学习条目
│   │   │   ├── revision_plan.schema.json       修订计划
│   │   │   ├── template_meta.schema.json       模板元数据
│   │   │   └── run_meta.schema.json            run 注册项
│   │   │
│   │   ├── prompts/                            prompt 模板（真 subagent 加载）
│   │   │   ├── writer-section-1-3.md
│   │   │   ├── writer-section-4.md
│   │   │   ├── writer-section-5-6a.md
│   │   │   ├── writer-section-6b.md
│   │   │   ├── reviewer-rubric.md
│   │   │   ├── revise-parser.md
│   │   │   └── extract-selfaudit.md
│   │   │
│   │   ├── recipes/                            Playwright YAML 配方
│   │   │   ├── incopat.recipe.yaml
│   │   │   ├── cnki.recipe.yaml
│   │   │   └── google-patents.recipe.yaml
│   │   │
│   │   ├── templates/                          ★ 按 fingerprint 组织
│   │   │   ├── <fingerprint_A>/
│   │   │   │   ├── template.docx               用户模板原件副本
│   │   │   │   ├── template.meta.json          结构描述 + canonical 映射
│   │   │   │   ├── build_docx.py               1:1 生成脚本
│   │   │   │   ├── verification.md             人类可读识别报告
│   │   │   │   └── verification_sample.docx    ★ 带标签的样例
│   │   │   └── <fingerprint_B>/...
│   │   │
│   │   ├── reference/
│   │   │   └── section-requirements.md         代理人范本可选产物
│   │   │
│   │   ├── loaders/                            多格式文档 loader
│   │   │   ├── pdf_loader.py
│   │   │   ├── docx_loader.py
│   │   │   └── text_loader.py
│   │   │
│   │   └── tests/golden/                       黄金集
│   │       ├── training-corpus/                训练数据（PDF + ground truth）
│   │       ├── regression/                     老 correction 回归
│   │       ├── rule-application/               新规则适用验证
│   │       ├── no-overreach/                   不误伤正常文本
│   │       └── template-roundtrip/             canonical ↔ template 双向验证
│   │
│   ├── cnpatent-setup/                         17 个 phase skills
│   ├── cnpatent-template-setup/
│   ├── cnpatent-template-study/
│   ├── cnpatent-ideate/
│   ├── cnpatent-ref-extract/
│   ├── cnpatent-novelty-free/
│   ├── cnpatent-novelty-paid/
│   ├── cnpatent-shortlist/
│   ├── cnpatent-deepread/
│   ├── cnpatent-judge/
│   ├── plan-cnpatent-outline/
│   ├── cnpatent-write/
│   ├── cnpatent-review/
│   ├── cnpatent-humanize/
│   ├── cnpatent-build/
│   ├── cnpatent-revise/
│   ├── cnpatent-learn/
│   ├── cnpatent-consolidate/
│   ├── cnpatent-pipeline/
│   ├── cnpatent-challenge/
│   ├── cnpatent-runs/                          ★ run 列表
│   ├── cnpatent-resume/                        ★ run 切换
│   ├── cnpatent-train/                         （延后到阶段 B）
│   │
│   └── _legacy/                                ← 老 3 skill 归档
│       ├── cnpatent-legacy/
│       ├── cnpatent-humanizer-legacy/
│       └── cnpatent-noveltycheck-legacy/
│
├── .cnpatent/                                  ★ 项目运行期状态目录
│   ├── active_run                              单行文件：当前 active run-id
│   ├── runs.jsonl                              run 注册表（append-only）
│   └── state/
│       └── <run-id>/                           每个专利一个目录
│           ├── 00_ideas.json
│           ├── 01_free_hits.jsonl
│           ├── 02_paid_hits.jsonl
│           ├── 03_shortlist.jsonl
│           ├── 03b_deep_reads/                 L2 精读卡
│           ├── 04_judgment.md
│           ├── 05_verified_outline.md
│           ├── 05b_outline_review.md           可选
│           ├── 06_sections/                    canonical 章节 md
│           ├── 07_review.json
│           ├── 08_humanized/
│           ├── 09_final.docx                   AI 原稿（不可改）
│           ├── 09_final.signed.docx            用户标注版
│           ├── 09_final.v2.docx, v3.docx ...   修订迭代
│           ├── 09_revision_history.jsonl       每轮修订的 plan 留痕
│           ├── 10_image_prompts.md
│           ├── config.json                     active_template、run metadata
│           └── run.log
│
└── .claude/refactor/                              ★ 本重构项目自身的文档（就是你在读的这个）
    ├── README.md
    ├── ARCHITECTURE.md
    ├── SKILLS.md
    ├── PR_PLAN.md
    ├── FINDINGS.md
    ├── DECISIONS.md
    ├── MVM.md
    └── state/
        ├── current.md
        ├── progress.jsonl
        └── sessions/
            └── YYYY-MM-DD_*.md
```

---

## 四、完整数据流

```
═══ 阶段 C：安装期 ═══

  用户 docx 模板                     代理人范本（可选）
       │                                    │
       ▼                                    ▼
 /cnpatent-template-setup         /cnpatent-template-study
   (对话式，循环核验)                 (仅在用户有范本时跑)
       │                                    │
       ▼                                    ▼
 kit/templates/<fingerprint>/     kit/reference/section-
   ├── template.docx              requirements.md
   ├── template.meta.json
   ├── build_docx.py
   ├── verification.md
   └── verification_sample.docx
       │                                    │
       └──────────────┬─────────────────────┘
                      │
═══ 阶段 A：单次专利创作 ═══

   /cnpatent-pipeline 启动
      │
      ▼
   检测 .cnpatent/active_run
   ├── 新建 run → AskUserQuestion 询问 title
   │              生成 run-id = <date>-<slug>-<rand4>
   │              mkdir state/<run-id>/
   │              append runs.jsonl, 写 active_run
   └── 恢复 run → 读 state/<run-id>/ 当前阶段，询问是否继续
      │
      ▼
   打印 "当前 run: <id> (<title>), 上次到 <phase>, 下一步 <next>"
      │
      ▼
   idea 来源二选一
   ┌──────────────┴──────────────┐
   用户已有                   开源材料/论文
      │                             │
      │                             ▼
      │                 /cnpatent-ideate
      │                     → 00_ideas.json
      │                             │
      └──────────────┬──────────────┘
                     ▼
         /cnpatent-novelty-free + novelty-paid (并行)
                     │
                     ▼
         /cnpatent-shortlist  (L1 卡片筛选, 50→8)
                     │
                     ▼
         /cnpatent-deepread   (L2 精读, top-3~5 拉全文)
                     │
                     ▼
         /cnpatent-judge      (三步法判定, 绿/黄/红)
                     │ gate: 绿灯
                     ▼
   /plan-cnpatent-outline (可选 plan-mode 评审)
                     │ gate: 评审分 ≥ 8/10 或跳过
                     ▼
              05_verified_outline.md
                     │
                     ▼
     [多模板? 超过 1 个时 AskUserQuestion 选 active]
                     │
                     ▼
         /cnpatent-write
           (4 个真 subagent 并行，加载 learned-rules.md 硬约束)
                     │ gate: 每 section 写出
                     ▼
         /cnpatent-review (三 rubric)
                     │ gate: 一致性+抗幻觉+去AI 各 ≥ 75 分
                     ▼
         /cnpatent-humanize
                     │ gate: AI 痕迹分 < 30
                     ▼
         /cnpatent-build
           (canonical → active template 映射 → build_docx.py)
                     │ gate: DOCX 结构校验通过
                     ▼
              09_final.docx + 10_image_prompts.md
                     │
                     ▼
              交付给用户


═══ 修订学习回路 ═══

   用户在 Word 里标修订（tracked changes + 批注 + chat）
                     │
                     ▼  保存为 09_final.signed.docx
                     │
         /cnpatent-revise
           · 解析三路（tracked / comment / chat）
           · 生成 revision_plan.json
             每项带 user_learn / ai_learn_propose / decision
           · 展示 plan 给用户过目
           · 应用 → 09_final.v2.docx
                     │ 可循环 v2 → v3 ... 直到用户 accept
                     ▼
              最终 v_final 定稿
                     │
                     ▼
         /cnpatent-learn
           · diff(09_final, v_final)
           · 过滤 decision=false 的项
           · append 到 kit/corrections.jsonl（带锁）
                     │
                     ▼  （积累数天或几个 run 后，手动触发）
                     │
         /cnpatent-consolidate
           · 聚类相似 correction (≥3 occurrences, conf ≥0.7)
           · 为每簇提议新规则
           · AskUserQuestion 逐条晋升
           · 跑 golden/regression 验证
           · 通过的写入 kit/learned-rules.md
           · 被晋升的 correction 标记 "promoted"
                     │
                     ▼
           下次 /cnpatent-write 加载新 learned-rules.md 作为硬约束
           同类错误不再重复出现


═══ 阶段 B：批量训练（延后）═══

   20 份真实专利 PDF/docx
                     │
                     ▼
         /cnpatent-train (批量)
           for each patent:
             /cnpatent-ref-extract → extracted_outline.md
             /cnpatent-write → ai_draft.md
             /cnpatent-learn (比对模式) → correction
                     │
                     ▼
              积累一大批 correction
                     │
                     ▼
         /cnpatent-consolidate (一次性大批量晋升)
                     │
                     ▼
              learned-rules.md 跃迁式充实
```

---

## 五、Run 生命周期

### Run 注册表结构 `.cnpatent/runs.jsonl`
```jsonl
{"run_id":"2026-04-18-fluid-coupling-a1b2","title":"流体耦合齿轮","created":"2026-04-18T14:22:00","last_active":"2026-04-18T16:00:00","phase":"judge_passed","template":"fp_abc123","status":"active"}
{"run_id":"2026-04-15-pcb-thermal-c3d4","title":"PCB热管理","created":"2026-04-15T10:00:00","last_active":"2026-04-16T18:00:00","phase":"delivered","template":"fp_abc123","status":"completed"}
{"run_id":"2026-04-10-motor-ctrl-e5f6","title":"电机控制","created":"2026-04-10T09:00:00","last_active":"2026-04-12T15:30:00","phase":"humanize","template":"fp_abc123","status":"paused"}
```

### 活跃指针 `.cnpatent/active_run`
单行文件，仅记录当前 active run-id：
```
2026-04-18-fluid-coupling-a1b2
```

### 显式声明契约
每个 skill 首次动作前打印：
```
当前 run: 2026-04-18-fluid-coupling-a1b2 (流体耦合齿轮)
上次阶段: judge_passed (三步法绿灯)
下一步: /plan-cnpatent-outline 或 /cnpatent-write
```

### Pipeline 启动检测流程
```
读 .cnpatent/active_run
├── 不存在/空:
│     → 首次使用，AskUserQuestion "这份专利叫什么？"
│     → 生成 run-id, mkdir state/<run-id>/, 追加 runs.jsonl, 写 active_run
├── run-id 有效（目录存在）:
│     → 读 state/<run-id>/config.json 的 phase
│     → AskUserQuestion "继续 run X (上次到 Y)，还是开新的？"
└── run-id 无效（目录被删等）:
      → 报错，展示 runs.jsonl 让用户选
```

---

## 六、学习回路（两层 + 人审晋升）

```
Layer 1: corrections.jsonl (原始，append-only)
    ↓  by /cnpatent-learn
    
    每条结构:
    {
      "id": "c042",
      "run_id": "2026-04-18-fluid-coupling-a1b2",
      "type": "phrasing" | "structure" | "vocab" | "tone" | "global_style",
      "section": "二",
      "before": "本发明提出了一种...",
      "after":  "本发明涉及...",
      "source": "tracked" | "comment" | "chat" | "pdf_diff",
      "user_learn": null | true | false,
      "ai_learn_propose": true,
      "ai_learn_reason": "法定开篇风格，跨专利通用",
      "decision": true,
      "confidence": 0.9,
      "created": "2026-04-18T15:30:00",
      "status": "active" | "promoted" | "superseded" | "rejected"
    }
    
    ↓  聚类条件：≥3 条相似 correction, 平均 conf ≥0.7
    ↓  触发：手动 /cnpatent-consolidate
    
Layer 2: learned-rules.md (晋升，只追加)
    
    每条规则:
    ## R042 [section: 二] [promoted: 2026-04-20] [approved_by: user]
    **规则**：二段法定开篇使用"本发明涉及..."，不得使用"本发明提出了一种..."
    **来源 corrections**: c042, c089, c103
    **测试用例**: golden/rule-application/R042_*.md
    
    ↓  加载方式
    
    /cnpatent-write 启动时:
      prompt = base_prompt
             + patent-voice.md
             + terminology-lock.md
             + de-ai-rules.md
             + learned-rules.md  ← 作为硬约束，不是 few-shot example
             + writer_specific_prompt
```

**为什么这样能达到"永久学会"**：
- 规则不靠 retrieval，每次都加载完整 `learned-rules.md`
- 规则是显式约束文字，不是 example 让模型"模仿"
- 同类错误被一条规则永久覆盖，不会反复出现
- 用户可以随时检查 `learned-rules.md` 内容，可读可审
- 规则可单条回滚（id 找到就能去除）

---

## 七、并发安全

共享文件只有两个会写：

| 文件 | 写入者 | 保护 |
|------|-------|------|
| `corrections.jsonl` | `/cnpatent-learn` | flock/msvcrt 文件锁，锁失败快停 |
| `learned-rules.md` | `/cnpatent-consolidate` | 同上，天然单用户手动场景 |

其他都是只读（模板、规则文件）或 per-run 隔离（state/<run-id>/）。

两个 session 并行：
- 各自的 active_run 指向不同 run-id → state 目录无冲突
- 同时跑 /cnpatent-learn：后者锁失败，提示"另一个 session 正在学习"，用户稍后重试

---

## 八、设计权衡记录

| 权衡点 | 选择 | 放弃的 |
|--------|------|-------|
| 书写并行 | 真 subagent | 主 context 里伪 agent role-play |
| 跨 skill 交接 | Artifact-only | 共享 context |
| 模板策略 | fingerprint + 一对一 build 脚本 | 通用 build + runtime 参数化 |
| 中间产物 | canonical 内核 | 按模板变结构 |
| 学习机制 | 两层 + 人审晋升 | 纯 few-shot 注入 |
| Playwright 策略 | YAML recipe 死脚本 | AI 解读 DOM 自适应 |
| 查新 token | L1 + L2 分层 | 全文全进 context 或纯摘要 |
| Run 并发 | 显式 active_run + 文件锁 | 隐式推断 |
| Skill 粒度 | 19 个窄职责 | 3 个大 skill |
| 老机制 | 先核验后采纳（MVM） | 原样保留 / 全部重写 |
