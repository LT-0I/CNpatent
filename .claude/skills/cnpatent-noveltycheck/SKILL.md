---
name: cnpatent-noveltycheck
description: >
  Chinese patent novelty + inventiveness pre-screening skill (中国发明专利新颖性 + 创造性初筛).
  This is the ONLY entry point for the cnpatent patent writing pipeline — cnpatent skill
  has been refactored to require a verified outline from this skill and no longer accepts
  raw paper + domain input. The workflow has three phases: Phase A auto-searches free
  databases (Google Patents, CNIPA pss-system, PATENTSCOPE, Google Scholar, arXiv) and
  generates a draft patent outline with first-pass novelty check. Phase B generates an
  operation guide that instructs the user through manual verification in paid databases
  (incoPat by default via campus IP) plus non-patent literature (Google Scholar, arXiv,
  CNKI). Phase C reads the user-filled search results, applies the 2023 CNIPA 专利审查指南
  three-step method (三步法) for inventiveness judgment, and outputs a green/yellow/red
  light decision. Green light triggers cnpatent skill for full patent writing. Use this
  skill whenever the user wants to write a Chinese invention patent from reference
  materials (academic papers, R&D notes, open-source projects) — it MUST run before
  cnpatent. Triggers on phrases like 写专利, 写交底书, 帮我写个发明专利, 专利查新, 专利新颖性,
  专利创造性, 专利技术交底书, novelty search, prior art check, 查新查重.
---

# cnpatent-noveltycheck — 中国发明专利新颖性 + 创造性初筛

> 在耗费资源写完整篇专利之前，通过自动免费库筛查 + 手动付费库核查两轮流程，按中国专利法新颖性 + 创造性标准判断方案是否值得申请。**绿灯通过才触发 cnpatent skill 进入正式书写**。

## 核心定位

**cnpatent 的唯一入口**。cnpatent skill 已经被改造为只接受本 skill 产出的 `5_verified_outline.md` 作为输入，不再独立接受参考文献 + 领域的输入。用户要写中国发明专利，必须从本 skill 开始。

**为什么这样设计**：前置查新关卡防止 AI 基于参考文献编造"创新点"写出实际上已被他人申请的专利。写完整篇专利后才发现撞车，成本远大于前置筛查。

### Playwright MCP（可选但推荐）

Phase B.2 支持两种模式：

| 模式 | 依赖 | 用户时间 | AI 时间 |
|---|---|---|---|
| Playwright 自动化（默认） | Playwright MCP server | ~5 min（登录） | ~30 min |
| 用户手动（降级） | 无 | 70-110 min | 0 |

安装 Playwright MCP：
```bash
claude mcp add playwright -- npx -y @playwright/mcp@latest
```

若已安装：Phase B.2 由 6 个 AI 后台 subagent 并行完成（用户仅登录）。
若未安装：降级为 v1.1 用户手动模式。配置在 `user_profile.yml` 的 `playwright:` 段。

## Quick Start

调用本 skill 时，先做状态检测决定从哪一步开始：

```
outputs/[方案名]/
  └─ 5_verified_outline.md 存在 ────────→ 触发 cnpatent (Phase D)
  └─ 4_manual_search_template.md 已填 ──→ 执行 Phase C
  └─ 3_manual_search_guide.md 存在 ─────→ 提醒用户完成人工核查
  └─ 以上都不存在 ──────────────────────→ 从 Phase A 开始
```

这个检测逻辑让用户可以在 Phase B 之后离开，做完人工核查再回来继续。

---

## 必需输入

| 项 | 必需 | 形式 | 用途 |
|---|:---:|---|---|
| **参考文献** | 是 | PDF / DOCX / URL / 文本 | 技术内容来源，由 pdf/docx skill 读取 |
| **目标应用领域** | 是 | 自由文本 | 领域迁移 + IPC 预估 + 场景化创新点 |
| 已知相关专利 | 否 | 专利号 / 标题 | 检索起点扩展 |
| 已知相关论文 | 否 | DOI / arXiv ID | 检索起点扩展 |
| 方案是否已公开过 | 否 | 日期 + 形式 | 宽限期判断（专利法 24 条） |

若用户未提供目标应用领域，skill **必须主动询问**，不得自行假设。

---

## 铁律

### 铁律 1 — 本 skill 是 cnpatent 的唯一入口

cnpatent 不能独立使用。用户若直接调 cnpatent，cnpatent 会检测 `5_verified_outline.md` 是否存在，不存在则拒绝执行并提示用户先运行本 skill。

### 铁律 2 — 自动筛查不能替代人工核查

Phase A 的免费库检索只能做"提示性判断"，不能据此得出"方案具备新颖性"的结论。**必须**走完 Phase B 和 Phase C 才能出绿灯。唯一可以直接跳过 Phase B/C 的情况是 Phase A 发现了破坏新颖性的命中 —— 此时可以直接走红灯。

### 铁律 3 — 三步法必须按 2023 审查指南

Phase C 的创造性判断必须严格遵循 2023 年版《专利审查指南》的三步法，关键点：
- 实际解决的技术问题**基于区别特征的实际技术效果**，不是说明书声称的问题
- 公知常识证据来源包括教科书、技术词典、技术手册
- 技术启示的四种来源：同一文件其他部分 / 另一文件 / 公知常识 / 惯用手段

详见 [references/cn-patent-law.md](references/cn-patent-law.md)。

### 铁律 4 — 三色灯决定下一步

| 灯 | 新颖性 | 创造性 | 下一步 |
|:---:|:---:|:---:|---|
| 🟢 绿 | 低 | 低-中 | 写 `5_verified_outline.md` → Phase D 触发 cnpatent |
| 🟡 黄 | 低 | 中-高 | 写 `5_adjustment_suggestions.md` → 用户手动重跑 Phase A |
| 🔴 红 | 中-高 | 任意 | 写 `5_rejection_report.md` → 方案放弃或大改 |

Judge agent **不得输出替代大纲或大段重写**。黄灯只能给出调整方向建议。

### 铁律 5 — 信息源锚定（防幻觉）

所有检索结果、特征对比、三步法推理必须可追溯：
- 每个命中文件标注专利号 / 论文 DOI / arXiv ID
- 每个特征对比的"公开 / 未公开"判断必须标注依据的段落号
- 每个风险判断必须引用具体的命中文件
- 无法确认时标 `[待核查:具体问题]`，禁止编造

---

## 执行流程

### Phase A — 自动筛查 + 草稿大纲生成

**Agent**：`cnpatent-noveltycheck-screener`（角色文件 [agents/cnpatent-noveltycheck-screener.md](agents/cnpatent-noveltycheck-screener.md)）

**模型**：opus（强制，orchestrator 显式传 `model="opus"`）

**输出文件**：

```
outputs/[方案名]/
├── 0_input_summary.md         # 素材要点 + 领域迁移推演
├── 1_auto_novelty_report.md   # 免费库检索报告 + 三步法预判
└── 2_candidate_outline.md     # 带查新标注的大纲草稿 (cnpatent 格式)
```

**步骤**：

1. 读取用户参考文献（通过 pdf / docx skill）
2. 提取潜在创新点（delta，不是整个方案）
3. 领域迁移推演：映射到目标领域的工程约束
4. 构建中英双语关键词块（至少 3 组）
5. 预估 2-4 个核心 IPC 分类号（电学 / 软件 / 算法类参考 [references/search-methodology.md](references/search-methodology.md) 的 IPC 列表）
6. 并行调用 WebSearch 查 5 个免费库：
   - Google Patents（含 Prior Art Finder）
   - CNIPA pss-system
   - WIPO PATENTSCOPE CLIR
   - The Lens
   - Google Scholar + arXiv
7. 每库 Top 20 读摘要，筛出 Top 5-10 精读
8. 构建特征对比表（目标 vs 命中 per feature）
9. 做三步法预判（最接近现有技术 + 区别特征 + 实际技术问题 + 显而易见性）
10. 输出大纲草稿 `2_candidate_outline.md`，**使用 cnpatent 的大纲 schema**（主旨四段式 / 三方对应 / 术语锁定，见 [references/templates.md](references/templates.md)）

**约束**：
- 至少两库交叉，不得基于单一库下结论
- 每个特征对比必须可追溯到原文段落
- 如 Phase A 已发现破坏新颖性的命中，Screener 可直接建议走红灯，跳过 Phase B/C

### Phase B — 两阶段核查（v1.1：B.1 AI 精读 + B.2 用户付费库）

v1.1 把 Phase B 拆成两个子阶段。背景、动机和完整设计见 [DESIGN.md §17](DESIGN.md)。

**Phase B.1 —— AI 自动精读公开资源**（必做，AI 执行，用户无需在场）

对 Phase A 的 Top 5-10 命中，由 Guide agent 生成 AI 精读卡片，orchestrator 随后派发 `subagent_type="general-purpose"` 的子 agent 并行执行：

- **摘要-全文交叉核实卡**（所有 Top 命中必做）—— 核实 Phase A WebSearch 返回的摘要是否与原文一致，防止 hallucination 传染后续 Judge 判断
- **arXiv 全文精读卡** —— 命中是 arXiv / openaccess 论文时生成
- **GitHub 源码精读卡** —— 命中是 GitHub 开源项目时生成

精读产物直接写入 `4_manual_search_template.md` 的"命中 #N · B.1 全文核实"字段。

**Phase B.2 —— AI Playwright 自动化检索**（必做，AI 后台 subagent 执行，用户仅需登录）

v1.2 把原来的用户手动付费库检索改为 AI 驱动的 Playwright 浏览器自动化。用户只需在 Playwright 打开的浏览器中完成登录（~5 分钟），AI 后台 subagent 负责查询注入、结果提取、评分和模板填写。

**6 通道全部后台 subagent 并行**：

| 通道 | Tab | 执行者 | 工具 |
|---|---|---|---|
| incoPat 命令检索 | T1 (tab 0) | 后台 subagent | Playwright |
| incoPat 语义检索 | T2 (tab 1) | 后台 subagent | Playwright |
| incoPat 抵触申请 | T3 (tab 2) | 后台 subagent | Playwright |
| CNKI 高级检索 | T6 (tab 3) | 后台 subagent | Playwright |
| Google Scholar | — | 后台 subagent | WebSearch |
| arXiv | — | 后台 subagent | WebSearch |

主 session 不执行任何 Playwright 操作，只负责派发和合并。DOM 操作脚本固化在 `scripts/playwright/*.js`。

**前置依赖**：Playwright MCP server（`claude mcp add playwright -- npx -y @playwright/mcp@latest`）

**降级策略**：若 Playwright MCP 不可用，回退到 v1.1 用户手动模式（Guide 生成操作卡片，用户手动检索 70-110 分钟）。

**Agent**：`cnpatent-noveltycheck-guide`（角色文件 [agents/cnpatent-noveltycheck-guide.md](agents/cnpatent-noveltycheck-guide.md)）

**模型**：opus（Guide 本身）+ sonnet（B.1 子 agent，结构化精读不需要 opus）

**输出文件**：

```
outputs/[方案名]/
├── 3_manual_search_guide.md      # 第一大节 Phase B.1 卡片 + 第二大节 Phase B.2 卡片
└── 4_manual_search_template.md   # 含 B.1 全文核实字段 + B.2 用户填写字段
```

**步骤**：

1. 读 `1_auto_novelty_report.md` 提取关键词块 + IPC
2. 读 `user_profile.yml` 获取用户付费库访问清单
3. **Phase B.1 卡片生成**：为 Top 5-10 命中生成 AI 精读卡片（卡片模板和派发协议见 [references/phase-b1-ai-read-cards.md](references/phase-b1-ai-read-cards.md)）
4. **Phase B.2 卡片生成**：为每个可访问的付费库生成用户操作卡片（URL / 登录方式 / 检索式 / 字段代码 / 步骤 / 停止准则）
5. 生成非专利库操作卡片（Google Scholar + arXiv + CNKI），归入 B.2
6. 生成回填模板，同时包含 B.1 核实字段和 B.2 用户填写字段

**orchestrator 在 Phase B.1 的执行协议**：Guide agent 返回后，orchestrator 读 `3_manual_search_guide.md` 的第一大节，对每张 B.1 卡片 `Agent` 工具派发一个子 agent（最多 10 张卡片并行），子 agent 执行后把结果写入 `4_manual_search_template.md` 的对应字段。Phase B.1 总耗时约 15-30 分钟 wall clock（并行）。完成后才进入 B.2 的"人类工作时段"提示。

**orchestrator 在 Phase B.2 的执行协议**（Playwright 模式）：

1. 检测 Playwright MCP 是否可用
   - 可用 → Playwright 模式
   - 不可用 → 降级为 v1.1 用户手动模式（生成操作卡片，暂停等用户手动检索）
2. 启动 Playwright 浏览器
3. **IP 登录 + 验证**（v1.2.1 新增，失败才退回用户手工登录）：
   - 读 `user_profile.yml` 的 `playwright.auto_login.enabled`，若为 false 跳到步骤 4
   - **IP 登录机制**：incoPat/CNKI 对校园 IP 段自动发回登录态 cookie，不需要表单/密码/点按。生效条件是 **Claude Code 本身运行在校园 IP 段内**（Playwright MCP 是本地子进程，出口 IP 等于 Claude Code 的 IP）
   - orchestrator 按 `playwright.tabs` 顺序 `browser_tabs new` + `browser_navigate` 打开 4 个标签页
   - 每个标签页 `browser_evaluate` 跑 `scripts/playwright/incopat_check_login.js` 或 `cnki_check_login.js` 验证 IP 登录是否生效
   - 若 `verify_tabs: all` 且 **4/4** 都返回 `logged_in: true` → 跳过人类工作时段，直接进入步骤 5
   - 若任一 tab 返回 `logged_in: false` → 按 `on_failure` 处理：`manual_prompt` 退回步骤 4；`abort` 终止
4. 提示用户登录（见下方"人类工作时段"），用户确认后继续
5. 读 Guide 输出的 B.2 执行计划（`3_manual_search_guide.md` 第二大节）
6. 在一条消息里同时派发 6 个后台 subagent：
   - 每个 Playwright subagent 收到：该通道的执行指令 + 脚本路径 + 输出路径 + 区别特征列表
   - 每个 WebSearch subagent 收到：查询表达式 + 输出路径
   - 每个 subagent 独立完成检索并写入 `.omc/research/<channel>/queryN.json`
7. 所有 subagent 完成后，orchestrator 按 [references/phase-b2-merge-rules.md](references/phase-b2-merge-rules.md) 执行：**同族合并在 incoPat 站内完成**（subagent 调 `incopat_merge_family.js`，512 条 → 364 族实测 29% 合并率）；orchestrator 只做跨通道同 `pn` / 同 `an` 合并 + Phase A 去重标记 + 相关性评分，写入 `4_manual_search_template.md` B.2 字段

**约束**（不变）：
- 检索式必须基于 Phase A 的关键词块 + IPC 构造，不得凭空编造
- 每个卡片必须给出停止准则
- 回填模板的字段必须对齐 Phase C judge 的解析格式
- B.1 子 agent 的精读结果必须附原文段落号或源码路径行号，无锚点的判定不被 Phase C Judge 采信

### ⏸ 人类工作时段

**Playwright 模式（v1.2 默认）**：

Phase B.1 执行完毕后，orchestrator 尝试 AI 自主登录：自动打开 4 个标签页 + 跑 `*_check_login.js` 脚本。

**路径 A —— IP 登录成功**（Playwright 出口 IP 在校园段 / 通过校园代理）：

```
✅ Phase B.1 完成。Phase B.2 IP 登录验证通过（4/4 标签页已登录）。
   - Tab 0 incoPat 命令检索: ✓ (#textarea 就绪)
   - Tab 1 incoPat 语义检索: ✓ (#querytext 就绪)
   - Tab 2 incoPat 抵触申请: ✓ (#textarea 就绪)
   - Tab 3 CNKI 高级检索: ✓ (检索表单就绪, 无 CAPTCHA)
开始 B.2 后台检索（约 30 分钟）。
```

orchestrator 立即派发 6 个后台 subagent，无需用户介入。

**路径 B —— IP 登录未生效，退回手工**：

```
⚠ Phase B.2 IP 登录验证失败（Tab 3 CNKI 未登录 — redirect to homepage）。

可能原因：
1. Claude Code 当前运行环境的出口 IP 不在校园/机构认可段内
2. CNKI 弹出滑块验证码阻止 IP 认证
3. 站点端 cookie 失效或账户绑定异常

退回手工模式。请在 Playwright 浏览器窗口中完成登录（~5 分钟），完成后告诉我 "标签页已开好"。
```

用户确认后，orchestrator 立即开始 B.2 自动化。

**用户手动模式（v1.1 降级）**：

若 Playwright 不可用，Phase B.1 完成后输出 v1.1 的原始提示：

```
✅ Phase B.1 完成（AI 精读）。Phase B.2 需要你在付费库手动完成：

1. 打开 outputs/[方案名]/3_manual_search_guide.md，查看第二大节 "Phase B.2 用户人工核查卡片"
2. 按 incoPat / CNKI 操作卡片执行检索
3. 将命中记录填入 outputs/[方案名]/4_manual_search_template.md 的 B.2 字段
4. 预计耗时 60-90 分钟
5. 完成后告诉我 "查新完成" 或 "人工核查完成"，我会继续 Phase C
```

然后 skill 本次调用结束。

### Phase C — 结果分析 + 决策

**触发条件**：用户告知人工核查完成，或 skill 检测到 `4_manual_search_template.md` 已填写（至少有一个命中的专利号字段非空）。

**Agent**：`cnpatent-noveltycheck-judge`（角色文件 [agents/cnpatent-noveltycheck-judge.md](agents/cnpatent-noveltycheck-judge.md)）

**模型**：opus

**输出文件**（三种之一）：

```
outputs/[方案名]/
├── 5_verified_outline.md           # 绿灯
   或
├── 5_adjustment_suggestions.md     # 黄灯
   或
├── 5_rejection_report.md           # 红灯
```

**步骤**：

1. 读用户填好的 `4_manual_search_template.md`
2. 读 `2_candidate_outline.md` 作为方案基线
3. 对每个标 "是 / 存疑" 的命中做单篇新颖性分析
4. 从所有命中选最接近现有技术
5. 做三步法创造性判断（按 2023 审查指南）
6. 扫描常见陷阱（上下位 / 等同 / 参数 / 公知组合）
7. 综合风险等级 → 三色灯决策 → 写对应的 5_*.md 文件

**三步法详细步骤见** [agents/cnpatent-noveltycheck-judge.md](agents/cnpatent-noveltycheck-judge.md) 和 [references/cn-patent-law.md](references/cn-patent-law.md)。

**约束**：
- 三步法每一步必须给出显式推理 + 引用依据
- 绿灯必须引用原文段落证明无破坏新颖性命中
- 红灯必须明确指出破坏新颖性的文件号和段落
- 黄灯必须给出具体调整方向，**不得**输出替代大纲

### Phase D — 绿灯触发 cnpatent

**仅在 Phase C 绿灯时执行**。

**步骤**：

1. 确认 `5_verified_outline.md` 已写入
2. 验证文件 schema 完整（含主旨四段式 / 三方对应 / 术语锁定 / 附图清单 / 步骤拆分）
3. 在聊天窗口告知用户：

```
🟢 新颖性 + 创造性初筛通过。

- 新颖性风险: 低
- 创造性风险: 低-中
- 最接近现有技术: [命中号]
- 区别技术特征: [列表]

现在自动进入 cnpatent skill，开始生成专利技术交底书（.docx）。
```

4. **调用 Skill 工具**：`Skill(skill="cnpatent")`。cnpatent 的 Phase 0 会检测并读取 `5_verified_outline.md`，不再需要用户输入。

---

## 与 cnpatent 的集成

### 集成点

`5_verified_outline.md` 必须使用 cnpatent 的原生大纲 schema。字段包括：

```
▍主旨四段式（全文骨架）
  ① 针对什么问题
  ② 采取什么方法
  ③ 基于什么原理
  ④ 带来什么提升

一、发明名称
二、技术领域
三、背景技术要点 (含编号局限对应三方)
四·发明目的要点 (含优势条目对应三方)
四·技术解决方案要点 (含编号步骤)
四·技术效果要点 (含效果条目对应三方)
五、预计附图清单
六、具体实施方式·步骤拆分 (含 Writer-C/D 分工)
七、术语锁定表
八、篇幅预算
九、查新验证元信息    ← 本 skill 新增字段，记录审查状态
```

详细 schema 见 [references/templates.md](references/templates.md) 的"verified_outline 格式"章节。

### cnpatent 的改造

cnpatent Phase 0 被改造为：

1. 检测 `outputs/[方案名]/5_verified_outline.md`
2. 若不存在 → 拒绝执行并提示用户先走 cnpatent-noveltycheck
3. 若存在 → 复制内容到 `outputs/[方案名]/01_outline.md`（保留原文件）
4. 直接进入 Phase 1（多 Writer 并行）
5. **跳过原来的用户确认点** —— 确认已在本 skill Phase C 完成

### 失败降级

如果 cnpatent 在 Phase 0 检测到 schema 不完整（比如字段缺失 / 术语锁定表为空），它会退回到 cnpatent-noveltycheck 并要求补充。这是最后一道保险。

---

## 工作目录

本 skill 和 cnpatent 共享工作目录 `outputs/[方案名]/`。完整布局：

```
outputs/[方案名]/
│
│ 本 skill 产物 ────────────
├── 0_input_summary.md
├── 1_auto_novelty_report.md
├── 2_candidate_outline.md
├── 3_manual_search_guide.md
├── 4_manual_search_template.md       # 用户回填
├── 5_verified_outline.md             # 绿灯 —— 或下面两者之一
├── 5_adjustment_suggestions.md       # 黄灯
├── 5_rejection_report.md             # 红灯
│
│ cnpatent 产物 ──────────────
├── 01_outline.md                     # 从 5_verified_outline.md 复制而来
├── sections/
│   ├── 1_name.md
│   ├── 2_field.md
│   ├── 3_background.md
│   ├── 4a_purpose.md
│   ├── 4b_solution.md
│   ├── 4c_effect.md
│   ├── 5_figures.md
│   └── 6_implementation.md
├── [专利名称]_专利技术交底书.docx       # 最终交付
└── [专利名称]_全套AI生图提示词.md     # 附图提示词
│
│ Playwright 原始数据（v1.2）──
.omc/research/
├── incopat_command/query*.json   # incoPat 命令检索原始结果
├── incopat_semantic/query*.json  # incoPat 语义检索原始结果
├── incopat_conflict/query*.json  # incoPat 抵触申请原始结果
├── cnki/query*.json              # CNKI 原始结果
├── scholar/query*.json           # Scholar 原始结果
└── arxiv/query*.json             # arXiv 原始结果
```

**设计原则**：
- 过程文件（审查报告 / Writer 草稿 / 回填前模板）不落盘
- 只保留"可编辑的最终态"和"最终交付"
- 如需版本追溯，用户自行在 `outputs/[方案名]/` 做 `git init`

---

## 用户配置

用户付费库访问清单在 `user_profile.yml`：

```yaml
# 位置: .claude/skills/cnpatent-noveltycheck/user_profile.yml
# 当前默认配置

paid_access:
  incopat:
    available: true
    auth: campus_ip      # 无需注册，校园 IP 登录
    quota: unlimited
  patsnap: false
  derwent: false
  orbit: false

free_access:
  cnipa_pss: true
  google_patents: true
  patentscope: true
  lens: true

non_patent:
  google_scholar: true
  arxiv: true
  cnki:
    available: true
    auth: campus_ip
```

**修改方式**：用户未来获得新库访问时，直接编辑 `user_profile.yml`。Phase B 的 Guide agent 会根据此文件动态生成操作卡片。

---

## 已知局限

1. **免费库检全率有限** — Phase A 的绿灯提示不可信，必须走 Phase B
2. **AI 幻觉风险** — 特征对比可能读错原文，Phase C 必须有引用原文的硬约束
3. **抵触申请覆盖不全** — 仅依赖 incoPat 的未公开申请检索功能
4. **宽限期自我公开不豁免** — 中国专利法 24 条不包括申请人自己的公开（与美日欧不同）
5. **非中英文献覆盖弱** — 日文 / 德文 / 俄文专利或论文漏检率较高
6. **不构成法律意见** — 仅为初筛，最终判断须由专利代理人和 CNIPA 审查员做出

详细局限与缓解策略见 [DESIGN.md](DESIGN.md) §13-14。

---

## 参考文档

- [DESIGN.md](DESIGN.md) 完整架构设计
- [references/database-catalog.md](references/database-catalog.md) 数据库分层 + 每库详情
- [references/search-methodology.md](references/search-methodology.md) 检索方法论
- [references/cn-patent-law.md](references/cn-patent-law.md) 新颖性 + 创造性 + 宽限期
- [references/templates.md](references/templates.md) 所有模板（操作卡片 / 回填 / verified_outline）
- [agents/README.md](agents/README.md) 角色文件约定（同 cnpatent）
- [scripts/playwright/README.md](scripts/playwright/README.md) Playwright 自动化脚本 + DOM 模式 + 踩坑记录

## 下游 skill

- **cnpatent** — 绿灯后自动触发，完成专利技术交底书的 .docx 生成
