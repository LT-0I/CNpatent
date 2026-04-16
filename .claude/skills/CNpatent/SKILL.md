---
name: CNpatent
description: >
  Chinese invention patent technical disclosure writer (专利技术交底书生成器, 下游书写环节).
  **This skill is the DOWNSTREAM component of the CNpatent-noveltycheck workflow and
  is NOT meant to be invoked directly**. It transforms a novelty-verified outline
  (`5_verified_outline.md` produced by CNpatent-noveltycheck Phase C green light)
  into a CNIPA-compliant technical disclosure document (.docx) in the electrical
  (电学类) disclosure format, with numbered sections 一～六 (发明名称、技术领域、
  背景技术、发明内容、附图说明、具体实施方式). The disclosure does NOT include
  section 七 (权利要求书) — claims are drafted separately by the patent agent.
  When the user asks to write a Chinese patent disclosure, Claude should
  **FIRST invoke CNpatent-noveltycheck skill** (the entry point for the patent
  writing pipeline), which runs novelty + inventiveness screening and then
  automatically triggers this CNpatent skill on green light. If the user directly
  tries to invoke this skill without a verified_outline, Phase 0 will detect the
  missing file, refuse to execute, and instruct the user to run CNpatent-noveltycheck
  first. Do NOT use this skill for raw paper + domain inputs — that workflow was
  moved to CNpatent-noveltycheck.
---

# CNpatent — 中国发明专利技术交底书生成器（电学类格式）

> 将学术论文、研发笔记、开源项目等素材转化为符合代理机构电学类格式的专利技术交底书（.docx）。
> 输出文档包含 一～六 节（发明名称 / 技术领域 / 背景技术 / 发明内容 / 附图说明 / 具体实施方式），**不包含** 七、权利要求书，权利要求书由专利代理人根据交底书另行撰写。

## Quick Start

本 skill **不再独立接受参考素材 + 领域作为输入**。CNpatent 现在是 CNpatent-noveltycheck 工作流的下游环节，只接受经查新验证的大纲作为输入。

1. **检测** `outputs/[专利名称]/5_verified_outline.md` 是否存在（由 CNpatent-noveltycheck 的 Phase C 生成）
2. 若**不存在** → 拒绝执行，提示用户先运行 CNpatent-noveltycheck skill，本次调用结束
3. 若**存在** → 读入 `5_verified_outline.md` 的内容，验证 schema 完整性（含主旨四段式 + 三方对应 + 术语锁定 + 九、查新验证元信息）
4. 复制内容到 `outputs/[专利名称]/01_outline.md`（保留原 `5_verified_outline.md` 文件不动）
5. **跳过用户确认环节** —— 大纲确认已在 CNpatent-noveltycheck Phase C 完成
6. 自动执行：4 个 Writer 并行生成 → Reviewer 三重审查 → 整合写入 .docx
7. 工作目录保留 `01_outline.md` 和 `sections/*.md`（8 个章节文件，DOCX 写入前的最终文本）
8. 自动静默触发 Phase 5，生成防幻觉 AI 附图提示词
9. 用户编辑任意 `sections/*.md` 后只需重跑 Phase 3 即可重新生成 DOCX；附图修正走 Phase 6

---

## 必需输入 (Required Inputs)

本 skill 的**唯一输入**是 CNpatent-noveltycheck 生成的经查新验证大纲：

| 输入项 | 必需 | 说明 |
|--------|:----:|------|
| **`outputs/[专利名称]/5_verified_outline.md`** | 是 | 由 CNpatent-noveltycheck Phase C 绿灯输出的 verified_outline，含九、查新验证元信息 |

**原来的参考素材 + 目标应用领域输入已被移除**。这些输入由 CNpatent-noveltycheck 处理，场景迁移、微创新设计、查新查重、大纲生成、用户确认都在前置 skill 完成。CNpatent 只负责"大纲到 .docx"的写作阶段。

**设计原因**：
- 防止 AI 基于参考文献编造"创新点"写出已被他人申请的专利
- 写完整篇专利后才发现撞车，成本远大于前置筛查
- 保留 CNpatent 内部的多 Writer 并行写作 + Reviewer 审查架构不变，只改入口

**如果用户直接调 CNpatent**（例如说"帮我写专利交底书"），skill 会检测 verified_outline 不存在，拒绝执行并指引用户走 CNpatent-noveltycheck。

---

## 铁律 (Core Execution Constraints)

### 铁律 1：模板驱动，严禁从零创建

本 Skill 使用的模板是 **电学类专利申请技术交底书** (`assets/交底书模板.docx`)。生成 .docx 时**绝对禁止创建空白文档**，必须加载内置模板。所有 docx 操作通过 `scripts/cnpatent_docx.py` 提供的辅助函数进行：

```python
import sys
from pathlib import Path

skill_root = Path.cwd() / '.claude' / 'skills' / 'CNpatent'
if not skill_root.exists():
    skill_root = Path.home() / '.claude' / 'skills' / 'CNpatent'
sys.path.insert(0, str(skill_root / 'scripts'))

from cnpatent_docx import (
    load_template, clear_placeholders, get_section_anchors,
    insert_before, append_at_end, add_formula, add_caption,
    para_replace, verify_docx,
)

doc = load_template()
```

**Why**：模板包含 CNIPA 提交所需的页面布局、页眉页脚、字体设置、段落样式表。从零创建会丢失这些，且字体/字号无法保证一致；让模板样式表决定一切，Python 端一个字体属性都不应该覆盖。

**模板结构**（详见 [docx-patterns.md](references/docx-patterns.md)）：模板共 18 段、0 表，包含 9 个标题段（6 H1 + 3 H2）+ 少量占位段。可用样式：

- `Heading 1` / `Heading 2` — 一/二级标题（必须原样保留）
- `Normal` — 普通正文段
- `Caption` — 附图说明的图题段
- `公式` — 数学公式段（纯文本 LaTeX）
- `图片` — 图片占位段

执行要求：
- 加载模板后，先调用 `clear_placeholders(doc)` 清除预留空段、`Caption` 段和 `图片` 占位段
- 9 个 Heading 段必须**原样保留**，不得改动文字、样式或顺序
- 写入策略：`get_section_anchors(doc)` 找到下一个 Heading 段，`insert_before(下一标题, doc, text)` 将新内容插入其前；六节是最后一节，用 `append_at_end(doc, text)` 追加
- 始终另存为新文件 `[专利名称]_专利技术交底书.docx`，**不得覆盖模板**

### 铁律 2：纯文本 LaTeX 公式

所有数学公式以**纯文本 LaTeX 字符串**写入文档，写入时使用模板的 `公式` 段落样式：
- 行内公式：`$E = mc^2$`（嵌入正文句子中，单 `$` 包裹）
- 独立公式：`$\sum_{i=1}^{N} x_i$　　（1）`（单独成段，左右各一个 `$` 包裹，编号在 `$` 外部，不使用 `$$`）
- 公式段必须用 `add_formula(doc, latex_text)` 辅助函数写入（见 [docx-patterns.md](references/docx-patterns.md)），该函数将段落 `style` 设为 `公式`
- 公式字符串必须用 Python **原始字符串字面量** `r'...'`，否则 `\a` / `\b` / `\f` 会被解释为控制字符，导致 docx 写入失败
- 公式**仅出现**在「六、具体实施方式」中，**严禁出现**在「四、发明内容」中（发明内容不写公式）

### 铁律 3：去 AI 痕迹（三层过滤）

生成专利文本时，必须经过**三层过滤**确保无 AI 写作痕迹：

**第一层 — 写作时预防**：每个 Writer Agent 的 prompt 中注入 [writing-rules.md](references/writing-rules.md) 的完整禁用词表，要求写作时即主动避免使用禁用词和 AI 高频句式。

**第二层 — 自动扫描替换**：Writer 完成输出后，对文本执行正则扫描，自动替换命中的禁用词（见 [writing-rules.md](references/writing-rules.md) 的禁用词表及"最终 DOCX 写入前自动替换"章节）。

**第三层 — Reviewer 终审**：Reviewer Agent 执行以下深度检查：
- a）禁用词残留扫描（逐词比对禁用词表）
- b）句式结构检测：平行结构、段落均匀度、三段式凑数、连续关联词（见 [writing-rules.md](references/writing-rules.md) 的"句式结构检测规则"章节）
- c）同义词轮换检测：同一技术概念是否全文术语统一
- d）调用 `CNpatent-humanizer` skill 做最终人类化润色

不合格内容退回对应 Writer 修正，最多 2 轮。最终文本必须符合专利文书的严谨、客观、技术性风格，读起来像领域工程师而非 AI 所写。

### 铁律 4：防幻觉附图提示词

主文档生成完毕后，自动静默触发 Phase 5。提示词必须遵守四条铁律：

**① 空间锚定**：中文标签必须绑定到具体视觉区块。
- 正确：`"A rectangular block on the top left, labeled explicitly with the Simplified Chinese text '位置编码'"`
- 错误：在末尾笼统列出词汇表

**② 公式极简化**：严禁让 AI 绘制复杂积分/求和/矩阵。仅用单字母（σ, c, T_i）或中文方块代替。

**③ 精准提取中文**：逐图从专利原文提取必需的中文标签，不多不少。

**④ 绝对排他禁令**：每段提示词末尾必须加全大写警告：
```
STRICT WARNING: The diagram MUST ONLY contain the following Simplified Chinese
text labels: [词汇列表]. DO NOT GENERATE ANY OTHER TEXT, LETTERS, NUMBERS,
SYMBOLS, OR FAKE CHINESE CHARACTERS. DO NOT ADD ANY FORMULAS OR EQUATIONS.
DO NOT INVENT ADDITIONAL LABELS OR ANNOTATIONS.
```

**⑤ 静默写入**：提示词不输出到聊天窗口，直接写入 `[专利名称]_全套AI生图提示词.md`。
警告段落用 `> **STRICT WARNING:**` blockquote + bold 格式呈现。

### 铁律 5：信息源锚定（防幻觉）

生成专利文本时，所有技术内容必须可追溯到参考素材或用户确认的大纲：

1. **数值参数**：必须来自参考素材或用户在大纲中确认。Writer 内部标注 `[源:论文X节]` 或 `[源:大纲约定]`，该标注仅用于 Reviewer 审查，写入 DOCX 前自动移除
2. **公式**：须与参考素材原文比对，不得自行推导参考素材中不存在的新公式。领域化"蒙皮"释义除外（变量重新释义不算新公式）
3. **技术步骤**：须严格对应大纲中的步骤规划，不得自行增减步骤
4. **无法确认的内容**：禁止编造，必须标记为 `[待确认:具体问题]`。Reviewer 汇总所有 `[待确认]` 标记，在最终输出中以醒目格式提示用户补充
5. **Writer 的 token 上限**：每个 Writer Agent 单次输出不超过 3500 字，避免因输出过长导致后半段内容质量下降

### 铁律 6：严禁生成权利要求书

本 Skill 严禁主动生成或追加权利要求书相关段落。

**Why**：技术交底书是供专利代理人撰写权利要求书所用的**素材**，权利要求书本身是**法律文件**——涉及保护范围界定、独立/从属权利要求的技术特征拆分、新颖性创造性论证等专业判断。这两类文档的输出对象与责任主体都不同：交底书写给专利代理人，权利要求书写给审查员。让 LLM 自动生成权利要求书会带来严重的范围界定风险。

若用户明确要求生成权利要求书，应回复：
> 权利要求书由专利代理人根据交底书另行撰写，不属于技术交底书范畴。建议交由专利代理人处理。

---

## 执行流程 (Execution Protocol)

### Phase 0：大纲接收与 01_outline.md 初始化

> **前置关卡**：本 skill 是 CNpatent-noveltycheck 工作流的下游环节。Phase 0 的唯一任务是**接收前置 skill 产出的 verified_outline 并做格式适配**，不再做任何大纲生成或用户确认的工作。原来的场景迁移 / 微创新设计 / 主旨四段式推导 / 结构化大纲生成 / 用户确认**都已前移到 CNpatent-noveltycheck**。
>
> **角色文件**：本阶段 orchestrator 遵循 [`agents/cnpatent-planner.md`](agents/cnpatent-planner.md) 中定义的 Planner 协议。Planner 现在简化为 **verified_outline 适配器**，不再做原创大纲生成。

**步骤**：

1. **检测 verified_outline**：
   - 默认检测路径：`outputs/[专利名称]/5_verified_outline.md`
   - 若用户在调用时提供了工作目录路径，则在该路径下检测
   - 若未提供专利名称，从 verified_outline 的一、发明名称字段里推导

2. **文件不存在 → 拒绝执行**：

   在聊天窗口输出以下提示，然后**立即结束本次调用**：

   ```
   ❌ 未检测到 5_verified_outline.md.

   CNpatent 不再独立接受参考素材 + 领域的输入. 必须先通过 CNpatent-noveltycheck skill
   做新颖性 + 创造性初筛, 获得绿灯后才能调用本 skill.

   请运行 CNpatent-noveltycheck skill, 完成 Phase A → B → C 流程,
   获得 5_verified_outline.md 后再调用 CNpatent.
   ```

3. **文件存在 → 读入并做 schema 校验**：

   读 `5_verified_outline.md`. 必需字段（缺一即校验失败）：

   - ▍主旨四段式（含四要素）
   - 一、发明名称（≤25 字）
   - 二、技术领域（1 句双层定位）
   - 三、背景技术要点（含编号局限对应三方）
   - 四·发明目的要点（含编号优势条目）
   - 四·技术解决方案要点（含编号步骤）
   - 四·技术效果要点（含编号效果条目，与优势标题一字不差）
   - 五、预计附图清单（4-7 张）
   - 六、具体实施方式·步骤拆分（含 Writer-C/D 分工）
   - 七、术语锁定表（8-15 个核心术语）
   - 八、篇幅预算
   - 九、查新验证元信息（含 `novelty_verified: true` + 最接近现有技术 + 区别技术特征）

   **三方对应硬约束**：背景局限 N = 优势条目 N = 效果条目 N，且（k）优势标题与（k）效果标题一字不差。

   **校验失败**时在聊天窗口指出具体缺失的字段，建议用户回到 CNpatent-noveltycheck 修复，本次调用结束。

4. **校验通过 → 复制内容到 `01_outline.md`**：

   - 通过 `Read` + `Write` 把 `5_verified_outline.md` 的内容写入同目录的 `01_outline.md`
   - **保留原 `5_verified_outline.md` 文件不动**（这是 noveltycheck 的审计产物）
   - `01_outline.md` 是 CNpatent 后续所有 Writer agent 的统一输入源

5. **跳过用户确认环节**：

   大纲确认已在 CNpatent-noveltycheck Phase C 完成。CNpatent 不再询问用户。

   在聊天窗口输出一句短确认：

   ```
   ✅ 接收 verified_outline 成功 (查新日期: YYYY-MM-DD, 最接近现有技术: #N).
   进入 Phase 1 多 Writer 并行生成.
   ```

6. **立即进入 Phase 1**（无需等待用户任何回复）

**设计原因**：前置 skill 已完成查新验证 + 领域迁移 + 大纲确认，CNpatent 专注于"大纲到 docx"的写作阶段。这样做的好处：

- 防止写出实际上已被他人申请的专利
- CNpatent 内部的多 Writer 并行 + Reviewer 审查架构**完全不变**
- 如需改动大纲，用户回到 CNpatent-noveltycheck 重跑，而不是在 CNpatent 里改

### Phase 1：任务拆分与并行生成（自动执行）

大纲确认后，自动进入多 Agent 并行生成流程。4 个 Writer 的**角色简报和写作规则**定义在 [`agents/cnpatent-writer-{a,b,c,d}.md`](agents/) 角色文件里；orchestrator 本阶段的任务是 **读取角色文件 → 拼接本次任务上下文 → 用 Agent 工具并行派发**。

**模型强制**：每次调用 Agent 工具时**必须显式传 `model="opus"`**（从角色文件 frontmatter 的 `model` 字段读取）。这是 `.claude/skills/CNpatent/agents/` 下未注册 agent 文件的**唯一运行时强制点**——frontmatter 本身不会被 Claude Code 的 subagent 发现机制读取。关于"能硬强制 vs 只能软影响"的完整约定，见 [`agents/README.md`](agents/README.md)。

**步骤 1 — 任务拆分**：根据确认的大纲，将全文拆分为以下 4 个独立任务：

| Writer Agent | 负责内容 | 字数上限 |
|-------------|---------|---------|
| **Writer-A** | 一、发明名称 + 二、技术领域 + 三、背景技术 | ~1200字 |
| **Writer-B** | 四、发明内容（发明目的 + 技术解决方案 + 技术效果 三个子节） | ~3500字 |
| **Writer-C** | 五、附图及附图的简单说明（不写声明段） + 六、具体实施方式·前半步骤（不写法律声明/概述/环境段） | ~3500字 |
| **Writer-D** | 六、具体实施方式·后半步骤（不写效果/总结/结尾段，步骤写完即止） | ~3500字 |

> 本交底书格式**不含摘要**（300字摘要），因此相比"说明书"格式减少了 Writer-E。

**步骤 2 — 准备每个 Writer 的任务上下文包**：

角色简报、写作规则、禁用词避坑清单、所述回指策略、对应三角守护等**常驻内容**已经写在 `agents/cnpatent-writer-{a,b,c,d}.md` 的 body 里——orchestrator 不要在这里重复。orchestrator 只负责注入**本次任务特有的上下文**：

1. **锁定的大纲片段** —— `01_outline.md` 中与该 Writer 任务相关的部分（含主旨四段式）
2. **参考素材原文片段** —— 与该 Writer 负责章节对应的参考材料段落
3. **术语锁定表** —— 从大纲里提取，每个 Writer 都收到完全相同的一份
4. **Writer-C/D 衔接信息** —— 两项元数据：
   - **步骤编号**：Writer-C 的最后一个步骤编号 K（供 Writer-D 从 K+1 起续写）
   - **公式编号区段**（v1.1 新增）：Writer-C 使用（1）-（10），Writer-D 从（11）起。如大纲预估 Writer-C 的公式需求超过 10 个，orchestrator 酌情扩到（15）并让 Writer-D 顺延。**Why**：2026-04-15 测试（Issue 3）发现两个 Writer 都从（4）开始编号，合并后出现重复。预分配区段是软约束，Phase 3 步骤 1a 的全局重编号脚本是硬兜底。
5. **工作目录绝对路径** —— `outputs/[专利名称]/sections/` 的完整路径，供 Writer 直接写文件
6. **`[待确认]` / `[源:...]` 标记约定** —— 一句话提醒；详细规则在角色文件 body 里

禁用词表、字数上限、对应章节格式规范、所述回指策略**都不再在此处重复注入**——它们是 Writer 的"角色记忆"，写在角色文件 body 里，避免 orchestrator 每次重拼 prompt 引入漂移。

**步骤 3 — 并行派发**：对每个 Writer 执行：

1. `Read` 角色文件 `agents/cnpatent-{writer-id}.md`
2. 从 frontmatter 解析出 `model`（统一为 `opus`）和 `outputs` 字段
3. 把 body 作为 system-prompt 级的角色描述，与步骤 2 的任务上下文拼接为完整 prompt
4. 调用 Agent 工具，参数为：`subagent_type="general-purpose"`、**`model="opus"` 显式传**、`prompt=<body + task_context>`、`run_in_background=True`

所有 4 个 Agent 调用在**单条消息内**发出（并行），等待全部完成。

**步骤 4 — 落盘到 sections/**：每个 Writer Agent 必须把输出（含 `[源:...]` 和 `[待确认:...]` 标记）直接写入 `outputs/[专利名称]/sections/` 下对应的章节文件。**没有 writer-named 中间文件**：Writer 视角的产物就是用户视角的章节文件。

| Writer | 写入文件 |
|--------|----------|
| **Writer-A** | `1_name.md`、`2_field.md`、`3_background.md` |
| **Writer-B** | `4a_purpose.md`、`4b_solution.md`、`4c_effect.md` |
| **Writer-C** | `5_figures.md`、`_part_six_first.md`（六节前半，临时） |
| **Writer-D** | `_part_six_second.md`（六节后半，临时） |

**Why**：用户基于专利结构（不是 Writer 并行结构）来定位编辑点。把"哪个 Writer 写了什么"这种并行细节藏在 orchestrator 内部，用户在 sections/ 看到的就是干净的 8 个章节文件。

**步骤 5 — 合并第六节并清理临时文件**：所有 4 个 Writer 完成后，orchestrator 读取 `_part_six_first.md` 和 `_part_six_second.md`，按顺序拼接（中间空一行）为 `sections/6_implementation.md`，然后删除两个 `_part_six_*.md`。Phase 1 结束时 sections/ 应严格包含 8 个文件，无 `_part_*` 残留。

**Writer-C 与 Writer-D 的衔接约定**：
- 大纲中六、的步骤按序号一分为二，前半给 Writer-C（写入 `_part_six_first.md`），后半给 Writer-D（写入 `_part_six_second.md`）
- Writer-C 不写法律声明段、实施例标题、概述段、环境说明段，直接从第一个步骤开始
- Writer-C 的最后一个步骤末尾不加总结性语句
- Writer-D 从下一个步骤编号继续，开头不加过渡性引言
- Writer-D 不写技术效果段、总结段、结尾段，最后一个步骤写完即止
- 拼接为 `6_implementation.md` 后，由 Reviewer 在 Phase 2 中负责检查衔接处的段落过渡是否自然
- **全文禁止使用"所述"**：用"上述"、"该"、"前述"等自然回指代替

### Phase 2：自动审查与修正（自动执行）

所有 Writer 完成后，自动启动 Reviewer Agent 执行**三重 rubric 审查**。Reviewer 的角色简报、完整 rubric（Rubric-A 一致性 / Rubric-B 反幻觉 / Rubric-C 去 AI 味）、输出格式、退回 Writer 的 `fix_spec` 规范全部定义在 [`agents/cnpatent-reviewer.md`](agents/cnpatent-reviewer.md) 中——不在 SKILL.md 重复 rubric 细节。

**派发协议**（与 Phase 1 相同）：orchestrator `Read` `agents/cnpatent-reviewer.md` → 拼接任务上下文（全部 8 个 section 文件路径 + `01_outline.md` + 参考素材 + 术语锁定表 + 当前轮次 1/2）→ 调用 Agent 工具，**`model="opus"` 显式传**。

**设计约束**（research-backed，详见 `agents/README.md` 的"设计原则"章节）：

- **Rubric-based 非 open critique**：Reviewer 逐项 pass/fail 检查 closed rubric，不做"这段写得怎么样"式开放式评论。研究表明 open critique 会触发 sycophancy（Reviewer 附和 Writer）
- **不输出替代草稿**：涉及语义 / 结构的问题必须退回对应 Writer。只有禁用词残留 / 标点 / 编号格式等**机械性问题**才由 Reviewer 直接 `Edit` 就地修补。研究表明允许 Reviewer 改写会触发 "over-correction stripping voice" 失败模式
- **硬 cap 2 轮**：Reviewer → Writer → Reviewer 最多往返 2 轮。infinite revision loop 是多 agent 写作管线的 top failure mode（MAST 框架）

**Reviewer 输出 & 回传协议**：

- Reviewer 产出结构化 chat 总结（Rubric-A/B/C 逐项 pass/fail + 退回清单 + `[待确认]` 汇总），**不**输出替代草稿
- **机械性修补**（禁用词残留 / 半角标点 / 编号格式 / Writer-C/D 衔接处段落过渡）由 Reviewer 直接 `Edit` `sections/*.md`，结果就地生效
- **语义 / 结构问题**由 Reviewer 写成带有 `section` + `quote` + `issue_type` + `fix_spec` 四元组的退回清单；orchestrator 通过 SendMessage 把 `fix_spec` 路由到对应 Writer；Writer 修改后 orchestrator 触发第 2 轮 Reviewer
- `CNpatent-humanizer` 返回 0–100 分的去 AI 味评分，Reviewer 据此决策：
  - 分数 ≥ 50：退回对应 Writer 整段重写
  - 分数 25–49：Reviewer 就地修补
  - 分数 < 25：通过
- **第 2 轮结束仍有未解决的结构性问题**，保留在 chat 总结里提示 orchestrator 让用户人工介入，**不**进入第 3 轮
- 审查通过后，移除所有 `[源:...]` 内部标注，保留 `[待确认:...]` 标记

**落盘策略**：Reviewer 的所有修改直接写回 `sections/*.md`（in-place 编辑）。**不保留任何审查中间文件**：审查报告、问题清单、Writer 退回轮次、人类化润色前/后对比都仅以 Reviewer 在聊天窗口的简要总结呈现，不落盘。调用 `CNpatent-humanizer` skill 时也是对 sections 文件就地处理。

**Why**：按照"工作目录只保留 DOCX 写入前的最终态"的设计原则，审查/润色过程产物属于"过程态"，不应留在工作目录里污染编辑视图。如需精确的变更追溯，建议用户在 `outputs/[专利名称]/` 下做 `git init` 自行管理（详见后文【工作目录与断点重启机制】）。

### Phase 3：兜底清理与 DOCX 写入（自动执行）

sections/ 中已经是按章节组织的最终文本，本阶段只做"清理 + 写入 DOCX"两件事，没有合并步骤。

**步骤 1 — 兜底清理（in-place）**：对 sections/ 下的 8 个 .md 文件依次调用 `scripts/deai_cleanup.py` 的 `final_deai_cleanup()`（纯正则替换，不依赖 AI 判断），结果写回原文件。

**Why in-place**：保证 `sections/*.md` 永远反映 DOCX 中的实际内容；用户基于 sections/ 编辑后再次跑 Phase 3 时，cleanup 是幂等的，重复调用无副作用。这样用户无论何时打开 sections 文件，看到的都是与 DOCX 一致的"最终状态"。

**步骤 1a — 公式编号全局校验与重编号（v1.1 新增，in-place）**：对 `sections/6_implementation.md` 调用 `scripts/formula_renumber.py` 的 `renumber_formulas_in_file()`，按公式定义在文本中的出现顺序重编号为连续的（1）（2）（3）...，同时更新所有 `式（N）` / `公式（N）` 引用。

```python
from formula_renumber import renumber_formulas_in_file
report = renumber_formulas_in_file(impl_path)
if report.changed:
    print(f"公式重编号: {report}")
```

脚本使用两阶段占位符替换避免链式冲突（与 Phase 6 图号重编号同理）。如公式序列已经连续且从 1 开始，脚本不写文件（幂等）。

**Why 这一步是必要的**：Phase 1 步骤 2 给 Writer-C/D 预分配了公式编号区段，但那是 LLM 软约束，Writer 可以不遵守。2026-04-15 测试（Issue 3）实证了这一失败模式。本步骤是确定性硬兜底，不依赖 AI 判断。

**步骤 2 — 按序写入 DOCX**：使用 `scripts/cnpatent_docx.py` 的辅助函数（按铁律 1 的代码块导入），按以下映射读取 sections/ 文件并写入对应的模板锚点：

| 顺序 | 文件 | 模板锚点（anchor key）| 写入方式 |
|------|------|-----------------------|----------|
| 1 | `sections/1_name.md` | `一` | `insert_before` |
| 2 | `sections/2_field.md` | `二` | `insert_before` |
| 3 | `sections/3_background.md` | `三` | `insert_before` |
| 4 | `sections/4a_purpose.md` | `发明目的` | `insert_before` |
| 5 | `sections/4b_solution.md` | `技术解决方案` | `insert_before` |
| 6 | `sections/4c_effect.md` | `技术效果` | `insert_before` |
| 7 | `sections/5_figures.md` | `五` | `insert_before` |
| 8 | `sections/6_implementation.md` | `六`（无后续锚点）| `append_at_end` |

写入流程：
1. `load_template()` → `clear_placeholders(doc)` → `get_section_anchors(doc)`
2. 按上表顺序读 sections 文件 → 切分为段落 → 按段落类型选择样式插入
3. 段落样式按内容分配：正文 `Normal`，图题 `Caption`，公式 `公式`（用 `add_formula(doc, r'...')`）
4. 保存为 `outputs/[专利名称]/[专利名称]_专利技术交底书.docx`

详见 [docx-patterns.md](references/docx-patterns.md) 的 Section-Aware Writing 完整示例。

**若存在 `[待确认]` 标记**：扫描 sections/*.md 找出所有 `[待确认:...]` 标记，在聊天窗口输出汇总提示，列出所有待用户确认的参数/内容，格式为：
```
⚠️ 以下内容需要您确认或补充：
1. [待确认:XXX的具体参数值] — 位于"六、具体实施方式·步骤（3）"
2. [待确认:YYY的取值范围] — 位于"六、具体实施方式·步骤（5）"
请提供相关信息，我将更新文档。
```

### Phase 4：DOCX 写入后验证（自动执行）

每次生成或修改 .docx 后，调用 `scripts/cnpatent_docx.py` 的 `verify_docx(output_path)` 执行完整验证。该函数检查 6 项必备断言：

1. 9 个模板标题段（6 H1 + 3 H2）完整保留
2. 全文无 `权利要求书` 字样
3. 附图编号 `图1..图N` 在「五、附图说明」中连续无跳号
4. 正文图引用编号不超出附图说明的最大编号
5. 公式段**仅**出现在「六、具体实施方式」中，且段落样式必须为 `公式`
6. 所有编号统一用**全角**`（N）`，无半角 `(N)` 残留

任一断言失败时函数抛出 `AssertionError`，定位到出错段落。完整实现见 [docx-patterns.md](references/docx-patterns.md) 的 "Post-Modification Verification" 章节。

### Phase 5：静默生成附图提示词（自动触发，输出 .md）

主文档保存后自动执行，**禁止在聊天窗口输出提示词内容**。生成 Markdown 文件 `[专利名称]_全套AI生图提示词.md`（不再生成 .docx），按图编号逐张写入：

- **主体段**：场景描述 + 中文标签的空间锚定（"位置编码 labeled in the top-left rectangular block"）
- **警告段**：全大写 STRICT WARNING 段（铁律 4 ④），用 `> **STRICT WARNING:**` blockquote + bold 格式

每张图的提示词用 `## 图N` 二级标题分隔。文件头部加一行说明："以下提示词用于 AI 生图工具（Midjourney / DALL-E / Stable Diffusion 等），每张图单独一段。"

**Why 改用 .md**：提示词只是给 AI 生图工具的纯文本输入，不需要 docx 的排版能力。Markdown 更轻量，不依赖 python-docx，用户可直接在编辑器里复制粘贴。

聊天窗口仅输出一句确认：
> ✅ 全套附图的防幻觉 AI 生图提示词已保存至 outputs/[专利名称]/[专利名称]_全套AI生图提示词.md。

### Phase 6：附图修正（按需触发）

当用户要求删除冗余附图、重编号或修正附图引用时，执行此阶段。

**执行步骤**：

1. **标记孤儿段落**：扫描全文，按内容和样式标记需要删除的段落（附图说明描述行、图题段落、关联空行）
2. **全局图号替换**：使用两阶段占位符策略，避免链式替换冲突（详见 [docx-patterns.md](references/docx-patterns.md)）
3. **删除孤儿段落**：按索引逆序删除标记的段落
4. **验证**：重新加载保存的文件，检查附图说明连续性、正文引用一致性、图题完整性
5. **更新提示词文档**：如果图号变化，同步更新 `[专利名称]_全套AI生图提示词.md`

**关键技术要点**：
- python-docx 中文本常被拆分到多个 Run，**必须使用段落级替换**（`para_replace`），不能在单个 Run 中搜索。详见 [docx-patterns.md](references/docx-patterns.md) 的 "Run Splitting Problem" 章节。
- 图号替换必须处理所有变体："如图X所示"、"如图X和图Y所示"、"图X至图Y"、附图说明行、图题段落。
- 多图引用（如"如图3和图4所示"）在其中一张图被删除后需简化（→"如图3所示"）。

**输出文件**：`outputs/[专利名称]/[前缀]_[专利名称]_专利技术交底书.docx`

---

## 工作目录与断点重启机制

工作目录 `outputs/[专利名称]/` **只保留两类文件**：
1. `01_outline.md` —— Phase 0 用户确认的大纲（断点重启时从此读起）
2. `sections/*.md` —— 8 个章节文件，DOCX 写入前的最终文本（用户可直接编辑）

**设计原则**：审查报告、Writer 原始草稿、人类化润色前/后对比等"过程产物"一律不落盘。修改场景下用户只需要最终态；过程态由 Reviewer 在聊天窗口的总结承载，如需精确变更追溯由用户用 git 自行管理。

### 工作目录结构

```
outputs/[专利名称]/
├── 01_outline.md                       # Phase 0 确认的大纲
├── sections/                           # 8 个章节文件，可由用户直接编辑
│   ├── 1_name.md                       # 一、发明名称
│   ├── 2_field.md                      # 二、技术领域
│   ├── 3_background.md                 # 三、背景技术
│   ├── 4a_purpose.md                   # 四·发明目的
│   ├── 4b_solution.md                  # 四·技术解决方案
│   ├── 4c_effect.md                    # 四·技术效果
│   ├── 5_figures.md                    # 五、附图说明
│   └── 6_implementation.md             # 六、具体实施方式
├── [专利名称]_专利技术交底书.docx       # Phase 3 最终 DOCX
└── [专利名称]_全套AI生图提示词.md       # Phase 5 静默生成的附图提示词（Markdown）
```

**Why 第四节拆三个文件**：四·发明目的、四·技术解决方案、四·技术效果三者构成"对应三角"（背景技术局限 ↔ 优势 ↔ 效果），用户最常对照修改这三段内容。拆分后可以并排打开三者 + `3_background.md`，校对对应关系一目了然。其他章节没有这种对应需求，所以不拆。

**Why 第六节合一**：六节虽然由 Writer-C 和 Writer-D 并行写就，但用户视角的"六节"是一个整体——把并行细节藏在 orchestrator 内部（详见 Phase 1 的 `_part_six_*.md` 临时机制），用户在 sections/ 看到的就是 `6_implementation.md` 一个文件。

### 断点重启与局部修改

只有两种修改场景：

| 用户意见涉及 | 修改的文件 | 需要重跑的阶段 |
|---|---|---|
| 大纲结构、技术路线、术语命名 | `01_outline.md` | Phase 1 → Phase 2 → Phase 3（覆盖整个 sections/） |
| 任意章节的内容/段落/术语 | 直接编辑对应 `sections/*.md` | 仅 Phase 3（清理 + DOCX 写入 + Phase 4 验证）|
| 附图增删/重编号 | 现有 DOCX | Phase 6（不动 sections/） |

**用户提意见的方式**：直接告诉 Skill"我编辑了 4b_solution.md，请重新生成 DOCX"——Skill 收到后只跑 Phase 3 即可，无需重跑 Writer/Reviewer。

**版本管理建议**：sections/ 是一个普通目录，建议用户在 `outputs/[专利名称]/` 下做 `git init`，每次修改前 commit 一次。这样：
- 想看 Reviewer 改了什么 → `git diff sections/`
- 想回滚 → `git checkout sections/`
- 想看历史版本 → `git log`

无需 Skill 内置版本号机制（不再有 `_v2` 后缀）。

---

## 文档结构与交付前检查清单

电学类交底书的完整文档结构（6 H1 + 3 H2 标题）和 19 项交付前质量检查清单见 [references/quality-checklist.md](references/quality-checklist.md)。Reviewer agent 和 Phase 4 验证均引用该文件。

## 参考规范

- [去 AI 痕迹与专利语言规范](references/writing-rules.md)
- [python-docx 代码模板](references/docx-patterns.md)（含模板章节定位、占位段删除、Run 分裂修复、链式替换、段落删除等模式）

## 插图写入

当用户提供图片文件时，使用 [docx-patterns.md](references/docx-patterns.md) 的 `insert_image_after()` 辅助函数，将图片插入到「五、附图说明」对应图题之后或「六、具体实施方式」对应步骤之后。

## 平台注意事项

Windows 上运行 Python 写入中文时需启用 UTF-8 模式（`PYTHONUTF8=1 python -X utf8 script.py`），详见 [docx-patterns.md](references/docx-patterns.md) 的 Common Issues 表。
