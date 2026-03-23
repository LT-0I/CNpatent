# DOCX Generation Patterns

## Python (python-docx) Template-Based

### Why Template-Based?

- Preserves the user's exact page layout, headers, footers, margins, fonts
- No risk of format mismatch — styles come from the user's own template
- Simpler code — just append paragraphs with existing styles

### Setup

```bash
pip install python-docx
```

### Step 1: Load Template & Discover Styles

```python
import os
from docx import Document
from docx.enum.style import WD_STYLE_TYPE

# Load built-in template from skill assets
template_path = os.path.join(
    os.path.expanduser('~'),
    '.claude', 'skills', 'CNpatent', 'assets', '专利交底书模板.docx'
)
doc = Document(template_path)

# Discover available paragraph styles
for style in doc.styles:
    if style.type == WD_STYLE_TYPE.PARAGRAPH:
        print(f'  Style: "{style.name}"')
```

Common template styles to look for:
- `Heading 1` or `标题 1` — section titles (技术领域, 背景技术, etc.)
- `Normal` or `正文` — body text
- `首行缩进` — body text with first-line indent
- `个人标题` — patent name (发明名称) title style
- `公式` or `MTDisplayEquation` — centered formula lines
- `图题` — figure caption style
- `List Paragraph` — list items (if any)

### 模板分节结构 (Critical)

内置模板包含 **4 个 Section**，每个 Section 有独立的页眉和页脚。分节符嵌入在特定段落的 `pPr/sectPr` 中，**删除这些段落会破坏整个文档的页面结构**。

```
Section 0 (页眉: "说明书摘要")  → 段落[0]  ← 携带 sectPr，绝不能删除
Section 1 (页眉: "摘要附图")    → 段落[1]  ← 携带 sectPr，绝不能删除
Section 2 (页眉: "说明书")      → 段落[2]~[12]，其中[12]携带 sectPr
Section 3 (页眉: "说明书附图")  → 段落[13]~[34]，图题占位符
```

**铁律**：段落[0]、[1]、[12] 携带分节符（sectPr），必须保留。清理模板内容时只能清空文本，不能删除这些段落。

### Step 2: 定位分节边界段落

```python
from docx.oxml.ns import qn

def find_section_boundaries(doc):
    """找到所有携带 sectPr 的段落索引，这些段落是分节边界，不能删除"""
    boundaries = []
    for i, p in enumerate(doc.paragraphs):
        ppr = p._element.find(qn('w:pPr'))
        if ppr is not None and ppr.find(qn('w:sectPr')) is not None:
            boundaries.append(i)
    return boundaries
    # 内置模板返回: [0, 1, 12]
    # Section 0 结束于 para[0]  → 说明书摘要
    # Section 1 结束于 para[1]  → 摘要附图
    # Section 2 结束于 para[12] → 说明书
    # Section 3 结束于文档末尾   → 说明书附图
```

### Step 3: Style Helper Functions

```python
def add_title(doc, text):
    """Add patent name using 个人标题 style."""
    para = doc.add_paragraph(text)
    for name in ['个人标题']:
        try:
            para.style = doc.styles[name]
            break
        except KeyError:
            continue
    return para

def add_h1(doc, text):
    """Add a section title using the template's Heading 1 style."""
    para = doc.add_paragraph(text)
    for name in ['Heading 1', '标题 1']:
        try:
            para.style = doc.styles[name]
            break
        except KeyError:
            continue
    return para

def add_body(doc, text):
    """Add body text using the template's normal/indented style."""
    para = doc.add_paragraph(text)
    for name in ['首行缩进', 'Normal', '正文']:
        try:
            para.style = doc.styles[name]
            break
        except KeyError:
            continue
    return para

def add_formula(doc, latex_text):
    """Add a LaTeX formula line using the template's formula style."""
    para = doc.add_paragraph(latex_text)
    for name in ['公式', 'MTDisplayEquation']:
        try:
            para.style = doc.styles[name]
            break
        except KeyError:
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            break
    return para

def add_fig_caption(doc, text):
    """Add figure caption using 图题 style."""
    para = doc.add_paragraph(text)
    for name in ['图题']:
        try:
            para.style = doc.styles[name]
            break
        except KeyError:
            continue
    return para
```

### Step 4: 分节感知写入 (Section-Aware Writing)

核心思路：在 Section 边界段落**之前**插入内容，利用 `_element.addprevious()` 实现精确定位。

```python
import os
from docx import Document
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from copy import deepcopy

template_path = os.path.join(
    os.path.expanduser('~'),
    '.claude', 'skills', 'CNpatent', 'assets', '专利交底书模板.docx'
)
doc = Document(template_path)
body = doc.element.body

# ── 1. 定位分节边界 ──
boundaries = find_section_boundaries(doc)  # [0, 1, 12]
sect0_para = doc.paragraphs[boundaries[0]]  # Section 0 边界 (说明书摘要)
sect1_para = doc.paragraphs[boundaries[1]]  # Section 1 边界 (摘要附图)
sect2_para = doc.paragraphs[boundaries[2]]  # Section 2 边界 (说明书)

# ── 2. 清除模板占位内容（保留边界段落本身）──
# 删除 Section 2 中的占位段落 (para[2]~[11])，保留 para[12]
for i in range(11, 1, -1):  # 逆序删除 11→2
    el = doc.paragraphs[i]._element
    el.getparent().remove(el)

# 删除 Section 3 中的图题占位段落 (para[13]~[34])
# 注意：删除 Section 2 占位后索引已变化，重新定位
# 此时 boundaries 已失效，用 sect2_para 的位置来定位
# 简单做法：删除 sect2_para 之后的所有段落
while True:
    last = doc.paragraphs[-1]
    if last._element is sect2_para._element:
        break
    # 检查是否是最终 sectPr（文档末尾），不能删
    if last._element.find(qn('w:pPr')) is not None:
        ppr = last._element.find(qn('w:pPr'))
        if ppr.find(qn('w:sectPr')) is not None:
            break
    last._element.getparent().remove(last._element)

# ── 3. Section 0：说明书摘要（在 sect0_para 之前插入）──
def insert_before(anchor, doc, text, style_func):
    """在锚点段落前插入新段落"""
    p = style_func(doc, text)
    anchor._element.addprevious(p._element)
    return p

insert_before(sect0_para, doc, '本发明公开了一种...方法。', add_body)

# ── 4. Section 1：摘要附图 → 保持空白，不写入任何内容 ──

# ── 5. Section 2：说明书正文（在 sect2_para 之前插入）──
insert_before(sect2_para, doc, '一种XXX方法', add_title)

insert_before(sect2_para, doc, '技术领域', add_h1)
insert_before(sect2_para, doc, '本发明属于...', add_body)

insert_before(sect2_para, doc, '背景技术', add_h1)
insert_before(sect2_para, doc, '...', add_body)

insert_before(sect2_para, doc, '发明内容', add_h1)
# ★ 发明内容标准结构（必须按此顺序插入）
# ① 目的句
insert_before(sect2_para, doc, '本发明的目的是提供一种XXX方法，以解决上述现有技术存在的问题。', add_body)
# ② 引入句
insert_before(sect2_para, doc, '为实现上述目的，本发明提供了一种XXX方法，包括：', add_body)
# ③ 独立权利要求主要步骤（每步独立成段，不编号，分号结尾，末步句号）
insert_before(sect2_para, doc, '步骤A技术描述；', add_body)
insert_before(sect2_para, doc, '步骤B技术描述；', add_body)
insert_before(sect2_para, doc, '步骤N技术描述。', add_body)  # 末步句号
# ④ "可选的"从属特征展开（对每个需要细化的主步骤各写一组）
insert_before(sect2_para, doc, '可选的，所述[步骤B关键词]，具体包括：', add_body)
insert_before(sect2_para, doc, '细节子步骤1；', add_body)
insert_before(sect2_para, doc, '细节子步骤2。', add_body)
# ... 重复更多"可选的"组 ...
# ⑤ 技术效果
insert_before(sect2_para, doc, '本发明的技术效果为：', add_body)
insert_before(sect2_para, doc, '本发明通过...；...；...。', add_body)

insert_before(sect2_para, doc, '附图说明', add_h1)
# ★ 附图说明通用法律声明（必须插入）
insert_before(sect2_para, doc, '为了更清楚地说明本发明实施例或现有技术中的技术方案，下面将对实施例中所需要使用的附图作简单的介绍，显而易见地，下面描述中的附图仅仅是本发明的一些实施例，对于本领域普通技术人员来讲，在不付出创造性劳动的前提下，还可以根据这些附图获得其他的附图。', add_body)
insert_before(sect2_para, doc, '构成本申请的一部分的附图用来提供对本申请的进一步理解，本申请的示意性实施例及其说明用于解释本申请，并不构成对本申请的不当限定。在附图中：', add_body)
# 然后逐图描述
insert_before(sect2_para, doc, '图1为...示意图。', add_body)

insert_before(sect2_para, doc, '具体实施方式', add_h1)
# ★ 具体实施方式通用法律声明（必须插入，共5段）
insert_before(sect2_para, doc, '现详细说明本发明的多种示例性实施方式，该详细说明不应认为是对本发明的限制，而应理解为是对本发明的某些方面、特性和实施方案的更详细的描述。', add_body)
insert_before(sect2_para, doc, '应理解本发明中所述的术语仅仅是为描述特别的实施方式，并非用于限制本发明。另外，对于本发明中的数值范围，应理解为还具体公开了该范围的上限和下限之间的每个中间值。在任何陈述值或陈述范围内的中间值以及任何其他陈述值或在所述范围内的中间值之间的每个较小的范围也包括在本发明内。这些较小范围的上限和下限可独立地包括或排除在范围内。', add_body)
insert_before(sect2_para, doc, '在不背离本发明的范围或精神的情况下，可对本发明说明书的具体实施方式做多种改进和变化，这对本领域技术人员而言是显而易见的。由本发明的说明书得到的其他实施方式对技术人员而言是显而易见的。本申请说明书和实施例仅是示例性的。', add_body)
insert_before(sect2_para, doc, '关于本文中所使用的「包含」「包括」「具有」「含有」等等，均为开放性的用语，即意指包含但不限于。', add_body)
insert_before(sect2_para, doc, '需要说明的是，在不冲突的情况下，本申请中的实施例及实施例中的特征可以相互组合。下面将参考附图并结合实施例来详细说明本申请。', add_body)

# ★ 实施例概述段（法律声明之后、详细步骤之前）
insert_before(sect2_para, doc, '实施例一', add_body)
insert_before(sect2_para, doc, '如图1至图N所示，本实施例中提供了一种XXX方法，包括：步骤A简称、步骤B简称、...、以及步骤N简称。', add_body)
# 可选：实施环境说明段（硬件平台、传感器参数等）
# insert_before(sect2_para, doc, '在本实施例中，以...为应用场景。...', add_body)
insert_before(sect2_para, doc, '本实施例的具体实施方案包括：', add_body)

# ★ 详细步骤（主体内容）
insert_before(sect2_para, doc, '（1）步骤标题', add_body)
insert_before(sect2_para, doc, '步骤正文...如图X所示...', add_body)
insert_before(sect2_para, doc, '$$E = U \\Sigma V^T$$', add_formula)
# ... 更多步骤 ...

# ★ 实施例技术效果段（详细步骤之后）
insert_before(sect2_para, doc, '本实施例的技术效果为：', add_body)
insert_before(sect2_para, doc, '能够XXX：本实施例通过...，...。', add_body)
insert_before(sect2_para, doc, '能够YYY：本实施例通过...，...。', add_body)

# ★ 实施例总结段
insert_before(sect2_para, doc, '综上所述，本实施例通过...，解决了现有技术在...中存在的...问题。该方法在...的前提下，实现了...，为...提供了一种...的技术方案。', add_body)

# ★ 结尾段（固定文本，必须逐字复制）
insert_before(sect2_para, doc, '以上所述，仅为本申请较佳的具体实施方式，但本申请的保护范围并不局限于此，任何熟悉本技术领域的技术人员在本申请揭露的技术范围内，可轻易想到的变化或替换，都应涵盖在本申请的保护范围之内。因此，本申请的保护范围应该以权利要求的保护范围为准。', add_body)

# ── 6. Section 3：说明书附图（在文档末尾追加）──
for fig_num in range(1, 9):
    add_fig_caption(doc, f'图{fig_num}')
    add_fig_caption(doc, '')  # 空行（留给图片插入位置）

# ── 7. 保存 ──
doc.save('一种XXX方法_专利技术交底书.docx')
```

注意：技术交底书中**不包含**权利要求书，权利要求书由专利代理人另行撰写。

### Step 4: Anti-Hallucination Figure Prompts (Separate File)

```python
from docx import Document
from docx.shared import Pt, RGBColor

prompt_doc = Document()  # Blank doc is OK for prompts

for fig_num in range(1, 11):
    prompt_doc.add_heading(f'Figure {fig_num}: ...', level=1)
    para = prompt_doc.add_paragraph()

    # Main body (normal text)
    run_main = para.add_run('Scientific diagram, patent illustration style...')
    run_main.font.size = Pt(10.5)

    # Warning (bold, red)
    warning = (
        'STRICT WARNING: The diagram MUST ONLY contain the following '
        'Simplified Chinese text labels: [...]. '
        'DO NOT GENERATE ANY OTHER TEXT, LETTERS, NUMBERS, SYMBOLS, '
        'OR FAKE CHINESE CHARACTERS.'
    )
    run_warn = para.add_run(warning)
    run_warn.bold = True
    run_warn.font.size = Pt(10.5)
    run_warn.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)

prompt_doc.save('一种XXX方法_全套AI生图提示词.docx')
```

## Image Insertion

To insert figures into the patent docx (when image files are available):

```python
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

doc.add_picture('图1.png', width=Inches(5.0))
last_paragraph = doc.paragraphs[-1]
last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
```

---

## Post-Generation Modification Patterns

### Run Splitting Problem (Critical)

python-docx 中，Word 文件里的文本经常被拆分到多个 Run 中。例如 "图6" 可能被拆成 Run[0]="图"、Run[1]="6"。**直接在单个 Run 中搜索 "图6" 永远找不到。**

**解决方案：段落级替换函数**

```python
def para_replace(paragraph, old, new):
    """段落级替换：合并所有 run 文本 → 替换 → 重写到第一个 run，保留其格式"""
    full_text = paragraph.text
    if old not in full_text:
        return False
    new_text = full_text.replace(old, new)
    runs = paragraph.runs
    if not runs:
        return False
    runs[0].text = new_text
    for run in runs[1:]:
        run._element.getparent().remove(run._element)
    return True
```

**注意**：此函数会将整段文本合并到第一个 Run，继承第一个 Run 的格式。如果段落中有多种格式（如部分加粗），需要更精细的处理。对于专利文档的正文段落，此方案已够用。

### Chain Replacement with Placeholders

图号重编号（如删除图4/图5后，图6→图4、图7→图5...图10→图8）存在链式冲突：先替换 图10→图8，再替换 图8→图6 会把已改好的 图8 再次替换。

**解决方案：两阶段占位符**

```python
# Phase 1: 全部替换为唯一占位符
PHASE1 = [
    ('图10', '##R_F8##'),
    ('图9',  '##R_F7##'),
    ('图8',  '##R_F6##'),
    ('图7',  '##R_F5##'),
    ('图6',  '##R_F4##'),
]
# Phase 2: 占位符替换为最终值
PHASE2 = [
    ('##R_F8##', '图8'),
    ('##R_F7##', '图7'),
    ('##R_F6##', '图6'),
    ('##R_F5##', '图5'),
    ('##R_F4##', '图4'),
]

# 执行：两遍扫描所有段落
for p in doc.paragraphs:
    for old, new in PHASE1:
        para_replace(p, old, new)
for p in doc.paragraphs:
    for old, new in PHASE2:
        para_replace(p, old, new)
```

**注意**：Phase 1 列表中长字符串必须排在前面（"图10" 先于 "图1"），避免子串匹配冲突。

### Paragraph Deletion

删除段落必须**从后向前**按索引逆序删除，否则前面的删除会导致后续索引失效。

```python
paras_to_delete_idx = [44, 45, 134, 135]  # 要删除的段落索引

for idx in sorted(paras_to_delete_idx, reverse=True):
    el = doc.paragraphs[idx]._element
    el.getparent().remove(el)
```

定位段落的常用策略：
- **按内容匹配**：`if '某关键词' in p.text`
- **按样式匹配**：`if p.style.name == '图题' and p.text.strip() == '图4'`
- **按位置关系**：删除某段后，检查下一段是否为空行，一并删除

### Post-Modification Verification

修改 .docx 后，必须重新加载文件并验证：

```python
import re
doc2 = Document(output_path)

# 1. 验证附图说明连续性
for p in doc2.paragraphs:
    if '为本发明实施例' in p.text:
        print(f"  附图: {p.text[:60]}")

# 2. 验证正文图引用
for p in doc2.paragraphs:
    refs = re.findall(r'如图[\d至~]+所示', p.text)
    if refs:
        print(f"  引用: {refs}")

# 3. 验证图题段落
for p in doc2.paragraphs:
    if p.style.name == '图题' and p.text.strip():
        print(f"  图题: {p.text}")
```

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Template style not found | Style name mismatch | Inspect template styles first |
| Chinese text garbled | Encoding issue | Windows: `PYTHONUTF8=1 python -X utf8 script.py` |
| Formula renders as box | OLE object expected | Write as plain LaTeX text string instead |
| Headers/footers lost | Created new doc instead of loading template | Always use `Document('template.docx')` |
| EBUSY error | File open in Word | Change output filename or close Word |
| Run splitting: "图6" split as "图"+"6" | Word internal formatting runs | Use `para_replace` (paragraph-level), not run-level search |
| Chain replacement collision | 图10→图8 then 图8→图6 | Two-phase placeholder strategy |
| Paragraph index shift after deletion | Deleting changes subsequent indices | Always delete in reverse index order |
