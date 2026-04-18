#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
background_leak.py — Rule 6 detector: background problem description leaking
into §4b 技术解决方案 step bodies.

Per《专利文档AI味特征分析报告_v2》rule 6: 技术解决方案 should describe
operations only; 背景问题 (稀疏/延迟/含噪/缺乏/不足/失效/发散) belongs to
背景技术. Step bodies must not prepend multiple problem-description sentences.

Also enforces single-step ≤ 150 char soft limit in 4b / §6 innovation.
Category=critical (weight 8); double-sentence "X缺乏Y。为解决..." gets
weight_factor=1.5 (final 12).
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List


PROBLEM_PATTERNS = [
    r'缺乏(?=[\u4e00-\u9fa5])',
    r'不足(?=[\u4e00-\u9fa5]|[。，])',
    r'失效(?=[\u4e00-\u9fa5]|[。，])',
    r'受限于',
    r'不可行',
    r'发散(?=[\u4e00-\u9fa5]|[。，])',
    r'不充分',
    r'观测稀疏', r'观测延迟', r'观测含噪',
    r'容易[误漂偏失]',
    r'难以(?=[\u4e00-\u9fa5])',
    r'脱耦',
    r'时序错配',
]

DOUBLE_STRUCTURE = re.compile(
    r'([^。\n]{5,50})'
    r'(缺乏|不足|受限于|易受|发散|不可行|脱耦|难以)'
    r'([^。\n]{0,30})'
    r'[。；]\s*'
    r'(为(解决|此|解)|针对)'
)

SOLUTION_START_ANCHORS = ['技术解决方案', '2、技术解决方案']
SOLUTION_END_ANCHORS = ['技术效果', '3、技术效果', '五、', '五、附图']


def _in_section(i: int, paragraphs: List[str]) -> bool:
    started = False
    for j in range(i + 1):
        p = paragraphs[j]
        if any(a in p for a in SOLUTION_START_ANCHORS):
            started = True
        if any(a in p for a in SOLUTION_END_ANCHORS):
            started = False
    return started


def detect(text: str, section: str = 'all') -> Dict:
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    flags: List[Dict] = []

    if section not in ('四', 'all'):
        return {'flags_background_leak': flags}

    for idx, para in enumerate(paragraphs):
        if not _in_section(idx, paragraphs):
            continue
        if not re.match(r'^[（(]\s*\d+\s*[）)]', para):
            continue

        problem_hits = []
        for pat in PROBLEM_PATTERNS:
            for m in re.finditer(pat, para):
                problem_hits.append({'pattern': pat, 'matched': m.group(0)})

        double = DOUBLE_STRUCTURE.search(para)

        if double:
            flags.append({
                'category': 'critical',
                'pattern': 'double_problem_solution_lead',
                'paragraph_index': idx,
                'weight_factor': 1.5,
                'weight': 12,
                'excerpt': para[:80],
                'matched': double.group(0)[:60],
                'note': 'step body opens with "X缺乏Y。为解决..."',
            })
        elif problem_hits:
            flags.append({
                'category': 'critical',
                'pattern': 'background_leak',
                'paragraph_index': idx,
                'weight': 8,
                'excerpt': para[:80],
                'problem_matches': [h['matched'] for h in problem_hits[:5]],
                'count': len(problem_hits),
                'note': 'step body contains background-problem vocabulary',
            })

        if len(para) > 150:
            flags.append({
                'category': 'high',
                'pattern': 'step_too_long',
                'paragraph_index': idx,
                'weight': 4,
                'char_len': len(para),
                'excerpt': para[:60],
                'note': 'solution step exceeds 150 chars (innovation bodies cap)',
            })

    return {'flags_background_leak': flags}


def main():
    parser = argparse.ArgumentParser(description='Background leak detector (rule 6)')
    parser.add_argument('--input', required=True)
    parser.add_argument('--section', default='all')
    parser.add_argument('--output', default=None)
    args = parser.parse_args()

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    text = Path(args.input).read_text(encoding='utf-8')
    result = detect(text, section=args.section)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload, encoding='utf-8')
        print(f'flags saved to {args.output}')
    else:
        print(payload)


if __name__ == '__main__':
    main()
