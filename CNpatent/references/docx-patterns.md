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
- `公式` or `MTDisplayEquation` — centered formula lines
- `List Paragraph` — list items (if any)

### Step 2: Write Content with Style Mapping

```python
def add_section_title(doc, text):
    """Add a section title using the template's Heading 1 style."""
    para = doc.add_paragraph(text)
    # Try to apply template's heading style
    for style_name in ['Heading 1', '标题 1']:
        try:
            para.style = doc.styles[style_name]
            break
        except KeyError:
            continue
    return para

def add_body_text(doc, text):
    """Add body text using the template's normal/indented style."""
    para = doc.add_paragraph(text)
    for style_name in ['首行缩进', 'Normal', '正文']:
        try:
            para.style = doc.styles[style_name]
            break
        except KeyError:
            continue
    return para

def add_formula(doc, latex_text):
    """Add a LaTeX formula line using the template's formula style."""
    para = doc.add_paragraph(latex_text)
    for style_name in ['公式', 'MTDisplayEquation']:
        try:
            para.style = doc.styles[style_name]
            break
        except KeyError:
            # Fallback: center-aligned Normal
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            break
    return para
```

### Step 3: Assemble Full Document (技术交底书)

```python
import os
from docx import Document

# Load template (skill built-in or user-provided)
template_path = os.path.join(
    os.path.expanduser('~'),
    '.claude', 'skills', 'CNpatent', 'assets', '专利交底书模板.docx'
)
doc = Document(template_path)

# --- 说明书 ---
add_section_title(doc, '技术领域')
add_body_text(doc, '本发明属于...技术领域，具体涉及一种...方法。')

add_section_title(doc, '背景技术')
add_body_text(doc, '...')

add_section_title(doc, '发明内容')
add_body_text(doc, '...')

add_section_title(doc, '附图说明')
add_body_text(doc, '图1为...示意图。')

add_section_title(doc, '具体实施方式')
add_body_text(doc, '...')

# Formulas in 具体实施方式
add_formula(doc, '$$E = U \\Sigma V^T$$')
add_body_text(doc, '其中，$U$为正交矩阵，$\\Sigma$为奇异值矩阵。')

# --- 说明书摘要 ---
add_section_title(doc, '说明书摘要')
add_body_text(doc, '本发明公开了一种...方法。')

# Save as new file (NEVER overwrite the template!)
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

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Template style not found | Style name mismatch | Inspect template styles first |
| Chinese text garbled | Encoding issue | Use `sys.stdout.reconfigure(encoding='utf-8')` |
| Formula renders as box | OLE object expected | Write as plain LaTeX text string instead |
| Headers/footers lost | Created new doc instead of loading template | Always use `Document('template.docx')` |
| EBUSY error | File open in Word | Change output filename or close Word |
