#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
term_pronoun.py — Rule 8 detector: in-paragraph long-term repetition without
pronoun substitution.

Per《专利文档AI味特征分析报告_v2》rule 8: terms >=6 characters appearing
twice or more within the same paragraph must use 该/上述/前述 + short form
on the second mention onward (while preserving cross-paragraph term lock).

Category=high (weight 4). Opt-in term_lock list suppresses auto-discovery.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional


PRONOUN_PREFIXES = ['该', '上述', '前述', '本', '所述']
MIN_TERM_LEN = 6
MIN_REPEAT = 2


def _auto_discover_terms(para: str) -> List[str]:
    """Extract candidate long Chinese terms (>=6 Hanzi) by connected-run scan."""
    seen_counts: Dict[str, int] = {}
    for m in re.finditer(r'[\u4e00-\u9fa5]{' + str(MIN_TERM_LEN) + ',}', para):
        term = m.group(0)
        seen_counts[term] = seen_counts.get(term, 0) + 1
    candidates: List[str] = []
    for term, c in seen_counts.items():
        if c >= MIN_REPEAT:
            candidates.append(term)
    return candidates


def _check_term_in_paragraph(term: str, para: str) -> Dict:
    occurrences = [m.start() for m in re.finditer(re.escape(term), para)]
    if len(occurrences) < MIN_REPEAT:
        return {'repeated': False}
    second_and_later = occurrences[1:]
    missing_pronoun_positions: List[int] = []
    for pos in second_and_later:
        window_start = max(0, pos - 4)
        window = para[window_start:pos]
        if any(pref in window for pref in PRONOUN_PREFIXES):
            continue
        missing_pronoun_positions.append(pos)
    return {
        'repeated': True,
        'total_occurrences': len(occurrences),
        'missing_pronoun_count': len(missing_pronoun_positions),
        'missing_positions': missing_pronoun_positions,
    }


def detect(text: str, section: str = 'all',
           term_lock: Optional[List[str]] = None) -> Dict:
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    flags: List[Dict] = []

    for idx, para in enumerate(paragraphs):
        if re.match(r'^[一二三四五六七]、', para):
            continue
        if len(para) < 40:
            continue

        if term_lock:
            candidates = [t for t in term_lock if len(t) >= MIN_TERM_LEN]
        else:
            candidates = _auto_discover_terms(para)

        for term in candidates:
            res = _check_term_in_paragraph(term, para)
            if res.get('repeated') and res.get('missing_pronoun_count', 0) >= 1:
                flags.append({
                    'category': 'high',
                    'pattern': 'term_repeat_no_pronoun',
                    'paragraph_index': idx,
                    'weight': 4,
                    'term': term,
                    'occurrences': res['total_occurrences'],
                    'missing_pronoun': res['missing_pronoun_count'],
                    'excerpt': para[:80],
                    'note': 'long term repeated in paragraph without 该/上述/前述 substitution',
                })

    return {'flags_term_repeat': flags}


def main():
    parser = argparse.ArgumentParser(description='In-paragraph term pronoun detector (rule 8)')
    parser.add_argument('--input', required=True)
    parser.add_argument('--section', default='all')
    parser.add_argument('--term-lock', default=None,
                        help='JSON file with term_lock list or dict')
    parser.add_argument('--output', default=None)
    args = parser.parse_args()

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    text = Path(args.input).read_text(encoding='utf-8')
    tl = None
    if args.term_lock:
        data = json.loads(Path(args.term_lock).read_text(encoding='utf-8'))
        tl = list(data.keys()) if isinstance(data, dict) else list(data)

    result = detect(text, section=args.section, term_lock=tl)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(payload, encoding='utf-8')
        print(f'flags saved to {args.output}')
    else:
        print(payload)


if __name__ == '__main__':
    main()
