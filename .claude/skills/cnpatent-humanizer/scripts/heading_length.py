#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
heading_length.py  —  H18 编号分点总起句字数检测

Detector for the user's explicit rule (v1.4 patch):
    每个编号分点的总起句（（N）后的标题/概述句）字数必须 < 10。
    例："（4）病害目标检测与几何先验驱动的误检抑制" (17字) → BAD
        "（4）病害检测误检抑制" (8字) → GOOD

算法：
1. 按段落扫描，匹配 ^[（(]\\d+[)）]
2. 截取到第一个句号/分号/逗号/换行的那段作为"总起句"
3. 计字数（仅中文字符，跳过英文数字符号）
4. ≥10 字 → flag；≥15 字 → 权重 ×2

Output JSON: {"headings": [...], "flags": [...]}
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


HEADING_RE = re.compile(r'^[（(](\d+)[)）]\s*([^\n]+)')
STOP_CHARS = re.compile(r'[。；;，,：:]')
CHINESE_CHAR = re.compile(r'[\u4e00-\u9fa5]')


def count_chinese(text: str) -> int:
    """Count Chinese characters in the text (primary metric for length)."""
    return len(CHINESE_CHAR.findall(text))


def extract_headings(text: str):
    """Yield (line_no, number, heading_text) for each numbered bullet."""
    for i, line in enumerate(text.splitlines(), start=1):
        m = HEADING_RE.match(line.strip())
        if not m:
            continue
        number = m.group(1)
        tail = m.group(2)
        stop = STOP_CHARS.search(tail)
        heading = tail[:stop.start()] if stop else tail
        heading = heading.strip()
        yield i, number, heading


def detect(text: str, section: str = 'all', limit: int = 10):
    headings = list(extract_headings(text))
    flags = []
    for line_no, number, heading in headings:
        length = count_chinese(heading)
        if length >= limit:
            weight_factor = 2 if length >= limit + 5 else 1
            flags.append({
                'type': 'heading_too_long',
                'number': number,
                'heading': heading,
                'length_cn': length,
                'line': line_no,
                'threshold': limit,
                'weight_factor': weight_factor,
                'excerpt': heading[:40] + ('…' if len(heading) > 40 else ''),
            })
    return {
        'section': section,
        'headings_scanned': len(headings),
        'flags': flags,
        'category': 'sentential',
        'base_weight': 6,
    }


def main():
    parser = argparse.ArgumentParser(
        description='Detect numbered-bullet headings whose topic sentence >=10 Chinese chars.'
    )
    parser.add_argument('--input', required=True, help='Input markdown file')
    parser.add_argument('--section', default='all',
                        help='Section context (三/四/五/六/all)')
    parser.add_argument('--limit', type=int, default=10,
                        help='Char limit (default 10)')
    parser.add_argument('--output', default=None, help='Output JSON path')
    args = parser.parse_args()

    text = Path(args.input).read_text(encoding='utf-8')
    report = detect(text, section=args.section, limit=args.limit)

    if args.output:
        Path(args.output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f'[OK] heading_length report: {args.output}')
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
