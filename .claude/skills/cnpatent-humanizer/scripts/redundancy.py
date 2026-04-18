#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
redundancy.py  —  H10 跨段语义复述检测

算法：bigram Jaccard similarity（纯 Python，零依赖）
  - 对每段提取字级 bigram 集合
  - 非相邻段对 sim ≥ 0.6 → flag
  - 单个段被 ≥3 其他段 sim ≥0.5 覆盖 → 权重 ×2

排除术语锁定 bigram，避免"都含专利核心术语"导致的假阳性。
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


CHINESE_RUN = re.compile(r'[\u4e00-\u9fa5]+')


def split_paragraphs(text: str):
    raw = re.split(r'\n\s*\n', text.strip())
    return [p.strip() for p in raw if p.strip()]


def bigrams(para: str, term_tokens=None):
    """Return bigram set for a paragraph, excluding term-lock tokens."""
    token_set = set(term_tokens or [])
    bset = set()
    for run in CHINESE_RUN.findall(para):
        # Skip term-lock tokens exact-match in run
        if run in token_set:
            continue
        for i in range(len(run) - 1):
            bg = run[i:i+2]
            if bg in token_set:
                continue
            bset.add(bg)
    return bset


def jaccard(a, b):
    if not a and not b:
        return 0.0
    inter = len(a & b)
    uni = len(a | b)
    return inter / uni if uni else 0.0


def detect(text: str, section: str = 'all', term_lock=None,
           sim_warn: float = 0.6, sim_over: float = 0.5):
    term_tokens = list(term_lock or [])
    paragraphs = split_paragraphs(text)
    # Skip headings / formulas
    filtered = [(i, p) for i, p in enumerate(paragraphs)
                if not (p.startswith('#') or p.startswith('$'))]
    bg_list = [(i, bigrams(p, term_tokens)) for i, p in filtered]

    flags = []
    overlap_counts = [0] * len(paragraphs)

    for idx1 in range(len(bg_list)):
        i1, b1 = bg_list[idx1]
        for idx2 in range(idx1 + 2, len(bg_list)):  # non-adjacent
            i2, b2 = bg_list[idx2]
            sim = jaccard(b1, b2)
            if sim >= sim_warn:
                flags.append({
                    'type': 'cross_para_redundancy',
                    'paragraph_pair': [i1, i2],
                    'jaccard': round(sim, 3),
                    'threshold': sim_warn,
                    'weight_factor': 1,
                })
            if sim >= sim_over:
                overlap_counts[i1] += 1
                overlap_counts[i2] += 1

    # Paragraphs covered by ≥3 others
    hub_flags = []
    for pi, cnt in enumerate(overlap_counts):
        if cnt >= 3:
            hub_flags.append({
                'type': 'redundancy_hub',
                'paragraph_index': pi,
                'overlap_count': cnt,
                'threshold': 3,
                'weight_factor': 2,
            })

    return {
        'section': section,
        'paragraphs_scanned': len(paragraphs),
        'flags_pairs': flags,
        'flags_hubs': hub_flags,
        'category': 'rhetorical',
        'base_weight': 6,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--section', default='all')
    parser.add_argument('--term-lock', default=None)
    parser.add_argument('--output', default=None)
    parser.add_argument('--sim-warn', type=float, default=0.6)
    args = parser.parse_args()

    text = Path(args.input).read_text(encoding='utf-8')
    term_lock = None
    if args.term_lock:
        data = json.loads(Path(args.term_lock).read_text(encoding='utf-8'))
        term_lock = list(data.keys()) if isinstance(data, dict) else data

    report = detect(text, section=args.section, term_lock=term_lock,
                    sim_warn=args.sim_warn)

    if args.output:
        Path(args.output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f'[OK] redundancy report: {args.output}')
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
