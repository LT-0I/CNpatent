#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
param_segment.py — Rule 13 detector: "其中，" parameter segments polluted
with operation verbs, or brackets packing operation descriptions.

Per《专利文档AI味特征分析报告_v2》rule 13: parameter-explanation segments
led by "其中，" must only describe parameters ("X 为 Y" / "X 与 Y 分别为 ...").
Operation verbs (利用/将/使用/获得/由此/通过/根据/计算/执行/采用/引入/构建/
优化) and bracketed operation flows >15 chars violate the purity rule.

Category=critical (weight 8).
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List


ACTION_VERBS_RE = re.compile(
    r'(?:利用|将|使用|获得|由此|通过|根据|计算|执行|采用|引入|构建|优化|反投影|投影|同步|更新|校验|标定)'
)

PARAM_SEG_RE = re.compile(r'^其中[，,]')
BRACKET_RE = re.compile(r'[（(]([^（()）]{5,})[）)]')


def _allowed_param_sentence(sent: str) -> bool:
    """Heuristic: pure parameter sentences usually contain 为/是 and no action verb."""
    if ACTION_VERBS_RE.search(sent):
        return False
    if '为' in sent or '是' in sent or '分别为' in sent:
        return True
    return True


def detect(text: str, section: str = 'all') -> Dict:
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    flags_param_mixed: List[Dict] = []
    flags_bracket_leak: List[Dict] = []

    for idx, para in enumerate(paragraphs):
        if not PARAM_SEG_RE.match(para):
            continue

        sentences = [s.strip() for s in re.split(r'[。；]', para) if s.strip()]
        mixed_sentences = []
        for s in sentences:
            if ACTION_VERBS_RE.search(s) and not _allowed_param_sentence(s):
                mixed_sentences.append(s[:60])

        if mixed_sentences:
            flags_param_mixed.append({
                'category': 'critical',
                'pattern': 'param_mixed_with_action',
                'paragraph_index': idx,
                'weight': 8,
                'excerpt': para[:100],
                'action_sentences': mixed_sentences[:3],
                'count': len(mixed_sentences),
                'note': '"其中，" segment mixes parameter explanation with operation verbs',
            })

        for m in BRACKET_RE.finditer(para):
            inner = m.group(1)
            if len(inner) > 15 and ACTION_VERBS_RE.search(inner):
                flags_bracket_leak.append({
                    'category': 'critical',
                    'pattern': 'bracket_op_leak',
                    'paragraph_index': idx,
                    'weight': 8,
                    'bracket_content': inner[:60],
                    'bracket_length': len(inner),
                    'excerpt': para[:80],
                    'note': 'bracket inside parameter explanation contains operation flow >15 chars',
                })

    return {
        'flags_param_mixed': flags_param_mixed,
        'flags_bracket_leak': flags_bracket_leak,
    }


def main():
    parser = argparse.ArgumentParser(description='Parameter-segment purity detector (rule 13)')
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
