#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
enumeration_check.py — Rule 3 detector: §4a/§4c sub-items without (数字)
numbering or without action-verb opening.

Per《专利文档AI味特征分析报告_v2》rule 3: 发明目的 / 技术效果 sub-items
must use 全角 (1)(2)(3) numbering and begin with an action verb
(提升/增强/降低/消除/实现/支持/获得/保障/解决/改善/提高/减少).

Violation category=critical (weight 8) for missing numbering; category=high
(weight 4) for non-action-verb opening.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List


ACTION_VERBS = [
    '提升', '增强', '降低', '消除', '实现', '支持', '获得', '保障',
    '解决', '改善', '提高', '减少', '打破', '简化',
]

FORBIDDEN_STARTERS = [
    '架构方面', '观测方面', '稳定性方面', '操作方面', '效果方面',
    '性能方面', '机制方面', '原理方面', '流程方面', '观测处理方面',
    '独立于', '对于', '针对', '架构上', '观测上', '稳定性上',
]

SECTION_ANCHORS = ['发明目的', '技术效果', '3、技术效果']
END_ANCHORS = ['技术解决方案', '2、技术解决方案', '五、', '六、']


def _is_enumeration_candidate(para: str) -> bool:
    if re.match(r'^[（(]\d+[）)]', para):
        return False
    if re.match(r'^[一二三四五六七]、', para):
        return False
    if '综上所述' in para or para.startswith('本发明提供') or para.startswith('本发明旨在'):
        return False
    for starter in FORBIDDEN_STARTERS:
        if para.startswith(starter):
            return True
    if re.match(r'^[^。，；\s]{2,8}方面[，,]', para):
        return True
    if re.match(r'^[^。，；\s]{2,8}上[，,]', para):
        return True
    return False


def _starts_with_numbered(para: str) -> bool:
    return bool(re.match(r'^[（(]\s*\d+\s*[）)]', para))


def _starts_with_action_verb(para: str) -> bool:
    numbered_match = re.match(r'^[（(]\s*\d+\s*[）)]\s*', para)
    body = para[numbered_match.end():] if numbered_match else para
    body = body.lstrip()
    return any(body.startswith(v) for v in ACTION_VERBS)


def detect(text: str, section: str = 'all') -> Dict:
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    flags: List[Dict] = []

    if section not in ('四', 'all'):
        return {'flags_enumeration': flags}

    scan_idx = None
    for i, p in enumerate(paragraphs):
        if any(anchor in p for anchor in SECTION_ANCHORS):
            scan_idx = i
            break
    if scan_idx is None:
        return {'flags_enumeration': flags}

    non_numbered_candidates: List[int] = []
    numbered_items: List[int] = []
    for i in range(scan_idx, len(paragraphs)):
        p = paragraphs[i]
        if any(end in p for end in END_ANCHORS):
            break
        if _starts_with_numbered(p):
            numbered_items.append(i)
            if not _starts_with_action_verb(p):
                flags.append({
                    'category': 'high',
                    'pattern': 'non_action_verb_start',
                    'paragraph_index': i,
                    'weight': 4,
                    'excerpt': p[:40],
                    'note': 'numbered item does not start with action verb',
                })
            continue
        if _is_enumeration_candidate(p):
            non_numbered_candidates.append(i)

    if len(non_numbered_candidates) >= 2 and len(numbered_items) == 0:
        flags.append({
            'category': 'critical',
            'pattern': 'missing_numbering',
            'paragraph_indices': non_numbered_candidates,
            'weight': 8,
            'count': len(non_numbered_candidates),
            'excerpt': paragraphs[non_numbered_candidates[0]][:40],
            'note': 'sub-items lack 全角 (数字) numbering',
        })

    return {'flags_enumeration': flags}


def main():
    parser = argparse.ArgumentParser(description='Enumeration numbering detector (rule 3)')
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
