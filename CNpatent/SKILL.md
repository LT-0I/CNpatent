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
3. 按 Phase 1→2 分阶段增量生成交底书正文，每阶段经 `humanizer` 去 AI 痕迹后展示，用户确认后再推进
4. 用户全部确认后，加载内置模板写入 .docx 文件
5. 自动静默触发 Phase 3，生成防幻觉 AI 附图提示词

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
- 先检查模板中可用的段落样式，再做样式映射（Heading 1 / Normal / 首行缩进 / 公式 等）
- **严禁修改**模板自带的页眉、页脚、页码、页面边距、字体设置
- 始终另存为新文件 `[专利名称]_专利技术交底书.docx`，**不得覆盖模板**

如果用户在工作目录下有自己的模板文件，优先使用用户提供的模板。

### 铁律 2：纯文本 LaTeX 公式

所有数学公式以纯文本 LaTeX 字符串写入文档：
- 行内公式：`$E = mc^2$`
- 独立公式：`$$\sum_{i=1}^{N} x_i$$`
- 公式**仅出现**在「具体实施方式」中，**严禁出现**在「发明内容」中

### 铁律 3：去 AI 痕迹（双重审查）

生成每一阶段的专利文本后，必须执行**双重去 AI 痕迹处理**：

**第一重 — 内置规则检查**：对照 [writing-rules.md](references/writing-rules.md) 中的禁用词表逐条检查并替换（显著提升→改善、卓越的→较高的、颠覆性的→删除，等）。

**第二重 — humanizer skill 审查**：调用 `humanizer` skill 对生成文本进行二次审查，识别并消除内置规则未覆盖的残余 AI 写作特征（如过度使用排比、不自然的连接词、夸大性修饰等）。

最终文本必须符合专利文书的严谨、客观、技术性风格，读起来像领域工程师而非 AI 所写。

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

---

## 执行流程 (Execution Protocol)

### Phase 0：输入确认与场景迁移

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
5. 向用户简要汇报场景迁移结果和微创新方向，确认后进入 Phase 1

### Phase 1：说明书正文

按以下顺序生成：

```
发明名称
技术领域（1-2 句）
背景技术（最多 3 段，无学术综述）
发明内容（纯文本，无公式；有益效果合并在末尾）
附图说明（每图一行）
说明书摘要（≤300 字）
```

生成后执行**铁律 3 双重去 AI 痕迹处理**（内置规则 + `humanizer`）。

**输出**：向用户展示以上章节，等待确认。

### Phase 2：具体实施方式

- 工程操作手册风格，写"如何做"而非"为什么"
- 每个步骤必须引用至少一张附图（"如图X所示，…"）
- 所有核心计算以纯文本 LaTeX 公式表达
- 公式后紧跟每个变量的物理含义解释
- 给出具体参数值（如 N=128、K=20、λ=0.2）

生成后执行**铁律 3 双重去 AI 痕迹处理**（内置规则 + `humanizer`）。

**输出**：向用户展示，等待确认。

### DOCX 写入（全部确认后执行）

```python
import os
from docx import Document
from docx.enum.style import WD_STYLE_TYPE

# 1. 加载内置模板
template_path = os.path.join(
    os.path.expanduser('~'),
    '.claude', 'skills', 'CNpatent', 'assets', '专利交底书模板.docx'
)
doc = Document(template_path)

# 2. 检查可用样式
available = [s.name for s in doc.styles if s.type == WD_STYLE_TYPE.PARAGRAPH]

# 3. 样式映射写入
def add_heading(doc, text):
    p = doc.add_paragraph(text)
    for name in ['Heading 1', '标题 1']:
        if name in available:
            p.style = doc.styles[name]
            break
    return p

def add_body(doc, text):
    p = doc.add_paragraph(text)
    for name in ['首行缩进', 'Normal', '正文']:
        if name in available:
            p.style = doc.styles[name]
            break
    return p

def add_formula(doc, latex_text):
    p = doc.add_paragraph(latex_text)
    for name in ['公式', 'MTDisplayEquation']:
        if name in available:
            p.style = doc.styles[name]
            break
        else:
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p

# 4. 按章节写入内容（说明书各节 + 说明书摘要）
# 5. 另存为新文件
doc.save('一种XXX方法_专利技术交底书.docx')
```

### Phase 3：静默生成附图提示词（自动触发）

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

---

## 专利技术交底书文档结构

```
【说明书】
  发明名称
  技术领域
  背景技术
  发明内容（含有益效果）
  附图说明
  具体实施方式

【说明书摘要】（≤300 字）
```

注：权利要求书由专利代理人根据本交底书另行撰写，交底书中不包含。
如用户明确要求生成权利要求书，可参考 [claims-guide.md](references/claims-guide.md) 单独生成。

## 参考规范

- [去 AI 痕迹与专利语言规范](references/writing-rules.md)
- [python-docx 代码模板](references/docx-patterns.md)
- [权利要求书撰写指南](references/claims-guide.md)（仅供参考，交底书中不生成）

## 插图写入

当用户提供图片文件时：

```python
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc.add_picture('图1.png', width=Inches(5.0))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
```
