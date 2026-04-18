#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
topic_switch.py — Rule 2 detector: multi-topic-switch marker in one paragraph.

Per《专利文档AI味特征分析报告_v2》rule 2: paragraphs containing >=2 topic
switch markers ("架构上，"/"X方面，"/"X层面"/"X角度"/"X维度") without
paragraph breaks, or long paragraphs (>250 chars) carrying >=1 such marker,
must be split.

Category: rhetorical (weight 6). Long-segment hit: weight_factor=1.5 (final 9).
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List


TOPIC_SWITCH_PATTERNS = [
    r'架构上(?=[，,])', r'观测上(?=[，,])', r'稳定性上(?=[，,])',
    r'操作上(?=[，,])', r'效果上(?=[，,])', r'性能上(?=[，,])',
    r'机制上(?=[，,])', r'原理上(?=[，,])', r'流程上(?=[，,])',
    r'架构方面', r'观测方面', r'稳定性方面', r'操作方面',
    r'效果方面', r'性能方面', r'机制方面', r'原理方面', r'流程方面',
    r'观测处理方面', r'观测与退化层面',
    r'[\u4e00-\u9fa5]{2,4}层面(?=[，,])',
    r'[\u4e00-\u9fa5]{2,4}角度(?=[，,])',
    r'[\u4e00-\u9fa5]{2,4}维度(?=[，,])',
]


def _scan_markers(para: str) -> List[Dict]:
    hits = []
    for pat in TOPIC_SWITCH_PATTERNS:
        for m in re.finditer(pat, para):
            hits.append({'pattern': pat, 'matched': m.group(0),
                         'position': m.start()})
    return hits


def detect(text: str, section: str = 'all') -> Dict:
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    flags_topic_switch: List[Dict] = []
    flags_long_switch: List[Dict] = []

    for idx, para in enumerate(paragraphs):
        if re.match(r'^[一二三四五六七]、', para):
            continue
        if re.search(r'\$[^$]+\$', para):
            continue

        hits = _scan_markers(para)
        distinct_count = len({h['matched'] for h in hits})

        if distinct_count >= 2:
            flags_topic_switch.append({
                'category': 'rhetorical',
                'pattern': 'topic_switch_multi',
                'paragraph_index': idx,
                'weight_factor': 1,
                'weight': 6,
                'excerpt': para[:60],
                'markers': [h['matched'] for h in hits],
                'note': 'paragraph contains >=2 topic-switch markers; force split',
            })
        if distinct_count >= 1 and len(para) > 250:
            flags_long_switch.append({
                'category': 'rhetorical',
                'pattern': 'long_segment_with_switch',
                'paragraph_index': idx,
                'weight_factor': 1.5,
                'weight': 9,
                'excerpt': para[:60],
                'markers': [h['matched'] for h in hits],
                'char_len': len(para),
                'note': 'long paragraph (>250 chars) with topic-switch marker',
            })

    return {
        'flags_topic_switch': flags_topic_switch,
        'flags_long_switch': flags_long_switch,
    }


def main():
    parser = argparse.ArgumentParser(description='Topic-switch marker detector (rule 2)')
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
