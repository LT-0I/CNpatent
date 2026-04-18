#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
merge_short.py — Over-correction side-effect detector: successive short
sentences that should be merged to restore natural flow.

Per《专利文档AI味特征分析报告_v2》第四部分 "过度修复副作用":
  - "动词1 X。[动词2|获得|得到] Y。" continuation pairs with len(S1)<20 &
    len(S2)<15 & S2 starts with 获得|得到|由此|据此|再|进而|从而 should
    be merged with a comma into "动词1 X，动词2 Y。"
  - Paragraphs with >=3 consecutive sub-20 char sentences flag
    "over_segmented_paragraph".

Category=style (weight 1.5). Output merge suggestions for LLM /
regex_clean downstream use.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List


CONTINUATION_STARTERS = ['获得', '得到', '由此', '据此', '再', '进而', '从而', '经此', '借此']
SHORT_1 = 20
SHORT_2 = 15


def _split_sentences(para: str) -> List[str]:
    return [s.strip() for s in re.split(r'([。！？])', para)]


def _paragraph_sentences(para: str) -> List[Dict]:
    parts = re.split(r'([。！？])', para)
    sents: List[Dict] = []
    buf = ''
    for token in parts:
        if token in '。！？':
            if buf.strip():
                sents.append({'text': buf.strip(), 'len': len(buf.strip()),
                              'end': token})
            buf = ''
        else:
            buf += token
    return sents


def _overlap_tail_head(s1: str, s2: str) -> bool:
    tail = re.findall(r'[\u4e00-\u9fa5]', s1)[-3:]
    head = re.findall(r'[\u4e00-\u9fa5]', s2)[:3]
    if not tail or not head:
        return False
    return any(ch in head for ch in tail)


def detect(text: str, section: str = 'all') -> Dict:
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    flags_merge_pair: List[Dict] = []
    flags_over_segmented: List[Dict] = []

    for idx, para in enumerate(paragraphs):
        if re.match(r'^[一二三四五六七]、', para):
            continue
        if re.search(r'\$[^$]+\$', para):
            continue

        sents = _paragraph_sentences(para)
        if len(sents) < 2:
            continue

        short_run_max = 0
        current_run = 0
        for s in sents:
            if s['len'] < 20:
                current_run += 1
                short_run_max = max(short_run_max, current_run)
            else:
                current_run = 0
        if short_run_max >= 3:
            flags_over_segmented.append({
                'category': 'style',
                'pattern': 'over_segmented_paragraph',
                'paragraph_index': idx,
                'weight': 1.5,
                'short_run': short_run_max,
                'excerpt': para[:80],
                'note': 'paragraph has >=3 consecutive sub-20 char sentences',
            })

        for i in range(len(sents) - 1):
            s1, s2 = sents[i], sents[i + 1]
            if s1['len'] >= SHORT_1 or s2['len'] >= SHORT_2:
                continue
            starter_hit = any(s2['text'].startswith(st) for st in CONTINUATION_STARTERS)
            overlap = _overlap_tail_head(s1['text'], s2['text'])
            if starter_hit or overlap:
                merged = f"{s1['text']}，{s2['text']}{s2['end']}"
                flags_merge_pair.append({
                    'category': 'style',
                    'pattern': 'mergable_short_pair',
                    'paragraph_index': idx,
                    'sentence_offset': i,
                    'weight': 1.5,
                    's1': s1['text'],
                    's2': s2['text'],
                    's1_len': s1['len'],
                    's2_len': s2['len'],
                    'starter_hit': starter_hit,
                    'overlap': overlap,
                    'merge_suggestion': merged,
                    'note': 'continuation pair; merge restores natural flow',
                })

    return {
        'flags_merge_pair': flags_merge_pair,
        'flags_over_segmented': flags_over_segmented,
    }


def main():
    parser = argparse.ArgumentParser(description='Short-sentence merge detector (over-correction guard)')
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
