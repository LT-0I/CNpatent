#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
unprepared_concept.py — Rule 10 detector: concept introduced via
"X缺乏Y。为解决" without prior mention, or mechanical stepwise references.

Per《专利文档AI味特征分析报告_v2》rule 10:
  - If X is a new term never mentioned in prior 3 paragraphs, flag.
  - "步骤（X）与步骤（Y）输出的是 Z" pedantic cross-step reference flag.

Categories: rhetorical (weight 6) for unprepared; high (weight 4) for
stepwise-ref bridge.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List


LEAD_PATTERN = re.compile(
    r'^([^。；\n]{3,40})'
    r'(缺乏|不足|受限于|易受|发散|不可行|脱耦|难以)'
    r'([^。；\n]{0,30})'
    r'[。；]\s*'
    r'(为(解决|此|解)|针对)'
)

STEP_REF_PATTERN = re.compile(
    r'^步骤[（(]\s*\d+\s*[）)][^。\n]{0,20}与步骤[（(]\s*\d+\s*[）)]'
    r'[^。\n]{0,5}输出的是'
)


def _extract_concept_tokens(prefix: str) -> List[str]:
    chinese = re.findall(r'[\u4e00-\u9fa5]{3,10}', prefix)
    tokens: List[str] = []
    for s in chinese:
        if len(s) >= 4:
            tokens.append(s)
    return tokens[-3:] if tokens else chinese[:3]


def detect(text: str, section: str = 'all') -> Dict:
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    flags_unprepared: List[Dict] = []
    flags_step_ref: List[Dict] = []

    for idx, para in enumerate(paragraphs):
        m = LEAD_PATTERN.search(para)
        if m:
            prefix = m.group(1)
            concept_tokens = _extract_concept_tokens(prefix)
            if concept_tokens:
                prior_window = '\n'.join(paragraphs[max(0, idx - 3):idx])
                found = any(tok in prior_window for tok in concept_tokens)
                if not found:
                    flags_unprepared.append({
                        'category': 'rhetorical',
                        'pattern': 'unprepared_concept',
                        'paragraph_index': idx,
                        'weight_factor': 1,
                        'weight': 6,
                        'concept_tokens': concept_tokens,
                        'excerpt': para[:80],
                        'note': 'concept introduced via "X缺乏Y。为解决" with no prior mention in last 3 paragraphs',
                    })

        if STEP_REF_PATTERN.match(para):
            flags_step_ref.append({
                'category': 'high',
                'pattern': 'stepwise_ref_bridge',
                'paragraph_index': idx,
                'weight': 4,
                'excerpt': para[:80],
                'note': 'mechanical "步骤（X）与步骤（Y）输出的是 Z" bridge',
            })

    return {
        'flags_unprepared': flags_unprepared,
        'flags_step_ref': flags_step_ref,
    }


def main():
    parser = argparse.ArgumentParser(description='Unprepared-concept detector (rule 10)')
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
