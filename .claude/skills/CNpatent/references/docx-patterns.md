# DOCX Generation Patterns

适用模板：`assets/交底书模板.docx`。

> **辅助函数实现位于 `scripts/cnpatent_docx.py`**：本文档只给出**用法示例**与**为什么这么做的解释**。函数源代码统一维护在该 .py 文件中，避免每次 Writer/orchestrator 调用时重复定义带来的漂移与笔误。

## 目录

- [Why Template-Based?](#why-template-based)
- [Setup](#setup)
- [模板结构](#模板结构)
- [辅助函数总览](#辅助函数总览)
- [Section-Aware Writing 完整示例](#section-aware-writing-完整示例)
- [Anti-Hallucination Figure Prompts](#anti-hallucination-figure-prompts)
- [Image Insertion](#image-insertion)
- [Post-Generation Modification Patterns](#post-generation-modification-patterns)
  - [Run Splitting Problem](#run-splitting-problem-critical)
  - [Chain Replacement with Placeholders](#chain-replacement-with-placeholders)
  - [Paragraph Deletion](#paragraph-deletion)
  - [Post-Modification Verification](#post-modification-verification)
- [Common Issues & Fixes](#common-issues--fixes)

---

## Why Template-Based?

- 保留模板的页面布局、页眉页脚、页边距、字体设置
- 模板使用 `Heading 1` / `Heading 2` 样式承载标题，正文段用 `Normal` 样式继承字体
- 字体属性由模板样式表决定，Python 端不要手动覆盖

## Setup

```bash
pip install python-docx
```

## 模板结构

模板共 **18 段，0 表**，结构如下：

```
Para[0]  [Heading 1] 一、发明/实用新型名称
Para[1]  [Normal   ] (空段)
Para[2]  [Heading 1] 二、所属技术领域
Para[3]  [Normal   ] (空段)
Para[4]  [Heading 1] 三、现有技术（背景技术）
Para[5]  [Normal   ] (空段)
Para[6]  [Heading 1] 四、发明内容
Para[7]  [Heading 2] 发明目的
Para[8]  [Normal   ] (空段)
Para[9]  [Heading 2] 技术解决方案
Para[10] [Normal   ] (空段)
Para[11] [Heading 2] 技术效果
Para[12] [Normal   ] (空段)
Para[13] [Heading 1] 五、附图及附图的简单说明
Para[14] [图片     ] (空段，图片占位)
Para[15] [Caption  ] 图1
Para[16] [Heading 1] 六、具体实施方式
Para[17] [Normal   ] (空段)
```

可用样式：

- `Heading 1` — 一级标题（一～六）
- `Heading 2` — 二级子标题（发明目的 / 技术解决方案 / 技术效果）
- `Normal` — 普通正文段
- `Caption` — 图题
- `公式` — 数学公式段（用于纯文本 LaTeX）
- `图片` — 图片锚点

**铁律**：

1. 9 个 Heading 段（6 个 H1 + 3 个 H2）必须**原样保留**，不得改动文字、样式或顺序
2. 普通正文用 `Normal` 样式，公式用 `公式` 样式，图题用 `Caption` 样式；不要手动设 `font.name` / `font.size`——由样式表决定
3. 写入策略：定位下一个 Heading 段，用 `addprevious` 在它前面插入新内容
4. 模板中预设的空段（Para[1]/[3]/[5]/...）在写入新内容前应清除，否则会留下空行

---

## 辅助函数总览

`scripts/cnpatent_docx.py` 一次性维护了所有 docx 操作的助手函数。SKILL.md 铁律 1 的代码块演示了如何 import：

| 函数 | 用途 |
|---|---|
| `find_template_path()` | 智能查找 `交底书模板.docx`（兼容项目级和全局安装）|
| `load_template()` | 加载模板返回 `Document` |
| `find_sections(doc)` | 列出所有 Heading 段：`(idx, level, text, paragraph)` |
| `get_section_anchors(doc)` | 返回 `{章节key: 下一个标题段}` 映射，便于 `insert_before` |
| `clear_placeholders(doc)` | 清除模板预置的空段、`Caption` 段和 `图片` 占位段 |
| `add_body(doc, text, style='Normal')` | 追加正文段 |
| `insert_before(anchor, doc, text, style='Normal')` | 在锚点段之前插入新段 |
| `append_at_end(doc, text, style='Normal')` | 追加到文档末尾（用于六、最后一节）|
| `add_formula(doc, latex_text, anchor=None)` | 添加 LaTeX 公式段（必须用 raw 字面量 `r'...'`）|
| `add_caption(doc, text, anchor=None)` | 添加图题段 |
| `para_replace(paragraph, old, new)` | 段落级替换，绕过 python-docx 的 Run-splitting 问题 |
| `verify_docx(doc_path)` | Phase 4 的完整 6 项断言（标题/排除关键字/附图连续/公式样式/全角编号）|

`get_section_anchors()` 返回的 keys：`'一', '二', '三', '四', '五', '六', '发明目的', '技术解决方案', '技术效果'`。最后一个 key（`'六'`）的 next 为 `None`，表示在文档末尾追加。

---

## Section-Aware Writing 完整示例

以下示例假设 `cnpatent_docx` 已按 SKILL.md 铁律 1 的代码块导入。

```python
# 1. 加载模板 + 清占位 + 锚点定位
doc = load_template()
clear_placeholders(doc)
anchors = get_section_anchors(doc)

# --- 一、发明名称 ---
insert_before(anchors['一'], doc,
    '一种基于改进灰狼优化算法的无人机集群区域覆盖侦察任务规划方法')

# --- 二、技术领域 ---
insert_before(anchors['二'], doc,
    '本发明涉及无人机集群协同任务规划技术领域，具体涉及一种基于改进灰狼'
    '优化算法的无人机集群区域覆盖侦察任务规划方法。')

# --- 三、背景技术 ---
insert_before(anchors['三'], doc, '无人机集群协同作战是指通过多架无人机的协同配合……')
insert_before(anchors['三'], doc, '本发明考虑的任务场景为：……主要体现在：')
insert_before(anchors['三'], doc, '（1）容易陷入局部最优解：……')
insert_before(anchors['三'], doc, '（2）收敛速度慢：……')
# ... 更多局限编号 ...
insert_before(anchors['三'], doc,
    '本发明提出一种基于改进灰狼优化算法的无人机集群区域覆盖侦察任务规划方法，'
    '旨在改善上述不足，实现更高效、全面的区域覆盖侦察效果。')

# --- 四、发明内容 ---
# 注意：'四'锚点指向'发明目的'子标题，所以 insert_before(anchors['四']) 会写在
# '四、发明内容'标题之后、'发明目的'子标题之前。本节通常不写正文内容
# （由发明目的/技术解决方案/技术效果三个子节承担）。

# 发明目的（在'技术解决方案'子标题之前插入）
insert_before(anchors['发明目的'], doc, '本发明旨在改善灰狼优化算法...本发明的优势体现在：')
insert_before(anchors['发明目的'], doc, '（1）提高目标覆盖率：……')
insert_before(anchors['发明目的'], doc, '（2）增加算法的可靠性：……')
# ...
insert_before(anchors['发明目的'], doc, '综上所述，本发明……')

# 技术解决方案（在'技术效果'子标题之前插入）
insert_before(anchors['技术解决方案'], doc,
    '本发明提供了一种技术解决方案……图1为本发明示意图。'
    '本发明的技术解决方案流程如图2所示，以下是该发明的大致流程：')
insert_before(anchors['技术解决方案'], doc, '（1）构建无人机集群的任务分配模型，……')
# ...

# 技术效果（在'五、'之前插入）
insert_before(anchors['技术效果'], doc, '本发明...取得了以下技术成果：')
insert_before(anchors['技术效果'], doc, '（1）提高目标覆盖率：……')
# ...
insert_before(anchors['技术效果'], doc, '综上所述，本发明的技术解决方案对……')

# --- 五、附图说明（用 add_caption 写图题）---
add_caption(doc, '图1 面向区域侦察覆盖的无人机集群任务规划示意图', anchor=anchors['五'])
add_caption(doc, '图2 面向区域覆盖侦察的无人机集群任务规划总体流程图', anchor=anchors['五'])
add_caption(doc, '图3 动态头狼选择策略流程图', anchor=anchors['五'])

# --- 六、具体实施方式（最后一节，append 到文档末尾）---
append_at_end(doc, '如图3所示，动态头狼的选择策略以及狼群更新策略步骤如下：')
append_at_end(doc, '（1）首先进行初始化，随机生成一群灰狼，每个灰狼代表一个潜在解x，'
                   '随后计算其适应度值。')
append_at_end(doc, '（2）α狼的选择，其中α狼被定义为适应度最高的个体。')

# 公式段用 add_formula，使用模板的 `公式` 样式；LaTeX 字符串必须是 raw 字面量
add_formula(doc, r'$\alpha = \arg\max_{i} f(x_i) \quad （1）$')
append_at_end(doc, r'其中$f(x_i)$为当前灰狼的适应度值函数。')
# ... 更多步骤、公式、变量解释 ...

# 2. 保存 + 验证
output_path = 'outputs/uav_recon/一种基于改进灰狼优化算法的无人机集群区域覆盖侦察任务规划方法_专利技术交底书.docx'
doc.save(output_path)
verify_docx(output_path)
```

注意事项：

1. 数学公式以纯文本 LaTeX 写入，使用 `公式` 段落样式，**仅出现在「六、具体实施方式」中**，"四、发明内容" 中严禁出现公式
2. LaTeX 字符串必须用 Python **原始字符串字面量** `r'...'`，否则 `\a` / `\b` / `\f` 会被解释为控制字符（BEL/BS/FF），破坏 docx 序列化
3. Heading 1 / Heading 2 / Caption / 公式 / Normal 样式由模板决定，不要在 Python 端覆盖字体
4. 编号符号统一用**全角**`（1）（2）`，不用半角 `(1)(2)`
5. 始终另存为新文件 `[专利名称]_专利技术交底书.docx`，**不得覆盖模板**

---

## Anti-Hallucination Figure Prompts

附图提示词写入**独立文档**（不是主交底书），用普通 `Document()` 创建即可：

```python
from docx import Document
from docx.shared import Pt, RGBColor

prompt_doc = Document()  # 空白文档即可

for fig_num in range(1, 11):
    prompt_doc.add_heading(f'Figure {fig_num}: ...', level=1)
    para = prompt_doc.add_paragraph()

    # 主体（普通字号）
    run_main = para.add_run('Scientific diagram, patent illustration style...')
    run_main.font.size = Pt(10.5)

    # 警告段（粗体红色）
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

prompt_doc.save('outputs/xxx/xxx_全套AI生图提示词.docx')
```

## Image Insertion

To insert figures into the patent docx (when image files are available):

```python
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

def insert_image_after(anchor_para, doc, image_path, width_inches=5.0):
    """在指定锚点段落之后插入图片，居中。"""
    new_para = doc.add_paragraph()
    new_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = new_para.add_run()
    run.add_picture(image_path, width=Inches(width_inches))
    anchor_para._element.addnext(new_para._element)
    return new_para
```

---

## Post-Generation Modification Patterns

### Run Splitting Problem (Critical)

python-docx 中，Word 文件里的文本经常被拆分到多个 Run 中。例如 "图6" 可能被拆成 `Run[0]="图"`、`Run[1]="6"`。**直接在单个 Run 中搜索 "图6" 永远找不到。**

**解决方案**：使用 `cnpatent_docx.para_replace(paragraph, old, new)` —— 段落级替换函数，合并所有 run 文本后替换，再写回第一个 run（继承格式）。

注意：此函数会将整段文本合并到第一个 Run，继承第一个 Run 的格式。如果段落中有多种格式（如部分加粗），需要更精细的处理。对于专利文档的正文段落，此方案已够用。

### Chain Replacement with Placeholders

图号重编号（如删除图4/图5后，图6→图4、图7→图5...图10→图8）存在链式冲突：先替换 `图10→图8`，再替换 `图8→图6` 会把已改好的 `图8` 再次替换。

**解决方案：两阶段占位符**

```python
from cnpatent_docx import para_replace

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

修改 .docx 后，必须重新加载文件并验证，调用 `cnpatent_docx.verify_docx(output_path)`：

```python
from cnpatent_docx import verify_docx

verify_docx('outputs/xxx_专利技术交底书.docx')
# 任一断言失败时抛出 AssertionError，定位到出错段落
```

`verify_docx()` 检查 6 项必备断言：

1. 9 个模板标题段（6 H1 + 3 H2）完整保留
2. 全文无 `权利要求书` 字样
3. 附图编号 `图1..图N` 在「五、附图说明」中连续无跳号
4. 正文图引用编号不超出附图说明的最大编号
5. 公式段**仅**出现在「六、具体实施方式」中，且段落样式必须为 `公式`
6. 所有编号统一用**全角**`（N）`，无半角 `(N)` 残留

实现见 `scripts/cnpatent_docx.py` 的 `verify_docx()` 函数与 `REQUIRED_HEADINGS` 常量。

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| Template style not found | Style name mismatch | Inspect template styles first via `for s in doc.styles: print(s.name)` |
| Chinese text garbled (Windows) | ANSI default encoding | Run with `PYTHONUTF8=1 python -X utf8 script.py`，或脚本头部加 `import sys; sys.stdout.reconfigure(encoding='utf-8')` |
| Formula renders as box | OLE object expected | Write as plain LaTeX text string instead — use `add_formula(doc, r'...')` |
| LaTeX 公式写入失败 (XML compatibility error) | `\a` / `\b` / `\f` 被 Python 解释为控制字符 | LaTeX 字符串必须用 Python raw 字面量 `r'...'` |
| Headers/footers lost | Created new doc instead of loading template | Always use `load_template()` from `cnpatent_docx` |
| EBUSY error | File open in Word | Change output filename or close Word |
| Run splitting: "图6" split as "图"+"6" | Word internal formatting runs | Use `para_replace` (paragraph-level), not run-level search |
| Chain replacement collision | 图10→图8 then 图8→图6 | Two-phase placeholder strategy |
| Paragraph index shift after deletion | Deleting changes subsequent indices | Always delete in reverse index order |
| 正文段字体跟标题段不一致 | 在 Python 端手动覆盖了 `font.name` / `font.size` | 删除手动字体设置，让 `Normal` / `Heading` 样式生效 |
| 标题段被改成正文 | 误将 Heading 段当作占位段删除 | `clear_placeholders` 必须跳过所有 `Heading 1` / `Heading 2` 段 |
| 写入位置错乱 | `insert_before` 用错了锚点 | 用 `get_section_anchors()` 返回的"下一标题"作为锚点 |
