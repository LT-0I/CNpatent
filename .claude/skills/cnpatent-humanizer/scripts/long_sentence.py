#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
long_sentence.py  —  H1/H16/H17 句长 / 段长 / 分号密度检测

H1 单句超长（>80 字 warn; >120 字 ×2）
H16 超长段（>200 字 warn; >300 字 ×2）
H17 段内分号过密（≥3 warn; ≥5 ×2；>200字 且 ≥4 → 权重 ×3）

算法：
- 句切分：中文句号/问号/叹号/分号作边界（分号按硬切分避免漏报）
- 段切分：空行分隔，或 markdown paragraph
- 字数：中文字符
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
SENT_END = re.compile(r'[。？！]')
SEMICOLON = re.compile(r'[；;]')


def count_cn(text: str) -> int:
    return len(CHINESE_CHAR.findall(text))


def split_paragraphs(text: str):
    raw = re.split(r'\n\s*\n', text.strip())
    return [p.strip() for p in raw if p.strip()]


def split_sentences(paragraph: str):
    """Split by sentence-ending punctuation. Semicolons are NOT treated as
    sentence boundaries here so we can count them separately."""
    parts = re.split(r'[。？！]', paragraph)
    return [s.strip() for s in parts if s.strip()]


def detect(text: str, section: str = 'all',
           sentence_warn: int = 80, sentence_crit: int = 120,
           para_warn: int = 200, para_crit: int = 300,
           semi_warn: int = 3, semi_crit: int = 5):
    paragraphs = split_paragraphs(text)
    flags_sent, flags_para, flags_semi = [], [], []

    # §6 numbered substeps (^（N）) halve sentence-length weight
    is_sec6 = section == '六' or section == 'six'

    for pi, para in enumerate(paragraphs):
        # Skip pure formula / heading lines
        if para.startswith('#') or para.startswith('$'):
            continue

        para_cn = count_cn(para)
        semi_count = len(SEMICOLON.findall(para))

        # H16/H17 paragraph-level
        if para_cn >= para_crit:
            flags_para.append({
                'type': 'paragraph_too_long',
                'paragraph_index': pi,
                'length_cn': para_cn,
                'threshold': para_crit,
                'weight_factor': 2,
                'excerpt': para[:50] + '…',
            })
        elif para_cn >= para_warn:
            wf = 3 if semi_count >= 4 else 1
            flags_para.append({
                'type': 'paragraph_too_long',
                'paragraph_index': pi,
                'length_cn': para_cn,
                'threshold': para_warn,
                'weight_factor': wf,
                'excerpt': para[:50] + '…',
                'semicolon_count': semi_count,
            })

        # H17 semicolon density (independent of paragraph length)
        if semi_count >= semi_crit:
            flags_semi.append({
                'type': 'semicolon_dense',
                'paragraph_index': pi,
                'count': semi_count,
                'threshold': semi_crit,
                'weight_factor': 2,
                'excerpt': para[:50] + '…',
            })
        elif semi_count >= semi_warn:
            flags_semi.append({
                'type': 'semicolon_dense',
                'paragraph_index': pi,
                'count': semi_count,
                'threshold': semi_warn,
                'weight_factor': 1,
                'excerpt': para[:50] + '…',
            })

        # H1 sentence-level (inside the paragraph)
        for si, sent in enumerate(split_sentences(para)):
            s_cn = count_cn(sent)
            if s_cn >= sentence_crit:
                flags_sent.append({
                    'type': 'sentence_too_long',
                    'paragraph_index': pi,
                    'sentence_index': si,
                    'length_cn': s_cn,
                    'threshold': sentence_crit,
                    'weight_factor': 1 if is_sec6 else 2,
                    'excerpt': sent[:50] + '…',
                })
            elif s_cn >= sentence_warn:
                flags_sent.append({
                    'type': 'sentence_too_long',
                    'paragraph_index': pi,
                    'sentence_index': si,
                    'length_cn': s_cn,
                    'threshold': sentence_warn,
                    'weight_factor': 0.5 if is_sec6 else 1,
                    'excerpt': sent[:50] + '…',
                })

    return {
        'section': section,
        'paragraphs_scanned': len(paragraphs),
        'flags_sentence': flags_sent,
        'flags_paragraph': flags_para,
        'flags_semicolon': flags_semi,
        'category': 'sentential',
        'base_weight': 3,
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
        print(f'[OK] long_sentence report: {args.output}')
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
