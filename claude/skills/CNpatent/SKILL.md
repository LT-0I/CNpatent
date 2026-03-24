---
name: CNpatent
description: >
  Chinese invention patent technical disclosure generator (专利技术交底书).
  Transforms reference materials (academic papers, R&D notes, open-source projects)
  into CNIPA-compliant technical disclosure documents (.docx), including Specification
  (说明书) and Abstract (说明书摘要). Use when user asks to: (1) write a Chinese patent
  disclosure (技术交底书), (2) draft a Chinese patent specification (专利说明书),
  (3) convert a paper or technical document into a patent disclosure, (4) rewrite or
  restructure an existing patent draft to CNIPA format, (5) generate patent
  figures/prompts, or (6) any task involving Chinese invention patent document creation
  or editing.
---

# CNpatent — 中国发明专利技术交底书生成器

> 将学术论文、研发笔记等素材转化为符合 CNIPA 规范的专利技术交底书（.docx）。
> 权利要求书由专利代理人根据本交底书另行撰写，交底书中**不包含**。

## Quick Start

1. 确认用户提供的**参考素材**和**目标应用领域**（若未提供领域则主动询问）
2. 基于目标领域执行场景迁移与微创新设计，规避现有专利
3. 生成结构化大纲（含各章节要点、预计附图清单、术语锁定表），与用户确认——**这是唯一的用户确认点**
4. 大纲确认后，自动并行派发多个 Writer Agent 生成全部章节 → Reviewer Agent 自动审查修正 → 整合写入 .docx（全程无需用户干预）
5. 自动静默触发 Phase 5，生成防幻觉 AI 附图提示词
6. 如需修正附图（删除冗余图、重编号），执行 Phase 6

---

## 必需输入 (Required Inputs)

在开始生成前，**必须**确认以下信息。若用户未主动提供，需主动询问：

| 输入项 | 必需 | 说明 | 示例 |
|--------|:----:|------|------|
| **参考素材** | 是 | 学术论文、技术文档、开源项目等 | PDF / 文本 / 链接 |
| **目标应用领域** | 是 | 专利要落地的具体工程场景，用于场景迁移与微创新 | 肛瘘术后创口三维重建 / 工业焊缝检测 / 自动驾驶障碍物识别 |
| 现有专利参考 | 可选 | 同领域已有专利，用于差异化设计、规避查重 | 专利号 / 标题 / 摘要 |

**目标应用领域**的三重作用：
1. **场景迁移**：将学术算法从实验室环境迁移至目标工程场景，重新推导技术痛点
2. **微创新设计**：基于目标领域的特定约束（数据特性、硬件限制、行业标准），设计区别于原始论文和现有技术的创新点
3. **规避专利查重**：通过领域特化的技术方案描述，与同领域已有专利形成差异化

---

## 铁律 (Core Execution Constraints)

### 铁律 1：模板驱动，严禁从零创建

生成 .docx 专利文档时，**绝对禁止创建空白文档**。必须加载本 Skill 内置的模板：

```python
import os
from docx import Document

template_path = os.path.join(
    os.path.expanduser('~'),
    '.claude', 'skills', 'CNpatent', 'assets', '专利交底书模板.docx'
)
doc = Document(template_path)
```

执行要求：
- 先检查模板中可用的段落样式，再做样式映射（个人标题 / Heading 1 / Normal / 首行缩进 / 公式 / 图题 等）
- **严禁修改**模板自带的页眉、页脚、页码、页面边距、字体设置
- **严禁删除携带 `sectPr` 的分节边界段落**（段落[0]、[1]、[12]），否则会破坏文档的页面结构和页眉
- 模板分 4 个 Section：说明书摘要(第1页) → 摘要附图(第2页，空白) → 说明书 → 说明书附图。内容必须写入对应 Section，详见 [docx-patterns.md](references/docx-patterns.md) 的分节感知写入章节
- 始终另存为新文件 `[专利名称]_专利技术交底书.docx`，**不得覆盖模板**

如果用户在工作目录下有自己的模板文件，优先使用用户提供的模板（注意：用户模板的分节结构可能不同，需重新扫描 `find_section_boundaries()`）。

### 铁律 2：纯文本 LaTeX 公式

所有数学公式以纯文本 LaTeX 字符串写入文档：
- 行内公式：`$E = mc^2$`
- 独立公式：`$$\sum_{i=1}^{N} x_i$$`
- 公式**仅出现**在「具体实施方式」中，**严禁出现**在「发明内容」中

### 铁律 3：去 AI 痕迹（三层过滤）

生成专利文本时，必须经过**三层过滤**确保无 AI 写作痕迹：

**第一层 — 写作时预防**：每个 Writer Agent 的 prompt 中注入 [writing-rules.md](references/writing-rules.md) 的完整禁用词表，要求写作时即主动避免使用禁用词和 AI 高频句式。

**第二层 — 自动扫描替换**：Writer 完成输出后，对文本执行正则扫描，自动替换命中的禁用词（见 [writing-rules.md](references/writing-rules.md) 的禁用词表及"最终 DOCX 写入前自动替换"章节）。

**第三层 — Reviewer 终审**：Reviewer Agent 执行以下深度检查：
- a）禁用词残留扫描（逐词比对禁用词表）
- b）句式结构检测：平行结构、段落均匀度、三段式凑数、连续关联词（见 [writing-rules.md](references/writing-rules.md) 的"句式结构检测规则"章节）
- c）同义词轮换检测：同一技术概念是否全文术语统一
- d）调用 `humanizer` skill 做最终人类化润色

不合格内容退回对应 Writer 修正，最多 2 轮。最终文本必须符合专利文书的严谨、客观、技术性风格，读起来像领域工程师而非 AI 所写。

### 铁律 4：防幻觉附图提示词

主文档生成完毕后，自动静默触发 Phase 3。提示词必须遵守四条铁律：

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

**⑤ 静默写入**：提示词不输出到聊天窗口，直接写入 `[专利名称]_全套AI生图提示词.docx`。
警告段落设置为**粗体红色**（#CC0000）。

### 铁律 5：信息源锚定（防幻觉）

生成专利文本时，所有技术内容必须可追溯到参考素材或用户确认的大纲：

1. **数值参数**：必须来自参考素材或用户在大纲中确认。Writer 内部标注 `[源:论文X节]` 或 `[源:大纲约定]`，该标注仅用于 Reviewer 审查，写入 DOCX 前自动移除
2. **公式**：须与参考素材原文比对，不得自行推导参考素材中不存在的新公式。领域化"蒙皮"释义除外（变量重新释义不算新公式）
3. **技术步骤**：须严格对应大纲中的步骤规划，不得自行增减步骤
4. **无法确认的内容**：禁止编造，必须标记为 `[待确认:具体问题]`。Reviewer 汇总所有 `[待确认]` 标记，在最终输出中以醒目格式提示用户补充
5. **Writer 的 token 上限**：每个 Writer Agent 单次输出不超过 3000 字，避免因输出过长导致后半段内容质量下降

---

## 执行流程 (Execution Protocol)

### Phase 0：输入确认 + 场景迁移 + 大纲生成

1. 读取用户提供的参考素材
2. 若用户未指定**目标应用领域**，**必须主动询问**，不可跳过
3. 基于目标领域执行场景迁移：
   - 禁止照搬学术背景（数据集名称、实验室环境、benchmark 指标）
   - 将核心算法迁移至用户指定的实际工程场景
   - 从新场景的工程约束（数据采集条件、硬件限制、行业标准）重新推导技术痛点
4. 设计微创新点：
   - 分析参考素材中的核心技术贡献
   - 结合目标领域的特殊需求，提出至少 1-2 个差异化改进
   - 确保技术方案与现有技术（若已知）形成明确区分
5. **生成结构化大纲**（本流程的核心产出）：

   大纲必须包含以下内容，以结构化格式展示给用户：

   ```
   一、发明名称：[名称]
   二、技术领域：[1-2句概述]
   三、背景技术要点：
       - 段1要点：[工程需求]
       - 段2要点：[现有方案局限]
       - 段3要点：[当前场景的技术问题]
   四、发明内容·主步骤：
       - S1：[步骤名] ← [源:论文X节 / 领域迁移设计]
       - S2：[步骤名] ← [源:...]
       - ...
   五、发明内容·创新点标注：
       - 创新点A：[描述] → 对应步骤SX
       - 创新点B：[描述] → 对应步骤SY
   六、具体实施方式·步骤拆分：
       - 步骤1：[标题]，简/繁=[简|繁]，预计子步骤数=[N]
       - 步骤2：[标题]，简/繁=[简|繁]，预计子步骤数=[N]
       - ...
   七、预计附图清单：
       - 图1：[描述]
       - 图2：[描述]
       - ...
   八、术语锁定表：
       - [学术术语A] → [专利术语A]（全文统一使用）
       - [学术术语B] → [专利术语B]（全文统一使用）
       - ...
   ```

6. 向用户展示大纲，等待用户确认。**这是整个流程中唯一的用户确认点**，大纲确认后全部自动完成，不再询问用户。

### Phase 1：任务拆分与并行生成（自动执行）

大纲确认后，自动进入多 Agent 并行生成流程。**所有 Agent 必须使用 opus 模型。**

**步骤 1 — 任务拆分**：根据确认的大纲，将全文拆分为以下 5 个独立任务：

| Writer Agent | 负责内容 | 字数上限 |
|-------------|---------|---------|
| **Writer-A** | 技术领域 + 背景技术 | ~800字 |
| **Writer-B** | 发明内容（目的句→引入句→主步骤→可选的从属特征→技术效果） | ~2000字 |
| **Writer-C** | 具体实施方式·前半部分（5段法律声明 + 实施例概述 + 前 N/2 个步骤） | ~3000字 |
| **Writer-D** | 具体实施方式·后半部分（后 N/2 个步骤 + 技术效果段 + 总结段 + 结尾段） | ~3000字 |
| **Writer-E** | 附图说明（2段法律声明 + 逐图描述）+ 说明书摘要（≤300字） | ~500字 |

**步骤 2 — 准备每个 Writer 的上下文包**：

每个 Writer Agent 的 prompt 中必须注入以下内容：
1. **锁定的大纲**（仅与该 Writer 任务相关的部分）
2. **参考素材原文片段**（与该 Writer 负责章节对应的参考材料段落）
3. **术语锁定表**（从大纲第八项提取，确保所有 Writer 使用完全相同的术语）
4. **writing-rules.md 的完整禁用词表**（第一层去 AI 预防）
5. **信息源锚定要求**（铁律 5）：
   - 数值参数必须标注来源 `[源:论文X节]` 或 `[源:大纲约定]`
   - 无法标注来源的参数禁止编造，必须标记 `[待确认:具体问题]`
   - 信息源标注仅用于审查，写入 DOCX 前自动移除
6. **本 Writer 的字数上限**（严格遵守）
7. **对应章节的格式规范**（从 SKILL.md 和 writing-rules.md 中提取相关段落）

**步骤 3 — 并行派发**：使用 Agent 工具并行启动 5 个 Writer Agent（单条消息中发出多个 Agent 调用），等待全部完成。

**Writer-C 与 Writer-D 的衔接约定**：
- 大纲中的步骤按序号一分为二，前半给 Writer-C，后半给 Writer-D
- Writer-C 的最后一个步骤末尾不加总结性语句
- Writer-D 从下一个步骤编号继续，开头不加过渡性引言
- 两者的衔接由 Reviewer 在 Phase 2 中负责检查和修正

### Phase 2：自动审查与修正（自动执行）

所有 Writer 完成后，自动启动 Reviewer Agent（使用 opus 模型）执行三重审查。

**审查 1 — 一致性检查**：
- 术语是否全文统一（对照术语锁定表，检查是否存在同义词轮换）
- 图号是否连续（图1~图N 无跳号）、正文图引用是否一致
- "所述"回指是否正确（每个技术要素第二次出现时是否加了"所述"）
- 步骤编号是否连续、格式是否统一（编号式或步骤式二选一）
- Writer-C 和 Writer-D 的衔接是否自然（步骤编号连续、无重复、无遗漏）
- 发明内容的主步骤是否与具体实施方式的步骤一一对应
- 摘要是否与发明内容主步骤一一对应、字数是否 ≤300

**审查 2 — 反幻觉检查**：
- 检查所有 `[源:...]` 标注是否合理（源头是否确实存在于参考素材中）
- 汇总所有 `[待确认:...]` 标记，准备在最终输出中提示用户
- 公式是否与参考素材一致（变量名可做领域化蒙皮，但公式结构不得改变）
- 参数值是否有出处（参考素材或大纲约定）
- 是否存在参考素材中完全没有的技术描述（排除大纲中约定的微创新部分）

**审查 3 — 去 AI 味检查**（铁律 3 第三层）：
- 对照 [writing-rules.md](references/writing-rules.md) 禁用词表做残留扫描
- 执行句式结构检测（平行结构、段落均匀度、三段式凑数、连续关联词）
- 执行同义词轮换检测
- 调用 `humanizer` skill 做最终人类化润色

**审查结果处理**：
- 发现问题后，将具体问题描述和修改要求通过 SendMessage 退回对应 Writer Agent 修正
- 最多 2 轮修正循环。若 2 轮后仍有 `[待确认]` 参数，保留标记
- Reviewer 负责 Writer-C/D 衔接处的段落过渡修正（可直接修改，无需退回）
- 审查通过后，移除所有 `[源:...]` 内部标注，保留 `[待确认:...]` 标记

### Phase 3：整合与 DOCX 写入（自动执行）

审查通过后，将 5 个 Writer 的输出按以下顺序整合，并写入 DOCX：

**整合顺序**：
1. Writer-A 的输出 → 技术领域 + 背景技术
2. Writer-B 的输出 → 发明内容
3. Writer-E 的附图说明部分 → 附图说明
4. Writer-C 的输出 → 具体实施方式·前半
5. Writer-D 的输出 → 具体实施方式·后半
6. Writer-E 的摘要部分 → 说明书摘要

**DOCX 写入**：使用分节感知写入，严格遵守模板的 4-Section 结构。详见 [docx-patterns.md](references/docx-patterns.md) 的完整代码模板。

核心要点：
1. 加载模板后，先用 `find_section_boundaries()` 定位 3 个携带 `sectPr` 的边界段落 [0]、[1]、[12]
2. 清除模板占位内容时，**绝不删除边界段落**，只删除非边界段落
3. **Section 0（说明书摘要）**：在 `sect0_para` 之前插入摘要文本（≤300字）
4. **Section 1（摘要附图）**：保持空白，不写入任何内容
5. **Section 2（说明书）**：在 `sect2_para` 之前依次插入：发明名称、技术领域、背景技术、发明内容、附图说明、具体实施方式
6. **Section 3（说明书附图）**：在文档末尾追加图题段落（图1、图2...）
7. 使用 `anchor._element.addprevious(p._element)` 在锚点前插入，而非 `doc.add_paragraph()` 追加到末尾

**写入前执行最终兜底替换**（见 [writing-rules.md](references/writing-rules.md) 的"最终 DOCX 写入前自动替换"章节）：对全文执行纯正则匹配替换，确保无禁用词残留。

**若存在 `[待确认]` 标记**：在聊天窗口输出汇总提示，列出所有待用户确认的参数/内容，格式为：
```
⚠️ 以下内容需要您确认或补充：
1. [待确认:XXX的具体参数值] — 位于"具体实施方式·步骤S3"
2. [待确认:YYY的取值范围] — 位于"具体实施方式·步骤S5"
请提供相关信息，我将更新文档。
```

### Phase 4：DOCX 写入后验证（自动执行）

每次生成或修改 .docx 后，必须验证文档完整性：

```python
import re
doc_check = Document(output_path)

# 1. 检查附图说明连续性（图1~图N 无跳号）
fig_nums_in_desc = []
for p in doc_check.paragraphs:
    m = re.match(r'图(\d+)为本发明', p.text)
    if m:
        fig_nums_in_desc.append(int(m.group(1)))
assert fig_nums_in_desc == list(range(1, len(fig_nums_in_desc) + 1)), "附图编号不连续！"

# 2. 检查正文引用不超出附图范围
max_fig = max(fig_nums_in_desc) if fig_nums_in_desc else 0
for p in doc_check.paragraphs:
    for m in re.finditer(r'图(\d+)', p.text):
        ref_num = int(m.group(1))
        assert ref_num <= max_fig, f"引用了不存在的图{ref_num}！"

# 3. 检查图题段落连续性
fig_nums_in_captions = []
for p in doc_check.paragraphs:
    if p.style.name == '图题' and p.text.strip():
        m = re.match(r'图(\d+)', p.text.strip())
        if m:
            fig_nums_in_captions.append(int(m.group(1)))
```

### Phase 5：静默生成附图提示词（自动触发）

主文档保存后自动执行，**禁止在聊天窗口输出提示词内容**。

```python
from docx import Document
from docx.shared import Pt, RGBColor

prompt_doc = Document()

for fig_num, data in figure_prompts.items():
    prompt_doc.add_heading(f'Figure {fig_num}: {data["title"]}', level=1)
    para = prompt_doc.add_paragraph()

    run_main = para.add_run(data['body'])
    run_main.font.size = Pt(10.5)

    run_warn = para.add_run(data['warning'])
    run_warn.bold = True
    run_warn.font.size = Pt(10.5)
    run_warn.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)

prompt_doc.save('[专利名称]_全套AI生图提示词.docx')
```

聊天窗口仅输出一句确认：
```
✅ 全套附图的防幻觉 AI 生图提示词已保存至 [专利名称]_全套AI生图提示词.docx。
```

### Phase 6：附图修正（按需触发）

当用户要求删除冗余附图、重编号或修正附图引用时，执行此阶段。

**执行步骤**：

1. **标记孤儿段落**：扫描全文，按内容和样式标记需要删除的段落（附图说明描述行、图题段落、关联空行）
2. **全局图号替换**：使用两阶段占位符策略，避免链式替换冲突（详见 [docx-patterns.md](references/docx-patterns.md)）
3. **删除孤儿段落**：按索引逆序删除标记的段落
4. **验证**：重新加载保存的文件，检查附图说明连续性、正文引用一致性、图题完整性
5. **更新提示词文档**：如果图号变化，同步更新 AI 生图提示词文档

**关键技术要点**：
- python-docx 中文本常被拆分到多个 Run，**必须使用段落级替换**（`para_replace`），不能在单个 Run 中搜索。详见 [docx-patterns.md](references/docx-patterns.md) 的 "Run Splitting Problem" 章节。
- 图号替换必须处理所有变体："如图X所示"、"如图X和图Y所示"、"图X至图Y"、附图说明行、图题段落。
- 多图引用（如"如图3和图4所示"）在其中一张图被删除后需简化（→"如图3所示"）。

**输出文件**：`[前缀]_[专利名称]_专利技术交底书.docx`

---

## 专利技术交底书文档结构

```
【说明书】
  发明名称
  技术领域（仅1句）
  背景技术（1-4段）
  发明内容：
    ① 目的句
    ② 引入句
    ③ 主步骤分段（创新步骤前加动机句）
    ④ "可选的"从属特征展开
    ⑤ 技术效果
  附图说明（2段法律声明 + 逐图描述）
  具体实施方式：
    ① 法律声明（5段固定文本）
    ② 实施例概述段（"实施例一" + 流程概述 + 可选环境说明）
    ③ 详细步骤（编号式或步骤式，含子步骤、公式、参数）
    ④ 实施例技术效果段（逐条展开）
    ⑤ 实施例总结段（1段综述）
    ⑥ 结尾段（固定文本）

【说明书摘要】（≤300 字，与发明内容主步骤一一对应）
```

注：权利要求书由专利代理人根据本交底书另行撰写，**交底书中严禁包含权利要求书**。如用户要求生成权利要求书，应明确告知其不属于技术交底书范畴，建议交由专利代理人处理。

## 交付前质量检查清单

生成文本后、写入 DOCX 前，逐项核查：

| # | 检查项 | 要求 |
|---|--------|------|
| 1 | **技术领域** | 仅1句，"本发明属于...技术领域，{具体涉及/特别是涉及/尤其涉及}一种..." |
| 2 | **背景技术** | 1-4段，无学术引文（可引专利号），末尾以技术问题句收束 |
| 3 | **发明内容结构** | 目的句→引入句→主步骤→可选的展开→技术效果，缺一不可 |
| 4 | **发明内容无公式** | 扫描确认无 $ 或 LaTeX 标记 |
| 5 | **"所述"回指** | 每个技术要素第二次出现时必须加"所述" |
| 6 | **术语一致性** | 同一技术要素全文只用一种叫法，无同义替换 |
| 7 | **附图说明声明** | 2段法律声明在逐图描述之前 |
| 8 | **附图说明格式** | "图X为本发明实施例中{的/提供的}[描述]{示意图/流程图}。" |
| 9 | **具体实施方式声明** | 5段法律声明在实施例正文之前 |
| 10 | **实施例概述段** | "实施例一" + 流程概述 + 可选环境说明 |
| 11 | **步骤引用附图** | 每步至少引用一张图（"如图X所示"） |
| 12 | **公式仅在具体实施方式** | 发明内容中无公式 |
| 13 | **公式连续编号** | （1）（2）...无跳号 |
| 14 | **实施例技术效果段** | 详细步骤之后，"本实施例的技术效果为：" + 逐条效果 |
| 15 | **实施例总结段** | "综上所述，本实施例通过..." |
| 16 | **结尾段** | 固定文本"以上所述，仅为本申请较佳的..."逐字存在 |
| 17 | **摘要 ≤300字** | 与发明内容主步骤一一对应 |
| 18 | **禁用词扫描** | 对照 writing-rules.md 禁用词表（含第六类），无残留 AI 痕迹（铁律 3 三层过滤） |
| 19 | **无权利要求书** | 交底书中不包含权利要求书 |

## 参考规范

- [去 AI 痕迹与专利语言规范](references/writing-rules.md)
- [python-docx 代码模板](references/docx-patterns.md)（含 Run 分裂修复、链式替换、段落删除等模式）

## 插图写入

当用户提供图片文件时：

```python
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc.add_picture('图1.png', width=Inches(5.0))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
```

## 平台注意事项

### Windows 环境

Windows 默认使用 ANSI 编码，Python 输出中文会乱码。执行脚本时必须加编码前缀：

```bash
PYTHONUTF8=1 python -X utf8 script.py
```

或在脚本开头添加：

```python
import sys
sys.stdout.reconfigure(encoding='utf-8')
```
