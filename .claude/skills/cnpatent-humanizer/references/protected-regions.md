# 受保护区域识别规则

> 本文档定义了 cnpatent-humanizer 在执行任何修改前必须识别并排除的"受保护区域"。
> 这些区域要么是法定固定文本（修改会导致专利不规范），要么是技术内容（修改会
> 引入语义错误），任何 Pass A-E 的处理都必须先确认目标段不在保护清单中。

## 一、章节标题段（不动）

特征：单独成段的加粗 14pt 宋体段落，文字以下列前缀开头：
- `一、` `二、` `三、` `四、` `五、` `六、` `七、`
- `发明目的`
- `技术解决方案`
- `3、技术效果`

**识别正则**：
```regex
^(一|二|三|四|五|六|七)、|^发明目的$|^技术解决方案$|^3、技术效果
```

**处理**：完全不动，包括字号、字体、加粗状态。

---

## 二、附图描述段（半保护：仅允许极轻微调整）

特征：在"五、附图及附图的简单说明"节内，固定格式：
```
图X 为本发明实施例[中的/提供的][描述][示意图/流程图]。
```

**识别**：
```regex
^图\s*\d+\s*[，,]?\s*为本发明实施例
```

**处理**：
- 不允许改写句式
- 不允许加入"所述"
- 不允许使用本文档中的禁用词替换（如"卓越"→"较高"）
- **允许**修正错别字、统一标点（中文逗号→中文逗号）
- **允许**统一末尾标点（中间图分号、最后一图句号）

---

## 三、公式段（不动）

特征：包含 LaTeX 标记的段落：
- 行内公式：包含 `$...$`
- 独立公式：包含 `$$...$$`
- 公式编号：行末 `（X）` 或 `(X)` 紧跟在公式后

**识别正则**：
```regex
\$.+\$|\\frac|\\sum|\\int|\\mathbf|\\sigma|\\alpha
```

**处理**：完全不动公式部分。但**允许**修改公式之前的引导句和公式之后的
变量释义段（"其中，..."），因为这些是自然语言文本。

---

## 四、封面信息表（不动）

特征：模板的第一个 Table（24 行 × 4 列），位于文档最开始。

**处理**：本 skill 处理的是正文段，根本不接触 Table 内容。

---

## 五、注意事项段（不动）

特征：封面之后、正文章节之前的 8 段，使用"缺省文本"样式，段首通常是
"交底书注意事项："。

**处理**：完全不动。

---

## 六、参数取值的具体数字（半保护）

特征：含有具体参数值的句子，如：
- `K 取 20`
- `本实施例取 30`
- `取值范围为 0.0001~0.001`
- `N=128`

**处理**：
- 不允许改动数值本身
- 不允许加入"约"、"大约"等模糊词
- 允许调整数值前后的句法结构

---

## 七、专利号引用（不动）

特征：`专利号为 CN[0-9]+` 或 `CN[0-9]+[A-Z]?` 格式的引用。

**处理**：不动专利号本身和它的引导句"专利号为 ... 的"。

---

## 八、技术术语本身（不动，由 Pass C 单独处理）

特征：从术语锁定表中读取的所有术语字符串。

**处理**：在 Pass A-B 的修改中，这些术语字符串必须**逐字保留**，不允许
被禁用词替换规则误伤。例如，如果某术语是"显著性梯度图"，包含"显著"二字，
但不应被"显著提升→提高"规则误伤。

实现方法：在执行词级替换前，先用占位符替换术语字符串，做完替换后再换回。

---

## 实现：保护区域检测函数

```python
import re
from typing import List, Tuple

# 章节标题的识别
HEADING_PATTERNS = [
    r'^[一二三四五六七]、',
    r'^发明目的$',
    r'^技术解决方案$',
    r'^3、技术效果',
]

# 公式特征
FORMULA_PATTERNS = [
    r'\$[^$]+\$',
    r'\$\$[^$]+\$\$',
    r'\\(?:frac|sum|int|mathbf|sigma|alpha|beta|gamma|theta|lambda|nabla)',
]

# 附图描述行
FIGURE_DESC_PATTERN = r'^图\s*\d+\s*[，,]?\s*为本发明'


def is_protected(paragraph_text: str, term_lock_terms: List[str] = None) -> Tuple[bool, str]:
    """
    判断段落是否受保护。
    返回 (是否受保护, 原因)
    """
    text = paragraph_text.strip()
    if not text:
        return True, '空段'

    # 法律声明
    for pattern in LEGAL_PREFIXES:
        if re.match(pattern, text):
            return True, f'法律声明段（匹配 {pattern}）'

    # 章节标题
    for pattern in HEADING_PATTERNS:
        if re.match(pattern, text):
            return True, f'章节标题段'

    # 公式段（含公式标记的段视为半保护）
    for pattern in FORMULA_PATTERNS:
        if re.search(pattern, text):
            return True, f'含公式（公式部分不动，引导句可改）'

    # 附图描述行
    if re.match(FIGURE_DESC_PATTERN, text):
        return True, f'附图描述行（半保护）'

    return False, ''


def mask_terms_for_replacement(text: str, terms: List[str]) -> Tuple[str, dict]:
    """
    在执行词级替换前，将术语锁定表中的术语用占位符替换，避免被误伤。
    返回 (替换后文本, 占位符映射)
    """
    mapping = {}
    masked = text
    # 按长度倒序，先处理长术语，避免子串冲突
    for i, term in enumerate(sorted(terms, key=len, reverse=True)):
        placeholder = f'__TERM_{i:04d}__'
        if term in masked:
            masked = masked.replace(term, placeholder)
            mapping[placeholder] = term
    return masked, mapping


def unmask_terms(text: str, mapping: dict) -> str:
    """将占位符还原为原术语"""
    for placeholder, term in mapping.items():
        text = text.replace(placeholder, term)
    return text
```

---

## 检查清单

执行任何修改前，对每个段落确认：

1. [ ] 不是章节标题段
2. [ ] 不是封面信息表内容
3. [ ] 不是注意事项段
4. [ ] 段中的公式部分不会被修改
5. [ ] 段中的具体参数数值不会被修改
6. [ ] 段中的专利号不会被修改
7. [ ] 段中的术语锁定项已用占位符屏蔽
8. [ ] 是附图描述行的话，仅允许标点修正
