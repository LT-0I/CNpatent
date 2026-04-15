#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CNpatent-humanizer regex cleanup script (Step 9 of the 9-step pipeline).

Hard-coded regex replacements as the final fallback. Compatible with
CNpatent's `final_deai_cleanup()` but adds patent-specific patches.

Use this AFTER the LLM has done semantic rewriting. This is a safety net,
not the main rewrite mechanism.

Usage:
    PYTHONUTF8=1 python -X utf8 regex_clean.py \\
        --input draft.txt \\
        --output cleaned.txt
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


# Protected legal-statement prefixes — paragraphs starting with these are
# left completely untouched.
PROTECTED_PREFIXES = [
    '为了更清楚地说明本发明实施例',
    '构成本申请的一部分的附图',
    '现详细说明本发明的多种示例性实施方式',
    '应理解本发明中所述的术语',
    '在不背离本发明的范围或精神',
    '关于本文中所使用的',
    '需要说明的是，在不冲突的情况下',
    '以上所述，仅为本申请较佳的具体实施方式',
]


# Replacement rules. Each entry is (regex_pattern, replacement, description).
# Order matters: longer patterns first to avoid sub-string conflicts.
REPLACEMENTS: List[Tuple[str, str, str]] = [
    # ────── 推销/夸大类 ──────
    (r'显著(?:提升|提高|改善)', '提高', '显著X→提高'),
    (r'大幅(?:提升|提高)', '提高', '大幅X→提高'),
    (r'大幅降低', '降低', '大幅降低→降低'),
    (r'极大(?:提升|提高)', '提高', '极大X→提高'),
    (r'(?:颠覆|革命|突破|划时代|开创)性(?:地|的)?', '', '颠覆性地/的→删'),
    (r'(?:巧妙|精妙|独创)(?:地|的)?', '', '巧妙地/的→删'),
    (r'(?:卓越|优异|出色)的', '较高的', '卓越的→较高的'),
    (r'高效地?', '', '高效地→删'),
    (r'精准地?', '', '精准地→删'),
    (r'具有广阔的应用前景', '', '广阔前景→删'),
    (r'意义深远', '', '意义深远→删'),
    (r'完美(?:解决|实现)', lambda m: m.group(0).replace('完美', ''), '完美X→X'),
    (r'创新性地', '', '创新性地→删'),

    # ────── 过渡填充词 ──────
    (r'值得注意的是[，,]?', '', '值得注意的是→删'),
    (r'需要(?:指出|强调|说明)的是[，,]?', '', '需要X的是→删'),
    (r'值得一提的是[，,]?', '', '值得一提→删'),
    (r'至关重要', '', '至关重要→删'),
    (r'尤为关键', '关键', '尤为关键→关键'),
    (r'(?<![\u4e00-\u9fa5])旨在', '用于', '旨在→用于'),
    (r'致力于', '', '致力于→删'),
    (r'得益于', '基于', '得益于→基于'),
    (r'(?:有)?鉴于此[，,]?', '', '鉴于此→删'),
    (r'综上所述[，,]?', '', '综上所述→删'),
    (r'总而言之[，,]?', '', '总而言之→删'),
    (r'^总之[，,]', '', '总之→删（仅段首）'),
    (r'毋庸置疑[，,]?', '', '毋庸置疑→删'),
    (r'不言而喻[，,]?', '', '不言而喻→删'),
    (r'在此基础上[，,]?', '', '在此基础上→删'),
    (r'从本质上讲[，,]?', '', '从本质上讲→删'),
    (r'从根本上说[，,]?', '', '从根本上说→删'),
    (r'充分利用', '利用', '充分利用→利用'),
    (r'充分考虑', '考虑', '充分考虑→考虑'),

    # ────── 排比连接词（仅段首） ──────
    (r'^首先[，,]?', '', '首先→删（仅段首）'),
    (r'^其次[，,]?', '', '其次→删（仅段首）'),
    (r'^然后[，,]?', '', '然后→删（仅段首）'),
    (r'^最后[，,]?', '', '最后→删（仅段首）'),
    (r'其一[，,]', '', '其一→删'),
    (r'其二[，,]', '', '其二→删'),
    (r'其三[，,]', '', '其三→删'),

    # ────── AI 高频结构 ──────
    (r'进一步地[，,]?', '', '进一步地→删'),
    (r'更为重要的是[，,]?', '', '更为重要的是→删'),
    (r'具体来说[，,]?', '', '具体来说→删'),
    (r'具体而言[，,]?', '', '具体而言→删'),
    (r'与此同时[，,]?', '', '与此同时→删'),
    (r'由此可以看出[，,]?', '', '由此可以看出→删'),
    (r'(?<![\u4e00-\u9fa5])事实上[，,]?', '', '事实上→删'),
    (r'(?<![\u4e00-\u9fa5])实际上[，,]?', '', '实际上→删'),
    (r'换言之[，,]?', '', '换言之→删'),
    (r'换句话说[，,]?', '', '换句话说→删'),
    (r'不难发现[，,]?', '', '不难发现→删'),
    (r'由此可见[，,]?', '', '由此可见→删'),

    # ────── 学术腔（注意：法律段已在段落级被保护，此处只做 lookahead 防误伤） ──────
    (r'本文(?!中所使用的)', '本发明', '本文→本发明（法律段已段级保护）'),
    (r'实验结果表明[，,]?', '', '实验结果表明→删'),
    (r'研究(?:发现|表明)[，,]?', '', '研究发现/表明→删'),
    (r'(?<![\u4e00-\u9fa5])我们提出', '本发明提供', '我们提出→本发明提供'),
    (r'(?<![\u4e00-\u9fa5])我们(?![\u4e00-\u9fa5]?(?:可以|能))', '本发明',
     '我们→本发明'),
    (r'(?<![\u4e00-\u9fa5])笔者', '', '笔者→删'),

    # ────── 中文独有：动词名词化 ──────
    (r'(?<![\u4e00-\u9fa5])进行预处理', '预处理', 'X化处理修正'),
    (r'(?<![\u4e00-\u9fa5])进行训练', '训练', 'X化处理修正'),
    (r'(?<![\u4e00-\u9fa5])进行(?:特征)?提取', '提取', 'X化处理修正'),
    (r'(?<![\u4e00-\u9fa5])进行(?:数据)?处理', '处理', 'X化处理修正'),
    (r'(?<![\u4e00-\u9fa5])做出判断', '判断', '做出判断→判断'),
    (r'(?<![\u4e00-\u9fa5])做出选择', '选择', '做出选择→选择'),
    (r'([\u4e00-\u9fa5])化处理', r'\1化', 'X化处理→X化'),

    # ────── 中英标点混用 ──────
    (r'([\u4e00-\u9fa5]),(?=\s|[\u4e00-\u9fa5])', r'\1，', '中英逗号混用'),
    (r'([\u4e00-\u9fa5]);(?=\s|[\u4e00-\u9fa5])', r'\1；', '中英分号混用'),
    (r'([\u4e00-\u9fa5]):(?=\s|[\u4e00-\u9fa5])', r'\1：', '中英冒号混用'),
    (r'([\u4e00-\u9fa5])\((?=[\u4e00-\u9fa5])', r'\1（', '中英括号混用'),
    (r'([\u4e00-\u9fa5])\)(?=\s|[\u4e00-\u9fa5]|$)', r'\1）', '中英括号混用'),

    # ────── 副词堆叠（保守） ──────
    (r'非常的?显著', '', '副词堆叠'),

    # ────── 比较级模糊（保守） ──────
    (r'(?<![\u4e00-\u9fa5])更(?:好|高|快|强|准)的(?=[\u4e00-\u9fa5])', '',
     '更X的→删（保守）'),
]


def is_protected_paragraph(paragraph: str) -> bool:
    """Check if paragraph starts with any protected legal prefix."""
    p = paragraph.strip()
    for prefix in PROTECTED_PREFIXES:
        if p.startswith(prefix):
            return True
    # Also protect heading paragraphs
    if re.match(r'^[一二三四五六七]、', p):
        return True
    if p in ('发明目的', '技术解决方案'):
        return True
    if re.match(r'^3、技术效果', p):
        return True
    # Protect formula paragraphs
    if re.search(r'\$[^$]+\$|\\frac|\\sum|\\int', p):
        return True
    # Protect figure description lines
    if re.match(r'^图\s*\d+\s*[，,]?\s*为本发明', p):
        return True
    return False


def clean_paragraph(text: str) -> Tuple[str, List[str]]:
    """Apply all regex replacements to a single paragraph."""
    applied = []
    cleaned = text
    for pattern, repl, desc in REPLACEMENTS:
        if re.search(pattern, cleaned):
            old = cleaned
            if callable(repl):
                cleaned = re.sub(pattern, repl, cleaned)
            else:
                cleaned = re.sub(pattern, repl, cleaned, flags=re.MULTILINE)
            if old != cleaned:
                applied.append(desc)

    # Cleanup: collapse multiple commas/spaces produced by deletions
    cleaned = re.sub(r'[，,]{2,}', '，', cleaned)
    cleaned = re.sub(r'^[，,。]+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'[，,]([。；！？])', r'\1', cleaned)
    cleaned = re.sub(r'[ \t]{2,}', ' ', cleaned)

    return cleaned, applied


def clean_text(text: str) -> Tuple[str, List[Tuple[int, str, List[str]]]]:
    """Clean entire text, paragraph by paragraph, respecting protections."""
    paragraphs = text.split('\n')
    output_paragraphs = []
    change_log = []

    for i, p in enumerate(paragraphs):
        if not p.strip():
            output_paragraphs.append(p)
            continue
        if is_protected_paragraph(p):
            output_paragraphs.append(p)
            continue
        cleaned, applied = clean_paragraph(p)
        output_paragraphs.append(cleaned)
        if applied:
            change_log.append((i, p[:30] + '...', applied))

    return '\n'.join(output_paragraphs), change_log


def main():
    parser = argparse.ArgumentParser(
        description='CNpatent-humanizer regex cleanup (Step 9)')
    parser.add_argument('--input', required=True, help='Input text file')
    parser.add_argument('--output', required=True, help='Output text file')
    parser.add_argument('--changelog', default=None,
                        help='Optional changelog file path')
    args = parser.parse_args()

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    text = Path(args.input).read_text(encoding='utf-8')
    cleaned, change_log = clean_text(text)
    Path(args.output).write_text(cleaned, encoding='utf-8')

    print(f'Cleaned text saved to {args.output}')
    print(f'Modified {len(change_log)} paragraphs')

    if args.changelog:
        log_lines = []
        for idx, preview, applied in change_log:
            log_lines.append(f'§{idx}: {preview}')
            for a in applied:
                log_lines.append(f'   - {a}')
        Path(args.changelog).write_text('\n'.join(log_lines), encoding='utf-8')
        print(f'Changelog saved to {args.changelog}')


if __name__ == '__main__':
    main()
