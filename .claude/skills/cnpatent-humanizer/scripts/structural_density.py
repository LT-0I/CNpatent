#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
structural_density.py  —  H3 / H4 前置长定语 / 复合长名词短语检测

H3 前置超长定语：
  正则 `[^。；，,]{15,}的[\u4e00-\u9fa5]{2,6}`
  "的"前 ≥15 字且含动词/并列顿号 → 段内 ≥2 处 warn

H4 复合长名词短语：
  连续 ≥4 Chinese NN/NR token 无虚词（初阶用正则近似；要更准请外挂 jieba）
  近似规则：连续 ≥8 个汉字未出现 {的/之/与/和/及/并/或/其/本/该/所/了/着/过/在/被/把/按/以} 的 chunk

两者都排除术语锁定表中的条目。
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


FUNCTION_WORD = set(
    '的之与和及并或其本该所了着过在被把按以对于由从到自将为使令让等'
    # 常见动词/介词：避免把"相比X取得""方法做Y"等片段当 noun chunk
    '相比取得做是为有得到获得实现采用利用基于依据通过针对'
    '经过借助据根据按照依照对于关于涉及包括包含属于用于供'
    '可将以按做形成构成具有不无未非即若或则'
)
VERB_HINT = re.compile(r'[对于|由|经|按|基于|利用|通过|根据|沿|自]')
COORD_HINT = re.compile(r'[、，]')


def split_paragraphs(text: str):
    raw = re.split(r'\n\s*\n', text.strip())
    return [p.strip() for p in raw if p.strip()]


def contains_function(chunk: str) -> bool:
    return any(c in FUNCTION_WORD for c in chunk)


def detect_long_premod(paragraphs, term_set):
    """H3: 的-前堆叠定语 ≥15 字，段内 ≥2 处 flag."""
    flags = []
    for pi, para in enumerate(paragraphs):
        matches = []
        # Greedy scan for 的 anchored long prefix
        for m in re.finditer(r'([^。；\n]{15,})的[\u4e00-\u9fa5]{2,6}', para):
            prefix = m.group(1)
            # Must contain a verb hint or coordination mark to signal structural stack
            has_verb = bool(VERB_HINT.search(prefix))
            has_coord = bool(COORD_HINT.search(prefix))
            if not (has_verb or has_coord):
                continue
            # Exclude if match overlaps term-lock token
            if any(t in m.group(0) for t in term_set):
                continue
            matches.append({
                'prefix_len': len(prefix),
                'excerpt': m.group(0)[:50],
                'position': m.start(),
            })
        if len(matches) >= 2:
            flags.append({
                'type': 'long_premodifier',
                'paragraph_index': pi,
                'count_in_para': len(matches),
                'matches': matches,
                'weight_factor': 1,
            })
    return flags


def detect_noun_chunks(paragraphs, term_set):
    """H4: 连续 ≥8 个汉字无虚词 + 不含术语锁定条目 → compound noun chunk."""
    flags = []
    # Per paragraph: slide windows of pure Chinese chars with no function word
    for pi, para in enumerate(paragraphs):
        if not para.strip():
            continue
        # Keep only Chinese chars (replace non-Chinese with marker to break chunks)
        segmented = re.sub(r'[^\u4e00-\u9fa5]', '|', para)
        # Split on marker and on function words
        fw_re = '[' + ''.join(re.escape(c) for c in FUNCTION_WORD) + ']'
        parts = re.split(fw_re + r'|\|', segmented)
        for part in parts:
            if not part:
                continue
            if len(part) < 12:  # raised from 8 to suppress FP on technical terms
                continue
            if any(t in part for t in term_set):
                continue
            flags.append({
                'type': 'compound_noun_chunk',
                'paragraph_index': pi,
                'chunk': part,
                'length': len(part),
                'weight_factor': 1,
            })
    return flags


def detect(text: str, section: str = 'all', term_lock=None):
    term_set = set(term_lock or [])
    paragraphs = split_paragraphs(text)
    return {
        'section': section,
        'paragraphs_scanned': len(paragraphs),
        'flags_long_premodifier': detect_long_premod(paragraphs, term_set),
        'flags_compound_noun_chunk': detect_noun_chunks(paragraphs, term_set),
        'category': 'sentential',
        'base_weight': 3,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--section', default='all')
    parser.add_argument('--term-lock', default=None)
    parser.add_argument('--output', default=None)
    args = parser.parse_args()

    text = Path(args.input).read_text(encoding='utf-8')
    term_lock = None
    if args.term_lock:
        term_data = json.loads(Path(args.term_lock).read_text(encoding='utf-8'))
        term_lock = list(term_data.keys()) if isinstance(term_data, dict) else term_data

    report = detect(text, section=args.section, term_lock=term_lock)

    if args.output:
        Path(args.output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f'[OK] structural_density report: {args.output}')
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
