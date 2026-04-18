#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
triple_pattern.py  —  H5 三元并列与跨段重现检测

检测两类：
  (a) A、B、C 三元短语本身（A/B/C 每项 2-6 字）
  (b) 同一三元在 ≥3 段重复出现 → flag；≥5 段 → 权重 ×2

典型命中：
  "稀疏、延迟、含噪" 在多个段落反复出现
  "观测稀疏、观测延迟、观测质量差" 等同变体

还检测"三类/三种/三重/三层"等"三元提示词"密度。
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


# A、B、C where A/B/C are 2-6 Chinese chars
TRIPLE_RE = re.compile(
    r'([\u4e00-\u9fa5]{2,6})[、，]([\u4e00-\u9fa5]{2,6})[、，]([\u4e00-\u9fa5]{2,6})'
)

TRIPLE_HINT_RE = re.compile(r'(三[类种重层]|三元|三段|三方)')


def split_paragraphs(text: str):
    raw = re.split(r'\n\s*\n', text.strip())
    return [p.strip() for p in raw if p.strip()]


def extract_triples(paragraph: str):
    """Return list of (a, b, c) tuples from a paragraph."""
    return [(m.group(1), m.group(2), m.group(3))
            for m in TRIPLE_RE.finditer(paragraph)]


def detect(text: str, section: str = 'all'):
    paragraphs = split_paragraphs(text)
    triple_to_paras = defaultdict(set)  # (a,b,c) -> set of paragraph indices
    para_triples = []

    for pi, para in enumerate(paragraphs):
        triples = extract_triples(para)
        para_triples.append(triples)
        for tr in triples:
            triple_to_paras[tr].add(pi)

    flags_cross_para = []
    for triple, pset in triple_to_paras.items():
        if len(pset) >= 5:
            flags_cross_para.append({
                'type': 'triple_cross_paragraph',
                'triple': list(triple),
                'paragraph_indices': sorted(pset),
                'count': len(pset),
                'weight_factor': 2,
            })
        elif len(pset) >= 3:
            flags_cross_para.append({
                'type': 'triple_cross_paragraph',
                'triple': list(triple),
                'paragraph_indices': sorted(pset),
                'count': len(pset),
                'weight_factor': 1,
            })

    # Hint-word density (三类/三种/三重/三层)
    hint_count = len(TRIPLE_HINT_RE.findall(text))
    flags_hint = []
    if hint_count >= 6:
        flags_hint.append({
            'type': 'triple_hint_dense',
            'count': hint_count,
            'threshold': 6,
            'weight_factor': 1,
        })
    if hint_count >= 10:
        flags_hint[-1]['weight_factor'] = 2

    return {
        'section': section,
        'paragraphs_scanned': len(paragraphs),
        'triples_unique': len(triple_to_paras),
        'flags_cross_paragraph': flags_cross_para,
        'flags_hint_dense': flags_hint,
        'category': 'rhetorical',
        'base_weight': 6,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--section', default='all')
    parser.add_argument('--output', default=None)
    args = parser.parse_args()

    text = Path(args.input).read_text(encoding='utf-8')
    report = detect(text, section=args.section)

    if args.output:
        Path(args.output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f'[OK] triple_pattern report: {args.output}')
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
