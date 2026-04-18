#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patent_boilerplate.py  —  H6/H7/H8/H12 八股/引号生造/被动书面化/末段陈词

H6 发明八股句 (Tier 1.6, 10 句)
H7 引号包裹生造概念
H8 被动书面化 (由...予以/施加 / 对...施加)
H12 末段总结陈词

每项命中一处即 flag，权重由 audit 层决定。
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


CHINESE_CHAR = re.compile(r'[\u4e00-\u9fa5]')


# ---- H6 发明八股 (Tier 1.6) ----
BOILERPLATE_PATTERNS = [
    (r'本发明的目的是提供', 'boilerplate_purpose_decl'),
    (r'本发明的优势体现', 'boilerplate_advantage_list'),
    (r'本发明提供.{0,20}相比现有技术具有', 'boilerplate_vs_prior_art'),
    (r'本方法.{0,15}相比现有技术', 'boilerplate_method_vs_prior'),
    (r'本步骤.{0,10}核心技术创新', 'boilerplate_core_claim'),
    (r'本方案.{0,10}必要性', 'boilerplate_necessity'),
    (r'本方案.{0,10}收敛性', 'boilerplate_convergence'),
    (r'本方案.{0,10}效果.{0,10}(?:佐证|支撑|证明)', 'boilerplate_evidence'),
    (r'本发明的技术效果为', 'boilerplate_effect_decl'),
    (r'综上所述.{0,20}本发明', 'boilerplate_summary'),
]

# ---- H8 被动书面化 ----
PASSIVE_PATTERNS = [
    (r'由[\u4e00-\u9fa5]{1,15}(?:予以|加以)', 'passive_yi_1'),
    (r'对[\u4e00-\u9fa5]{1,15}施加', 'passive_yi_2'),
    (r'以[\u4e00-\u9fa5]{0,10}方式对[\u4e00-\u9fa5]{0,15}施加', 'passive_yi_3'),
    (r'由[\u4e00-\u9fa5]{0,10}约束', 'passive_yi_4'),
    (r'由[\u4e00-\u9fa5]{0,8}(?:控制|限制|决定)', 'passive_yi_5'),
]

# ---- H12 末段总结陈词 ----
END_SUMMARY_HEAD = re.compile(r'^(由此|通过|综上|因此)')
END_SUMMARY_TAIL = re.compile(
    r'本(?:发明|方法).{0,30}(?:能力|要求|支撑|实现|满足)'
)


def count_cn(text: str) -> int:
    return len(CHINESE_CHAR.findall(text))


def split_paragraphs(text: str):
    raw = re.split(r'\n\s*\n', text.strip())
    return [p.strip() for p in raw if p.strip()]


def detect_boilerplate(text: str):
    flags = []
    for pattern, name in BOILERPLATE_PATTERNS:
        for m in re.finditer(pattern, text):
            flags.append({
                'type': 'boilerplate',
                'subtype': name,
                'pattern': pattern,
                'position': m.start(),
                'excerpt': m.group(0)[:40],
            })
    return flags


def detect_quote_coinage(text: str, term_lock=None):
    """Detect 「X」 or "X" wrappers around non-lexicon phrases (H7)."""
    term_set = set(term_lock or [])
    flags = []
    # Curly / angle / straight double quotes containing short Chinese phrase
    for m in re.finditer(r'[「「""]([\u4e00-\u9fa5]{2,12})[」」""]', text):
        phrase = m.group(1)
        if phrase in term_set:
            continue
        flags.append({
            'type': 'quote_coinage',
            'phrase': phrase,
            'position': m.start(),
            'excerpt': m.group(0),
        })
    return flags


def detect_passive_written(text: str):
    flags = []
    for pattern, name in PASSIVE_PATTERNS:
        for m in re.finditer(pattern, text):
            flags.append({
                'type': 'passive_written',
                'subtype': name,
                'position': m.start(),
                'excerpt': m.group(0),
            })
    return flags


def detect_end_summary(text: str):
    paragraphs = split_paragraphs(text)
    flags = []
    for pi, para in enumerate(paragraphs):
        if not para or para.startswith('#') or para.startswith('$'):
            continue
        if not END_SUMMARY_HEAD.search(para):
            continue
        if END_SUMMARY_TAIL.search(para):
            flags.append({
                'type': 'end_summary_cliche',
                'paragraph_index': pi,
                'excerpt': para[:60] + ('…' if len(para) > 60 else ''),
            })
    return flags


def detect(text: str, section: str = 'all', term_lock=None):
    return {
        'section': section,
        'flags_boilerplate': detect_boilerplate(text),
        'flags_quote_coinage': detect_quote_coinage(text, term_lock),
        'flags_passive_written': detect_passive_written(text),
        'flags_end_summary': detect_end_summary(text),
        'category': 'rhetorical',
        'base_weight': 6,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--section', default='all')
    parser.add_argument('--term-lock', default=None,
                        help='Path to JSON term-lock list')
    parser.add_argument('--output', default=None)
    args = parser.parse_args()

    text = Path(args.input).read_text(encoding='utf-8')
    term_lock = None
    if args.term_lock:
        term_data = json.loads(Path(args.term_lock).read_text(encoding='utf-8'))
        if isinstance(term_data, list):
            term_lock = term_data
        elif isinstance(term_data, dict):
            term_lock = list(term_data.keys())

    report = detect(text, section=args.section, term_lock=term_lock)

    if args.output:
        Path(args.output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f'[OK] patent_boilerplate report: {args.output}')
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
