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
from pathlib import Path
from docx import Document
from docx.enum.style import WD_STYLE_TYPE

# 智能查找模板路径（兼容项目级和全局安装）
candidates = [
    Path.cwd() / '.claude' / 'skills' / 'CNpatent' / 'assets' / '专利交底书模板.docx',
    Path.home() / '.claude' / 'skills' / 'CNpatent' / 'assets' / '专利交底书模板.docx',
]
template_path = next((p for p in candidates if p.exists()), None)
if template_path is None:
    raise FileNotFoundError('找不到专利交底书模板.docx，请确认 Skill 安装正确')
doc = Document(str(template_path))

# Discover available paragraph styles
for style in doc.styles:
    if style.type == WD_STYLE_TYPE.PARAGRAPH:
        print(f'  Style: "{style.name}"')
```

本模板使用的样式非常简单，全部内容都使用 `Normal` 样式，通过 run 级别的字体属性（宋体 14pt，标题加粗）区分标题和正文。

可用样式一览：
- `Normal` — 正文和标题共用此样式
- `缺省文本` — 注意事项段落使用
- `Heading 1` ~ `Heading 9` — 模板中未使用，但存在于样式表中

### 模板结构 (Critical)

内置模板是**电学类专利申请技术交底书**格式，结构如下：

```
=== 封面页 ===
Table[0]: 24行 × 4列 信息表（发明人/申请人基本资料）← 绝不能修改
Para[0]-[1]: 空段
Para[2]: "为了方便与您的沟通..." ← 封面说明文字
Para[3]: 空段
Para[4]: 空段 [SECTPR] ← 分节符，封面页/正文页的分界，绝不能删除

=== 正文页 ===
Para[5]: 空段
Para[6]: "交底书注意事项：" [BOLD] ← 原样保留
Para[7]-[14]: 注意事项8段 (缺省文本样式) ← 原样保留
Para[15]: 空段

--- 七个章节 ---
Para[16]: "一、发明/实用新型名称" [BOLD]
Para[17]-[22]: 【占位说明】+ 例 + 空段 ← 写入前删除

Para[23]: "二、所属技术领域" [BOLD]
Para[24]-[27]: 【占位说明】+ 例 + 空段 ← 写入前删除

Para[28]: "三、现有技术（背景技术）" [BOLD]
Para[29]-[33]: 【占位说明】+ 例 + 空段 ← 写入前删除

Para[34]: "四、发明内容：" [BOLD]
  Para[35]: "发明目的" [BOLD] ← 子标题，保留
  Para[36]-[38]: 【占位说明】+ 例 ← 写入前删除
  Para[39]: "技术解决方案" [BOLD] ← 子标题，保留
  Para[40]-[43]: 【占位说明】+ 例 ← 写入前删除
  Para[44]: "3、技术效果" [BOLD] ← 子标题，保留
  Para[45]-[59]: 【占位说明】+ 例 + 大量空段 ← 写入前删除

Para[60]: "五、附图及附图的简单说明" [BOLD]
Para[61]-[66]: 【占位说明】+ 例 + 空段 ← 写入前删除

Para[67]: "六、具体实施方式" [BOLD]
Para[68]-[70]: 【占位说明】+ 例 ← 写入前删除

Para[71]: "七、权利要求书" [BOLD] ← 整节删除（含标题）
Para[72]-[74]: 【占位说明】+ 空段 ← 整节删除
```

**铁律**：
1. `Para[4]` 携带 sectPr 分节符，绝不能删除
2. 封面表格（Table[0]）和注意事项段落（Para[6]-[14]）必须原样保留
3. 章节标题段（"一、"~"六、" 和三个子标题）保留，不得改动格式
4. "七、权利要求书" 整节（标题+内容+空段）必须完全删除

### Step 2: 定位章节标题段

```python
import re

def find_sections(doc):
    """按标题文字前缀定位各节的段落索引"""
    sections = {}
    sub_sections = {}  # 四、发明内容的子标题
    for i, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        if text.startswith('一、'):
            sections['一'] = i
        elif text.startswith('二、'):
            sections['二'] = i
        elif text.startswith('三、'):
            sections['三'] = i
        elif text.startswith('四、'):
            sections['四'] = i
        elif text.startswith('五、'):
            sections['五'] = i
        elif text.startswith('六、'):
            sections['六'] = i
        elif text.startswith('七、'):
            sections['七'] = i
        # 四、发明内容 的子标题
        if text == '发明目的':
            sub_sections['发明目的'] = i
        elif text == '技术解决方案':
            sub_sections['技术解决方案'] = i
        elif text.startswith('3、技术效果'):
            sub_sections['技术效果'] = i
    return sections, sub_sections
    # 内置模板返回:
    # sections = {'一': 16, '二': 23, '三': 28, '四': 34, '五': 60, '六': 67, '七': 71}
    # sub_sections = {'发明目的': 35, '技术解决方案': 39, '技术效果': 44}
```

### Step 3: 删除占位内容 + 删除权利要求书

核心思路：保留标题段（和子标题段），删除标题之后、下一标题之前的所有非标题段（占位说明、示例、空段）。对"七、权利要求书"则连标题一起删除。

```python
from docx.oxml.ns import qn

def clear_template_placeholders(doc):
    """删除模板中所有占位内容，保留标题段"""
    sections, sub_sections = find_sections(doc)

    # 所有需要保留的标题段索引
    keep_indices = set(sections.values()) | set(sub_sections.values())
    # 七、权利要求书 的标题也要删除
    keep_indices.discard(sections.get('七'))

    # 确定删除范围：从"一、"开始到文档末尾
    start = sections['一']
    total = len(doc.paragraphs)

    # 收集要删除的段落索引（标题段之外的所有段落 + 七的标题）
    to_delete = []
    for i in range(start, total):
        if i not in keep_indices:
            # 检查是否携带 sectPr（不能删）
            ppr = doc.paragraphs[i]._element.find(qn('w:pPr'))
            if ppr is not None and ppr.find(qn('w:sectPr')) is not None:
                continue
            to_delete.append(i)

    # 逆序删除
    for idx in sorted(to_delete, reverse=True):
        el = doc.paragraphs[idx]._element
        el.getparent().remove(el)

    return doc
```

### Step 4: 内容写入辅助函数

本模板所有内容使用 `Normal` 样式 + 宋体 14pt。标题已存在于模板中，新写入的都是正文段。

```python
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def add_body(doc, text):
    """添加正文段：Normal 样式 + 宋体 14pt"""
    para = doc.add_paragraph(text)
    para.style = doc.styles['Normal']
    for run in para.runs:
        run.font.name = '宋体'
        run.font.size = Pt(14)
        # 设置东亚字体
        rpr = run._element.get_or_add_rPr()
        rFonts = rpr.find(qn('w:rFonts'))
        if rFonts is None:
            rFonts = OxmlElement('w:rFonts')
            rpr.insert(0, rFonts)
        rFonts.set(qn('w:eastAsia'), '宋体')
    return para

def add_formula(doc, latex_text):
    """添加公式段：宋体 14pt，居中"""
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    para = add_body(doc, latex_text)
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return para

def insert_after(anchor, doc, text, style_func=None):
    """在锚点段落之后插入新段落"""
    if style_func is None:
        style_func = add_body
    p = style_func(doc, text)
    anchor._element.addnext(p._element)
    return p

def insert_before(anchor, doc, text, style_func=None):
    """在锚点段落之前插入新段落"""
    if style_func is None:
        style_func = add_body
    p = style_func(doc, text)
    anchor._element.addprevious(p._element)
    return p
```

### Step 5: 章节定位替换写入 (Section-Aware Writing)

核心思路：清除占位内容后，每个标题段后面紧跟下一个标题段。在两个标题之间插入新内容。使用 `insert_before(下一标题)` 策略，按序插入的段落自然排列在标题之后。

```python
import os
import re
from pathlib import Path
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt

# ── 1. 加载模板 ──
candidates = [
    Path.cwd() / '.claude' / 'skills' / 'CNpatent' / 'assets' / '专利交底书模板.docx',
    Path.home() / '.claude' / 'skills' / 'CNpatent' / 'assets' / '专利交底书模板.docx',
]
template_path = next((p for p in candidates if p.exists()), None)
doc = Document(str(template_path))

# ── 2. 定位章节 ──
sections, sub_sections = find_sections(doc)

# ── 3. 清除占位内容（含删除七、权利要求书）──
clear_template_placeholders(doc)

# 清除后重新定位（索引已变化）
sections, sub_sections = find_sections(doc)

# ── 4. 构建标题→下一标题的映射 ──
# 清除后，标题段紧密相连，需要知道每个标题后面的下一个标题
all_headings = sorted(
    list(sections.items()) + list(sub_sections.items()),
    key=lambda x: x[1]
)
# 构建：heading_key → next_heading_para 的映射
next_heading = {}
for i, (key, idx) in enumerate(all_headings):
    if i + 1 < len(all_headings):
        next_key, next_idx = all_headings[i + 1]
        next_heading[key] = doc.paragraphs[next_idx]
    else:
        next_heading[key] = None  # 最后一个标题，追加到末尾

# ── 5. 写入各节内容 ──

# --- 一、发明名称 ---
anchor = next_heading['一']  # 即"二、"标题段
insert_before(anchor, doc, '一种XXX方法')

# --- 二、技术领域 ---
anchor = next_heading['二']  # 即"三、"标题段
insert_before(anchor, doc, '本发明涉及XXX技术领域，具体涉及一种XXX方法。')

# --- 三、背景技术 ---
anchor = next_heading['三']  # 即"四、"标题段
insert_before(anchor, doc, '现有技术概况段落...')
insert_before(anchor, doc, '(1) 现有技术局限1；')
insert_before(anchor, doc, '(2) 现有技术局限2。')
insert_before(anchor, doc, '本发明引出句...')

# --- 四、发明内容 ---
# 发明目的（在"技术解决方案"子标题之前插入）
anchor = next_heading['发明目的']  # 即"技术解决方案"标题段
insert_before(anchor, doc, '本发明的目的在于提供一种XXX方法，以解决上述问题。')
insert_before(anchor, doc, '本发明的优势体现在：')
insert_before(anchor, doc, '(1) 优势1；')
insert_before(anchor, doc, '(2) 优势2。')
insert_before(anchor, doc, '综上所述，本发明...')

# 技术解决方案（在"3、技术效果"子标题之前插入）
anchor = next_heading['技术解决方案']  # 即"3、技术效果"标题段
insert_before(anchor, doc, '如图1所示，本发明提供了一种XXX方法，包括以下步骤：')
insert_before(anchor, doc, '(1) 步骤1概要；')
insert_before(anchor, doc, '(2) 步骤2概要。')

# 技术效果（在"五、"标题之前插入）
anchor = next_heading['技术效果']  # 即"五、"标题段
insert_before(anchor, doc, '采用上述技术方案，本发明的技术效果为：')
insert_before(anchor, doc, '(1) 效果1；')
insert_before(anchor, doc, '(2) 效果2。')
insert_before(anchor, doc, '综上所述，本发明...')

# --- 五、附图说明 ---
anchor = next_heading['五']  # 即"六、"标题段
insert_before(anchor, doc, '图1 XXX方法总体流程示意图。')
insert_before(anchor, doc, '图2 XXX模块结构示意图。')

# --- 六、具体实施方式（在文档末尾追加，因为七已删除）---
# 六、是最后一个标题，next_heading['六'] 为 None
# 直接在 body 末尾 append 即可（doc.add_paragraph 默认 append）
# 但为保持一致性，也可定位六的标题后用 addnext
add_body(doc, '如图1所示，本实施例提供了一种XXX方法，包括以下步骤：')
add_body(doc, '(1) 步骤1标题')
add_body(doc, '步骤1详细描述...')
add_body(doc, '$$公式1$$ \\quad (1)')
# ... 更多步骤 ...

# ── 6. 保存 ──
doc.save('一种XXX方法_专利技术交底书.docx')
```

注意事项：
1. 技术交底书中**不包含**权利要求书，权利要求书由专利代理人另行撰写
2. 数学公式以纯文本 LaTeX 写入，**仅出现在"六、具体实施方式"中**，"四、发明内容"中严禁出现公式
3. 封面表格、注意事项、章节标题格式都不得修改

### Step 6: Anti-Hallucination Figure Prompts (Separate File)

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
- **按位置关系**：删除某段后，检查下一段是否为空行，一并删除

### Post-Modification Verification

修改 .docx 后，必须重新加载文件并验证：

```python
import re
from docx import Document

doc_check = Document(output_path)
texts = [p.text for p in doc_check.paragraphs]

# 1. 检查所有主要节标题都存在
required_headings = ['一、发明', '二、所属技术领域', '三、现有技术', '四、发明内容', '五、附图', '六、具体实施方式']
for h in required_headings:
    assert any(h in t for t in texts), f'缺少章节标题: {h}'

# 2. 检查 七、权利要求书 已被删除
assert not any('七、权利要求书' in t for t in texts), '七、权利要求书 未删除'

# 3. 检查 四、发明内容 的三个子标题仍然存在
for sub in ['发明目的', '技术解决方案', '技术效果']:
    assert any(sub in t for t in texts), f'缺少子标题: {sub}'

# 4. 检查附图编号连续性
fig_nums = []
for t in texts:
    m = re.match(r'^图\s*(\d+)\s', t.strip())
    if m:
        fig_nums.append(int(m.group(1)))
if fig_nums:
    assert fig_nums == list(range(1, len(fig_nums) + 1)), f'附图编号不连续: {fig_nums}'

# 5. 检查正文引用不超出附图范围
max_fig = max(fig_nums) if fig_nums else 0
for t in texts:
    for m in re.finditer(r'图\s*(\d+)', t):
        ref_num = int(m.group(1))
        assert ref_num <= max_fig, f'引用了不存在的图{ref_num}！'

# 6. 检查封面表格未被破坏
assert len(doc_check.tables) >= 1, '封面表格丢失'
assert len(doc_check.tables[0].rows) >= 20, '封面表格行数异常'
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
| 新段落字体不一致 | 未显式设置 run 字体 | 每个 run 必须设置 `font.name='宋体'` + `font.size=Pt(14)` + eastAsia='宋体' |
| 封面表格被破坏 | 删除范围过大 | 只从"一、"开始删除占位内容，不碰封面和注意事项 |
| sectPr 丢失 | 误删了 Para[4] | 删除前检查 `pPr/sectPr`，携带 sectPr 的段落绝不能删 |
