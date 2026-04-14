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
2. 基于目标领域执行场景迁移与微创新设计，规避现有专利
3. 生成结构化大纲（含各章节要点、预计附图清单、术语锁定表），与用户确认——**这是唯一的用户确认点**
4. 大纲确认后，自动并行派发 4 个 Writer Agent 生成全部章节 → Reviewer Agent 自动审查修正 → 整合写入 .docx（全程无需用户干预）
5. 自动静默触发 Phase 5，生成防幻觉 AI 附图提示词
6. 如需修正附图（删除冗余图、重编号），执行 Phase 6

---

## 必需输入 (Required Inputs)

在开始生成前，**必须**确认以下信息。若用户未主动提供，需主动询问：

| 输入项 | 必需 | 说明 | 示例 |
|--------|:----:|------|------|
| **参考素材** | 是 | 学术论文、技术文档、开源项目等 | PDF / 文本 / 链接 |
| **目标应用领域** | 是 | 专利要落地的具体工程场景，用于场景迁移与微创新 | 无人机集群侦察 / 工业焊缝检测 / 自动驾驶障碍物识别 |
| 现有专利参考 | 可选 | 同领域已有专利，用于差异化设计、规避查重 | 专利号 / 标题 / 摘要 |

**目标应用领域**的三重作用：
1. **场景迁移**：将学术算法从实验室环境迁移至目标工程场景，重新推导技术痛点
2. **微创新设计**：基于目标领域的特定约束（数据特性、硬件限制、行业标准），设计区别于原始论文和现有技术的创新点
3. **规避专利查重**：通过领域特化的技术方案描述，与同领域已有专利形成差异化

---

## 铁律 (Core Execution Constraints)

### 铁律 1：模板驱动，严禁从零创建

本 Skill 使用的模板是 **电学类专利申请技术交底书** 格式（代理机构标准模板），与传统"说明书"格式（有摘要、附图、权利要求四个分节）截然不同。生成 .docx 时**绝对禁止创建空白文档**，必须加载本 Skill 内置的模板：

```python
from pathlib import Path
from docx import Document

# 智能查找模板路径（兼容项目级和全局安装）
candidates = [
    Path.cwd() / '.claude' / 'skills' / 'CNpatent' / 'assets' / '专利交底书模板.docx',
    Path.home() / '.claude' / 'skills' / 'CNpatent' / 'assets' / '专利交底书模板.docx',
]
template_path = next((p for p in candidates if p.exists()), None)
if template_path is None:
    raise FileNotFoundError('找不到专利交底书模板.docx，请确认 Skill 安装正确')
doc = Document(str(template_path))
```

**模板结构要点**（详见 [docx-patterns.md](references/docx-patterns.md)）：
- **封面页**：顶部含一个 24 行 × 4 列的信息表（发明人/申请人基本资料），供用户填写，**Skill 不得修改此表**
- **注意事项**：封面后有"交底书注意事项"段落（8 段 `缺省文本` 样式），原样保留
- **正文七节**（每节由一个加粗 14pt 宋体的标题段引出）：
  - 一、发明/实用新型名称
  - 二、所属技术领域
  - 三、现有技术（背景技术）
  - 四、发明内容（含 `发明目的` / `技术解决方案` / `3、技术效果` 三个加粗子标题）
  - 五、附图及附图的简单说明
  - 六、具体实施方式
  - ~~七、权利要求书~~（**Skill 必须删除此节**，不生成任何内容）
- 每节原模板内含 `【...】` 填写说明和 `例：...` 示例段，Skill 写入内容前**必须删除**这些占位段

执行要求：
- **严禁修改**封面表格、页眉页脚、页边距、字体设置
- 只允许删除 `【...】` 填写说明、`例：...` 示例段、以及 `七、权利要求书` 整节
- 章节标题段（`一、` ~ `六、` 和三个子标题）必须**原样保留**，不得改动加粗/字号/字体
- 新写入内容使用 `宋体 14pt` 以匹配模板排版
- 始终另存为新文件 `[专利名称]_专利技术交底书.docx`，**不得覆盖模板**

### 铁律 2：纯文本 LaTeX 公式

所有数学公式以纯文本 LaTeX 字符串写入文档：
- 行内公式：`$E = mc^2$`
- 独立公式：`$$\sum_{i=1}^{N} x_i$$`
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

**本交底书格式 `七、权利要求书` 一节严禁生成任何内容**。代码必须主动**删除**模板中 `七、权利要求书` 标题段及其后所有段落（到 body 末尾的 sectPr 之前），以明确告知读者权利要求书由代理人另行撰写。

若用户明确要求生成权利要求书，应回复：
> 权利要求书由专利代理人根据交底书另行撰写，不属于技术交底书范畴。建议交由专利代理人处理。

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
   一、发明名称：[名称，≤25字，体现方法/装置属性]
   二、技术领域：[1-2 句概述]
   三、背景技术要点：
       - 现有技术概况：[工程需求 + 现有技术介绍]
       - 现有技术局限（编号列举）：
         (1) [局限1]
         (2) [局限2]
         ...
       - 本发明引出句：[简述本发明如何改善上述局限]
   四、发明内容·发明目的要点：
       - 总起句
       - 优势条目（编号列举，(1)-(N)）：
         (1) [优势1] ← [源:论文X节 / 领域迁移设计]
         (2) [优势2] ← [源:...]
         ...
       - 综述收尾句
   四、发明内容·技术解决方案要点：
       - 开场句（引用附图，给出大致流程）
       - 技术步骤（编号列举，(1)-(N)）：
         (1) [步骤标题]：[概要]
         (2) [步骤标题]：[概要]
         ...
   四、发明内容·技术效果要点：
       - 总起句
       - 效果条目（编号列举，(1)-(N)，与发明目的一一对应）：
         (1) [效果1]：[机理说明]
         ...
       - 综述收尾句
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
   ```

6. 向用户展示大纲，等待用户确认。**这是整个流程中唯一的用户确认点**，大纲确认后全部自动完成，不再询问用户。

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

**Writer-C 与 Writer-D 的衔接约定**：
- 大纲中六、的步骤按序号一分为二，前半给 Writer-C，后半给 Writer-D
- Writer-C 的最后一个步骤末尾不加总结性语句
- Writer-D 从下一个步骤编号继续，开头不加过渡性引言
- 两者的衔接由 Reviewer 在 Phase 2 中负责检查和修正

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

### Phase 3：整合与 DOCX 写入（自动执行）

审查通过后，将 4 个 Writer 的输出按以下顺序整合，并写入 DOCX：

**整合顺序**：
1. Writer-A 的输出 → 一、发明名称 + 二、技术领域 + 三、背景技术
2. Writer-B 的输出 → 四、发明内容（发明目的 / 技术解决方案 / 技术效果 三子节）
3. Writer-C 的前半 → 五、附图说明
4. Writer-C 的后半 → 六、具体实施方式·前半部分
5. Writer-D 的输出 → 六、具体实施方式·后半部分

**DOCX 写入**：使用**章节定位替换**策略。详见 [docx-patterns.md](references/docx-patterns.md) 的完整代码模板。

核心要点：
1. 加载模板后，使用 `find_sections()` 按标题文字前缀（`一、`、`二、`、`三、`、`四、`、`五、`、`六、`、`七、`）定位各节的起始 body 索引
2. 同时定位 `四、发明内容` 下的三个子标题（`发明目的`、`技术解决方案`、`3、技术效果`），用于精准拆分 Writer-B 的内容
3. 对每一节：删除标题之后、下一标题之前的所有占位段（`【...】` 填写说明、`例：...` 示例段、空段）
4. **在每节标题段之后逐段插入新内容**，插入时使用 `addprevious` 或 `addnext`
5. 对 `七、权利要求书` 一节：删除标题段及其后所有非 sectPr 段落，该节内容为空
6. 新插入段落必须显式设置字体为 `宋体 14pt`（runs 中 `font.name='宋体'`、`font.size=Pt(14)`），否则会与模板其他段落不一致

**写入前执行最终兜底替换**（见 [writing-rules.md](references/writing-rules.md) 的"最终 DOCX 写入前自动替换"章节）：对全文执行纯正则匹配替换，确保无禁用词残留。

**若存在 `[待确认]` 标记**：在聊天窗口输出汇总提示，列出所有待用户确认的参数/内容，格式为：
```
⚠️ 以下内容需要您确认或补充：
1. [待确认:XXX的具体参数值] — 位于"六、具体实施方式·步骤(3)"
2. [待确认:YYY的取值范围] — 位于"六、具体实施方式·步骤(5)"
请提供相关信息，我将更新文档。
```

### Phase 4：DOCX 写入后验证（自动执行）

每次生成或修改 .docx 后，必须验证文档完整性：

```python
import re
from docx import Document

doc_check = Document(output_path)
texts = [p.text for p in doc_check.paragraphs]
full_text = '\n'.join(texts)

# 1. 检查所有主要节标题都存在
required_headings = ['一、发明', '二、所属技术领域', '三、现有技术', '四、发明内容', '五、附图', '六、具体实施方式']
for h in required_headings:
    assert any(h in t for t in texts), f'缺少章节标题: {h}'

# 2. 检查 七、权利要求书 已被删除
assert not any('七、权利要求书' in t for t in texts), '七、权利要求书 未删除'
assert not any('【申请人通过本发明想要保护' in t for t in texts), '权利要求书占位文字残留'

# 3. 检查 四、发明内容 的三个子标题仍然存在
for sub in ['发明目的', '技术解决方案', '技术效果']:
    assert any(sub in t for t in texts), f'缺少子标题: {sub}'

# 4. 检查附图说明连续性（图1~图N 无跳号）
fig_nums_in_desc = []
for t in texts:
    m = re.match(r'^图\s*(\d+)', t.strip())
    if m:
        fig_nums_in_desc.append(int(m.group(1)))
if fig_nums_in_desc:
    assert fig_nums_in_desc == sorted(set(fig_nums_in_desc)), f'附图编号不连续: {fig_nums_in_desc}'

# 5. 检查正文引用不超出附图范围
max_fig = max(fig_nums_in_desc) if fig_nums_in_desc else 0
for t in texts:
    for m in re.finditer(r'图\s*(\d+)', t):
        ref_num = int(m.group(1))
        assert ref_num <= max_fig, f'引用了不存在的图{ref_num}！'

# 6. 检查封面表格未被破坏（应保留 24 行）
assert len(doc_check.tables) >= 1, '封面表格丢失'
assert len(doc_check.tables[0].rows) >= 20, '封面表格行数异常'
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

## 专利技术交底书文档结构（电学类交底书格式）

```
[封面页]
  封面信息表（24行×4列，发明人/申请人基本资料，用户填写）
  交底书注意事项（8 段原样保留）

[正文六节]
  一、发明/实用新型名称
     [发明名称，≤25字]

  二、所属技术领域
     [1-2 句技术领域概述]

  三、现有技术（背景技术）
     [现有技术概况段]
     [应用背景与任务场景段]
     (1) [现有技术局限1]
     (2) [现有技术局限2]
     ...
     [本发明引出句]

  四、发明内容：
     发明目的
        [总起句]
        [本发明的优势体现在：]
        (1) [优势1]
        (2) [优势2]
        ...
        [综上所述，...]
     技术解决方案
        [开场句，引用附图]
        (1) [步骤1]
        (2) [步骤2]
        ...
     3、技术效果
        [总起句]
        (1) [效果1]
        (2) [效果2]
        ...
        [综上所述，...]

  五、附图及附图的简单说明
     图1 [描述]
     图2 [描述]
     ...

  六、具体实施方式
     [实施例开场，如图X所示，...]
     (1) [详细步骤1]
     [公式、参数、子步骤]
     (2) [详细步骤2]
     ...

  —— 权利要求书 删除 ——
```

注：权利要求书由专利代理人根据本交底书另行撰写，**交底书中严禁包含权利要求书**。如用户要求生成权利要求书，应明确告知其不属于技术交底书范畴，建议交由专利代理人处理。

## 交付前质量检查清单

生成文本后、写入 DOCX 前，逐项核查：

| # | 检查项 | 要求 |
|---|--------|------|
| 1 | **一、发明名称** | ≤25字，体现方法/装置属性，"一种...方法/系统/装置" |
| 2 | **二、技术领域** | 1-2 句，"本发明涉及/属于...技术领域" 或 "本发明旨在提供一种...，适用于...领域" |
| 3 | **三、背景技术** | 包含：现有技术概况 + 任务场景说明 + 编号局限(1)-(N) + 引出句，无学术引文 |
| 4 | **四、发明目的** | 总起句 + `本发明的优势体现在：` + (1)-(N) 条目 + 综述收尾，无公式 |
| 5 | **四、技术解决方案** | 开场句引用附图 + (1)-(N) 步骤概要，无公式，步骤数与六节详细步骤一一对应 |
| 6 | **四、技术效果** | 总起句 + (1)-(N) 效果条目 + 综述收尾，每条对应一个发明目的 |
| 7 | **发明内容无公式** | 扫描"四、发明内容"全节，确认无 `$` 或 LaTeX 标记 |
| 8 | **术语一致性** | 同一技术要素全文只用一种叫法，无同义替换 |
| 9 | **五、附图说明** | 逐图一行："图X [描述]" 或 "图 X [描述]"，编号连续无跳号 |
| 10 | **六、具体实施方式** | 开场句引用附图 + 编号步骤 + 步骤引用附图 + 公式块 + 参数 |
| 11 | **公式连续编号** | 公式编号（1）（2）...无跳号，仅出现在具体实施方式 |
| 12 | **禁用词扫描** | 对照 writing-rules.md 禁用词表，无残留 AI 痕迹（铁律 3 三层过滤） |
| 13 | **无权利要求书** | 七、权利要求书 整节已删除（含标题段、【占位说明】、尾随空段） |
| 14 | **封面表格保留** | 封面信息表 24 行结构未被破坏 |
| 15 | **章节标题加粗** | 一、~六、六个主标题 + 发明目的/技术解决方案/3、技术效果 三个子标题仍保持粗体 14pt 宋体 |

## 参考规范

- [去 AI 痕迹与专利语言规范](references/writing-rules.md)
- [python-docx 代码模板](references/docx-patterns.md)（含模板章节定位、占位段删除、Run 分裂修复、链式替换、段落删除等模式）

## 插图写入

当用户提供图片文件时，在"五、附图及附图的简单说明"每图描述行之后、或在"六、具体实施方式"的对应步骤后插入图片：

```python
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# 在指定锚点段落之后插入图片
def insert_image_after(anchor_para, image_path, width_inches=5.0):
    # 创建新段落并置中
    new_para = doc.add_paragraph()
    new_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = new_para.add_run()
    run.add_picture(image_path, width=Inches(width_inches))
    # 移动到锚点之后
    anchor_para._element.addnext(new_para._element)
    return new_para
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
