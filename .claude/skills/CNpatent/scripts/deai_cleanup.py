"""
Final deterministic anti-AI cleanup pass.

Why this file exists:
    The Reviewer agent does the heavy lifting on AI-detection (semantic
    review, sentence-structure analysis, calling CNpatent-humanizer skill). But
    the Reviewer is an LLM, so any single miss leaves an AI-flavoured
    word in the final docx. This module is the *deterministic safety
    net*: pure regex, no AI judgement, run unconditionally just before
    DOCX serialisation.

    Use it at the end of Phase 3, after all Reviewer rounds have settled.

Usage from Phase 3:

    import sys
    from pathlib import Path

    skill_root = Path.cwd() / '.claude' / 'skills' / 'CNpatent'
    if not skill_root.exists():
        skill_root = Path.home() / '.claude' / 'skills' / 'CNpatent'
    sys.path.insert(0, str(skill_root / 'scripts'))

    from deai_cleanup import final_deai_cleanup

    cleaned = final_deai_cleanup(merged_text)
    # write `cleaned` into the DOCX

The replacement table is curated against high-frequency AI markers
identified across multiple patent disclosure samples. See
references/writing-rules.md (`Anti-AI Vocabulary Replacement Table`)
for the human-readable categorisation and rationale behind each entry.
"""

from __future__ import annotations

import re


# Format: (regex pattern, replacement string).
# Categories follow writing-rules.md's "六大类禁用词" structure.
REPLACEMENTS = [
    # ── 一、推销/夸大类 ──
    (r'显著(?:提升|提高|改善)', '提高'),
    (r'(?:颠覆|革命|突破)性的?', ''),
    (r'(?:巧妙|精妙|独特|独创)的?地?', ''),
    (r'具有广阔的应用前景', ''),
    (r'意义深远', ''),
    (r'(?:卓越|优异|出色)的', '较高的'),

    # ── 二、AI 高频过渡/填充词 ──
    (r'值得注意的是[，,]?', ''),
    (r'需要指出的是[，,]?', ''),
    (r'需要强调的是[，,]?', ''),
    (r'至关重要', ''),
    (r'毋庸置疑[，,]?', ''),
    (r'不言而喻[，,]?', ''),
    (r'从本质上讲[，,]?', ''),
    (r'从根本上说[，,]?', ''),

    # ── 六、AI 高频结构模式 ──
    (r'进一步地[，,]?', ''),
    (r'更为重要的是[，,]?', ''),
    (r'值得一提的是[，,]?', ''),
    (r'具体来说[，,]?', ''),
    (r'具体而言[，,]?', ''),
    (r'与此同时[，,]?', ''),
    (r'由此可以看出[，,]?', ''),
    (r'事实上[，,]?', ''),
    (r'实际上[，,]?', ''),
    (r'换言之[，,]?', ''),

    # ── 五、学术/论文腔 ──
    # NOTE the negative lookahead: the legal boilerplate inside 具体实施方式
    # contains "本文中所使用的「包含」「包括」..." — that exact 本文 must NOT
    # be rewritten. A simple `(?!中所使用的)` is enough; Python 3.13+ rejects
    # variable-width lookbehinds so we don't use them here.
    (r'本文(?!中所使用的)', '本发明'),
    (r'实验结果表明[，,]?', ''),
    (r'研究(?:发现|表明)[，,]?', ''),
]


def _strip_perfect(m):
    """Callable replacement: strip 完美 prefix from 完美解决/完美实现."""
    return m.group(0).replace('完美', '')


# Patterns whose replacement is a function, not a string.
LAMBDA_REPLACEMENTS = [
    (r'(?:完美)(?:解决|实现)', _strip_perfect),
]


def final_deai_cleanup(text):
    """Apply all regex replacements + clean up stray punctuation left behind.

    Pure-rule, no AI judgement. Safe to run unconditionally as the final
    pass before DOCX write.
    """
    for pattern, repl in REPLACEMENTS:
        text = re.sub(pattern, repl, text)
    for pattern, repl in LAMBDA_REPLACEMENTS:
        text = re.sub(pattern, repl, text)

    # Cleanup of consecutive Chinese commas left behind by deletions
    text = re.sub(r'[，,]{2,}', '，', text)
    # Strip leading commas left at line starts after deletions
    text = re.sub(r'^\s*[，,]', '', text, flags=re.MULTILINE)
    return text
