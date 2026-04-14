---
name: CNpatent
description: >
  Chinese invention patent technical disclosure generator (专利技术交底书).
  Transforms reference materials (academic papers, R&D notes, open-source projects)
  into CNIPA-compliant technical disclosure documents (.docx) in the electrical
  (电学类) disclosure format, with numbered sections 一～六 (发明名称、技术领域、
  背景技术、发明内容、附图说明、具体实施方式). The disclosure does NOT include
  section 七 (权利要求书) — claims are drafted separately by the patent agent.
  Use when user asks to: (1) write a Chinese patent disclosure (技术交底书),
  (2) draft a Chinese electrical patent disclosure (电学类专利交底书),
  (3) convert a paper or technical document into a patent disclosure,
  (4) rewrite or restructure an existing patent draft to the 电学类交底书 format,
  (5) generate patent figures/prompts, or (6) any task involving Chinese invention
  patent disclosure document creation or editing.
---

# CNpatent — 中国发明专利技术交底书生成器（电学类格式）

> 将学术论文、研发笔记、开源项目等素材转化为符合代理机构电学类格式的专利技术交底书（.docx）。
> 输出文档包含 一～六 节（发明名称 / 技术领域 / 背景技术 / 发明内容 / 附图说明 / 具体实施方式），**不包含** 七、权利要求书，权利要求书由专利代理人根据交底书另行撰写。

## Quick Start

1. 确认用户提供的**参考素材**和**目标应用领域**（若未提供领域则主动询问）
2. 初始化工作目录 `outputs/[专利名称]/`，所有中间文件统一保留于此
3. 基于目标领域执行场景迁移与微创新设计，规避现有专利
4. 生成结构化大纲（含主旨四段式 + 各章节要点 + 预计附图 + 术语锁定 + 篇幅预算），与用户确认——**这是唯一的用户确认点**
5. 大纲确认后自动执行：4 个 Writer 并行生成 → Reviewer 三重审查 → 整合写入 .docx
6. 工作目录只保留 `01_outline.md` 和 `sections/*.md`（8 个章节文件，DOCX 写入前的最终文本），便于用户编辑回滚
7. 自动静默触发 Phase 5，生成防幻觉 AI 附图提示词
8. 用户编辑任意 `sections/*.md` 后只需重跑 Phase 3 即可重新生成 DOCX；附图修正走 Phase 6

---

## 必需输入 (Required Inputs)

在开始生成前，**必须**确认以下信息。若用户未主动提供，需主动询问：

| 输入项 | 必需 | 说明 | 示例 |
|--------|:----:|------|------|
| **参考素材** | 是 | 学术论文、技术文档、开源项目等 | PDF / 文本 / 链接 |
| **目标应用领域** | 是 | 专利要落地的具体工程场景，用于场景迁移与微创新 | 无人机集群侦察 / 工业焊缝检测 / 自动驾驶障碍物识别 |
| 现有专利参考 | 可选 | 同领域已有专利，用于差异化设计、规避查重 | 专利号 / 标题 / 摘要 |
| 输出目录 | 可选 | 工作目录，用于保留全部中间文件，默认 `outputs/[专利名称]/` | `outputs/uav_recon/` |

**目标应用领域**的三重作用：
1. **场景迁移**：将学术算法从实验室环境迁移至目标工程场景，重新推导技术痛点
2. **微创新设计**：基于目标领域的特定约束（数据特性、硬件限制、行业标准），设计区别于原始论文和现有技术的创新点
3. **规避专利查重**：通过领域特化的技术方案描述，与同领域已有专利形成差异化

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
- 行内公式：`$E = mc^2$`
- 独立公式：`$$\sum_{i=1}^{N} x_i$$`
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
- d）调用 `humanizer` skill 做最终人类化润色

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

**⑤ 静默写入**：提示词不输出到聊天窗口，直接写入 `[专利名称]_全套AI生图提示词.docx`。
警告段落设置为**粗体红色**（#CC0000）。

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

### Phase 0：输入确认与大纲生成

> 子步骤：工作目录初始化 → 场景迁移 → 微创新设计 → 主旨四段式 → 结构化大纲 → 用户确认

1. 读取用户提供的参考素材
2. 若用户未指定**目标应用领域**，**必须主动询问**，不可跳过
3. **初始化工作目录**（中间文件保留机制）：
   - 默认目录：`outputs/[专利名称简写]/`（专利名称简写从用户输入或参考素材推导，避免特殊字符）
   - 若用户指定了输出目录，则使用用户指定的路径
   - 工作目录用于存放整个工作流的全部中间产物，便于用户基于任一中间文件提出修改意见并断点重启
   - 详见后文【中间文件保留与断点重启机制】小节
4. 基于目标领域执行场景迁移：
   - 禁止照搬学术背景（数据集名称、实验室环境、benchmark 指标）
   - 将核心算法迁移至用户指定的实际工程场景
   - 从新场景的工程约束（数据采集条件、硬件限制、行业标准）重新推导技术痛点
5. 设计微创新点：
   - 分析参考素材中的核心技术贡献
   - 结合目标领域的特殊需求，提出至少 1-2 个差异化改进
   - 确保技术方案与现有技术（若已知）形成明确区分
6. **写作主旨四段式（全文骨架，详见 [writing-rules.md](references/writing-rules.md) ⚠️ 章节）**：

   `针对什么问题(背景) → 采取什么方法(方案) → 基于什么原理(实施) → 带来什么提升(效果)`

   关键约束：背景局限（1）-（N）↔ 发明目的优势（1）-（N）↔ 技术效果效果（1）-（N）**三方对应**；优势/效果条目**标题相同、措辞不同**；技术方案步骤数 ≥ 优势条目数。

7. **生成结构化大纲**（本流程的核心产出）：

   大纲必须包含以下内容，以结构化格式展示给用户。**编号统一用全角**`（1）（2）`：

   ```
   ▍主旨四段式（全文骨架）
       ① 针对什么问题：[1-2 句话浓缩本发明要解决的核心痛点]
       ② 采取什么方法：[1-2 句话浓缩本发明的核心技术方案]
       ③ 基于什么原理：[1-2 句话浓缩本发明的关键技术机理]
       ④ 带来什么提升：[1-2 句话浓缩本发明的可量化效果]

   一、发明名称：[名称，≤25字，体现方法/装置属性]
   二、技术领域：[1-2 句概述]
   三、背景技术要点：
       - 现有技术概况：[工程需求 + 现有技术介绍]
       - 任务场景描述：[本发明考虑的具体任务场景]
       - 现有技术局限（编号列举，与发明目的优势条目一一对应）：
         （1）[局限1]
         （2）[局限2]
         ...
       - 本发明引出句：[简述本发明如何改善上述局限]
   四、发明内容·发明目的要点：
       - 总起句：[本发明旨在改善...通过对...加以改进，提供一种...的方法。本发明的优势体现在：]
       - 优势条目（编号列举，与背景技术局限、技术效果效果**三方对应**，标题与效果条目相同）：
         （1）[优势标题1]：[做了什么 → 通过什么机理 → 带来什么] ← [源:论文X节 / 领域迁移设计]
         （2）[优势标题2]：[做了什么 → 通过什么机理 → 带来什么] ← [源:...]
         ...
       - 综述收尾句：[综上所述，本发明...]
   四、发明内容·技术解决方案要点：
       - 开场句（引用附图，给出大致流程）："本发明提供了一种技术解决方案...图1为本发明示意图。本发明的技术解决方案流程如图2所示，以下是该发明的大致流程："
       - 技术步骤（编号列举，步骤数 ≥ 优势条目数）：
         （1）[步骤标题]：[概要 + 机理说明]
         （2）[步骤标题]：[概要 + 机理说明]
         ...
   四、发明内容·技术效果要点：
       - 总起句：[本发明提供了一种创新的技术解决方案...并取得了以下技术成果：]
       - 效果条目（编号列举，与发明目的优势条目**标题相同、措辞不同**）：
         （1）[效果标题1，与优势1相同]：[带来什么 + 量化结果说明]
         （2）[效果标题2，与优势2相同]：[带来什么 + 量化结果说明]
         ...
       - 综述收尾句：[综上所述，本发明的技术解决方案...]
   五、预计附图清单：
       - 图1：[描述]
       - 图2：[描述]
       - ...
   六、具体实施方式·步骤拆分：
       - 步骤1：[标题]，简/繁=[简|繁]，预计子步骤数=[N]
       - 步骤2：[标题]，简/繁=[简|繁]，预计子步骤数=[N]
       - ...
   七、术语锁定表：
       - [学术术语A] → [专利术语A]（全文统一使用）
       - [学术术语B] → [专利术语B]（全文统一使用）
       - ...
   八、篇幅预算（参考 [writing-rules.md](references/writing-rules.md) 的"篇幅参考表"）：
       - 三、背景技术：~1000-1600 字
       - 四·发明目的：~500-900 字
       - 四·技术解决方案：~900-1400 字
       - 四·技术效果：~700-1100 字
       - 六、具体实施方式：~1200-3500 字
       - 全文目标总字数：4500-7500 字
   ```

8. 向用户展示大纲，等待用户确认。**这是整个流程中唯一的用户确认点**，大纲确认后全部自动完成，不再询问用户。

9. **确认后立即将大纲写入 `outputs/[专利名称]/01_outline.md`**，作为后续所有 Writer Agent 的统一输入源（断点重启时也从此文件读起）。

### Phase 1：任务拆分与并行生成（自动执行）

大纲确认后，自动进入多 Agent 并行生成流程。**所有 Agent 必须使用 opus 模型。**

**步骤 1 — 任务拆分**：根据确认的大纲，将全文拆分为以下 4 个独立任务：

| Writer Agent | 负责内容 | 字数上限 |
|-------------|---------|---------|
| **Writer-A** | 一、发明名称 + 二、技术领域 + 三、背景技术 | ~1200字 |
| **Writer-B** | 四、发明内容（发明目的 + 技术解决方案 + 技术效果 三个子节） | ~3500字 |
| **Writer-C** | 五、附图及附图的简单说明 + 六、具体实施方式·前半部分（前 N/2 步骤） | ~3500字 |
| **Writer-D** | 六、具体实施方式·后半部分（后 N/2 步骤 + 总结） | ~3500字 |

> 本交底书格式**不含摘要**（300字摘要），因此相比"说明书"格式减少了 Writer-E。

**步骤 2 — 准备每个 Writer 的上下文包**：

每个 Writer Agent 的 prompt 中必须注入以下内容：
1. **锁定的大纲**（仅与该 Writer 任务相关的部分）
2. **参考素材原文片段**（与该 Writer 负责章节对应的参考材料段落）
3. **术语锁定表**（从大纲中提取，确保所有 Writer 使用完全相同的术语）
4. **writing-rules.md 的完整禁用词表**（第一层去 AI 预防）
5. **信息源锚定要求**（铁律 5）：
   - 数值参数必须标注来源 `[源:论文X节]` 或 `[源:大纲约定]`
   - 无法标注来源的参数禁止编造，必须标记 `[待确认:具体问题]`
   - 信息源标注仅用于审查，写入 DOCX 前自动移除
6. **本 Writer 的字数上限**（严格遵守）
7. **对应章节的格式规范**（从 [writing-rules.md](references/writing-rules.md) 中提取相关章节，包括"背景技术·编号局限列举"、"发明目的编号条目"、"技术解决方案编号步骤"、"技术效果编号条目"、"具体实施方式·编号展开"）

**步骤 3 — 并行派发**：使用 Agent 工具并行启动 4 个 Writer Agent（单条消息中发出多个 Agent 调用），等待全部完成。

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
- Writer-C 的最后一个步骤末尾不加总结性语句
- Writer-D 从下一个步骤编号继续，开头不加过渡性引言
- 拼接为 `6_implementation.md` 后，由 Reviewer 在 Phase 2 中负责检查衔接处的段落过渡是否自然

### Phase 2：自动审查与修正（自动执行）

所有 Writer 完成后，自动启动 Reviewer Agent（使用 opus 模型）执行三重审查。

**审查 1 — 一致性检查**：
- 术语是否全文统一（对照术语锁定表，检查是否存在同义词轮换）
- 图号是否连续（图1~图N 无跳号）、正文图引用是否一致
- 编号连续性：背景技术局限 (1)-(N)、发明目的 (1)-(N)、技术解决方案 (1)-(N)、技术效果 (1)-(N)、具体实施方式步骤 (1)-(N)
- 发明目的中的"优势条目"与技术效果中的"效果条目"是否一一对应、一一映射到 技术解决方案 中的核心创新步骤
- Writer-C 和 Writer-D 的衔接是否自然（步骤编号连续、无重复、无遗漏）
- 发明内容的技术方案步骤是否与具体实施方式的详细步骤一一对应

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

**落盘策略**：Reviewer 的所有修改直接写回 `sections/*.md`（in-place 编辑）。**不保留任何审查中间文件**：审查报告、问题清单、Writer 退回轮次、humanizer 润色前/后对比都仅以 Reviewer 在聊天窗口的简要总结呈现，不落盘。如调用 `humanizer` / `CNpatent-humanizer` skill，也是对 sections 文件就地处理。

**Why**：按照"工作目录只保留 DOCX 写入前的最终态"的设计原则，审查/润色过程产物属于"过程态"，不应留在工作目录里污染编辑视图。如需精确的变更追溯，建议用户在 `outputs/[专利名称]/` 下做 `git init` 自行管理（详见后文【工作目录与断点重启机制】）。

### Phase 3：兜底清理与 DOCX 写入（自动执行）

sections/ 中已经是按章节组织的最终文本，本阶段只做"清理 + 写入 DOCX"两件事，没有合并步骤。

**步骤 1 — 兜底清理（in-place）**：对 sections/ 下的 8 个 .md 文件依次调用 `scripts/deai_cleanup.py` 的 `final_deai_cleanup()`（纯正则替换，不依赖 AI 判断），结果写回原文件。

**Why in-place**：保证 `sections/*.md` 永远反映 DOCX 中的实际内容；用户基于 sections/ 编辑后再次跑 Phase 3 时，cleanup 是幂等的，重复调用无副作用。这样用户无论何时打开 sections 文件，看到的都是与 DOCX 一致的"最终状态"。

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

### Phase 5：静默生成附图提示词（自动触发）

主文档保存后自动执行，**禁止在聊天窗口输出提示词内容**。使用 python-docx 创建独立文档 `[专利名称]_全套AI生图提示词.docx`，按图编号逐张写入：

- **主体段**：场景描述 + 中文标签的空间锚定（"位置编码 labeled in the top-left rectangular block"）
- **警告段**：粗体红色（#CC0000）的全大写 STRICT WARNING 段（铁律 4 ④）

完整代码模板见 [docx-patterns.md](references/docx-patterns.md) 的 "Anti-Hallucination Figure Prompts" 章节。

聊天窗口仅输出一句确认：
> ✅ 全套附图的防幻觉 AI 生图提示词已保存至 outputs/[专利名称]/[专利名称]_全套AI生图提示词.docx。

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

**输出文件**：`outputs/[专利名称]/[前缀]_[专利名称]_专利技术交底书.docx`

---

## 工作目录与断点重启机制

工作目录 `outputs/[专利名称]/` **只保留两类文件**：
1. `01_outline.md` —— Phase 0 用户确认的大纲（断点重启时从此读起）
2. `sections/*.md` —— 8 个章节文件，DOCX 写入前的最终文本（用户可直接编辑）

**设计原则**：审查报告、Writer 原始草稿、humanizer 前/后对比等"过程产物"一律不落盘。修改场景下用户只需要最终态；过程态由 Reviewer 在聊天窗口的总结承载，如需精确变更追溯由用户用 git 自行管理。

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
└── [专利名称]_全套AI生图提示词.docx     # Phase 5 静默生成的附图提示词
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

## 专利技术交底书文档结构（电学类交底书）

```
一、发明/实用新型名称              [Heading 1]
   一种...方法                                       [Normal]
二、所属技术领域                    [Heading 1]
   本发明涉及...                                     [Normal]
三、现有技术（背景技术）            [Heading 1]
   现有技术概况 + 任务场景 + （1）-（N）局限 + 引出句   [Normal]
四、发明内容                        [Heading 1]
  发明目的                          [Heading 2]
     总起 + （1）-（N）优势条目 + 综述句                [Normal]
  技术解决方案                      [Heading 2]
     开场（图引用）+ （1）-（N）步骤                    [Normal]
  技术效果                          [Heading 2]
     总起 + （1）-（N）效果条目 + 综述句                [Normal]
五、附图及附图的简单说明            [Heading 1]
   图X [描述]                                        [Caption]
六、具体实施方式                    [Heading 1]
   开场（图引用）+ （1）-（N）详细步骤                  [Normal]
   $LaTeX 公式$                                      [公式]
   变量解释                                          [Normal]
```

权利要求书由专利代理人根据本交底书另行撰写，不属于技术交底书范畴。

## 交付前质量检查清单

生成文本后、写入 DOCX 前，逐项核查：

| # | 检查项 | 要求 |
|---|--------|------|
| 1 | **主旨四段式** | 大纲与正文都能清晰对应"针对什么问题→采取什么方法→基于什么原理→带来什么提升"四个要素 |
| 2 | **一、发明名称** | ≤25字，体现方法/装置属性，"一种...方法/系统/装置" |
| 3 | **二、技术领域** | 1-2 句，"本发明涉及/属于...技术领域" 或 "本发明旨在提供一种...，适用于...领域" |
| 4 | **三、背景技术** | 现有技术概况 + 任务场景说明 + 编号局限（1）-（N） + 引出句，无学术引文，~1000-1600 字 |
| 5 | **四、发明目的** | 总起句 + `本发明的优势体现在：` + （1）-（N） 优势条目 + 综述收尾，无公式，~500-900 字 |
| 6 | **四、技术解决方案** | 开场句引用附图 + （1）-（N） 步骤，无公式，步骤数 ≥ 优势条目数，~900-1400 字 |
| 7 | **四、技术效果** | 总起句 + （1）-（N） 效果条目 + 综述收尾，**每条标题与发明目的优势完全相同、措辞不同**，~700-1100 字 |
| 8 | **优势↔效果对应** | 三方对应：背景技术局限（1）-（N）↔ 发明目的优势（1）-（N）↔ 技术效果效果（1）-（N） |
| 9 | **发明内容无公式** | 扫描"四、发明内容"全节，确认无 `$` 或 LaTeX 标记 |
| 10 | **术语一致性** | 同一技术要素全文只用一种叫法，无同义替换 |
| 11 | **五、附图说明** | 逐图一行："图X [描述]"，编号连续无跳号 |
| 12 | **六、具体实施方式** | 开场句引用附图 + 编号步骤 + 步骤引用附图 + 公式块 + 参数，~1200-3500 字 |
| 13 | **公式连续编号** | 公式编号（1）（2）...无跳号，仅出现在具体实施方式 |
| 14 | **编号符号全角** | 所有编号统一用全角`（1）（2）`，禁止半角 `(1)(2)` |
| 15 | **禁用词扫描** | 对照 writing-rules.md 禁用词表，无残留 AI 痕迹（铁律 3 三层过滤） |
| 16 | **无权利要求书** | 全文不出现"权利要求书"字样 |
| 17 | **Heading 样式保留** | 9 个标题段（6 H1 + 3 H2）的样式、文字、顺序与模板完全一致 |
| 18 | **全文总字数** | 4500-7500 字（不含发明名称） |
| 19 | **工作目录齐全** | `outputs/[专利名称]/` 下含 `01_outline.md` + `sections/` 子目录（8 个章节文件，无 `_part_*` 残留） |

## 参考规范

- [去 AI 痕迹与专利语言规范](references/writing-rules.md)
- [python-docx 代码模板](references/docx-patterns.md)（含模板章节定位、占位段删除、Run 分裂修复、链式替换、段落删除等模式）

## 插图写入

当用户提供图片文件时，使用 [docx-patterns.md](references/docx-patterns.md) 的 `insert_image_after()` 辅助函数，将图片插入到「五、附图说明」对应图题之后或「六、具体实施方式」对应步骤之后。

## 平台注意事项

Windows 上运行 Python 写入中文时需启用 UTF-8 模式（`PYTHONUTF8=1 python -X utf8 script.py`），详见 [docx-patterns.md](references/docx-patterns.md) 的 Common Issues 表。
