#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CNpatent-humanizer burstiness analysis script.

Computes sentence-length burstiness (CV = std/mean) for Chinese patent text.
Low burstiness (CV < 0.15) is a strong AI tell — humans naturally vary
sentence length, AI tends to produce uniform-length sentences.

Based on GPTZero's burstiness concept, adapted for Chinese text using
Chinese sentence-end punctuation (。；！？).

Usage:
    PYTHONUTF8=1 python -X utf8 burstiness.py \\
        --input draft.txt \\
        --section 六 \\
        --window 4
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Optional


# Section-specific CV thresholds (lower = more strict)
# Patent's 具体实施方式 naturally has long compound sentences,
# so we use a lower threshold there.
SECTION_THRESHOLDS = {
    '一': 0.15,
    '二': 0.15,
    '三': 0.18,  # 背景技术 should have varied rhythm
    '四': 0.15,  # 发明内容
    '五': 0.20,  # 附图说明 (each line is similar by design)
    '六': 0.12,  # 具体实施方式 (long sentences are normal)
    'all': 0.15,
}


# Skip these legal-statement sentences when computing burstiness
LEGAL_SENTENCE_FRAGMENTS = [
    '为了更清楚地说明本发明实施例',
    '构成本申请的一部分的附图',
    '现详细说明本发明的多种示例性实施方式',
    '应理解本发明中所述的术语',
    '在不背离本发明的范围或精神',
    '关于本文中所使用的',
    '需要说明的是，在不冲突的情况下',
    '以上所述，仅为本申请较佳的具体实施方式',
]


def is_legal_sentence(sentence: str) -> bool:
    """Check if a sentence is part of a legal-statement section."""
    s = sentence.strip()
    for fragment in LEGAL_SENTENCE_FRAGMENTS:
        if fragment in s:
            return True
    return False


def split_sentences(text: str) -> List[str]:
    """
    Split Chinese text into sentences.

    Splits on Chinese sentence-end punctuation (。；！？) and Chinese-style
    enumeration semicolons. Filters empty strings and very short fragments.
    """
    # Split, but keep the punctuation by using lookbehind
    sentences = re.split(r'(?<=[。；！？])', text)
    # Clean up
    cleaned = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        # Remove trailing punctuation for length calculation
        if len(s) < 5:
            continue
        if is_legal_sentence(s):
            continue
        cleaned.append(s)
    return cleaned


def compute_burstiness_cv(lengths: List[int]) -> float:
    """Compute coefficient of variation (std/mean) for a list of lengths."""
    if not lengths:
        return 0.0
    mean = sum(lengths) / len(lengths)
    if mean == 0:
        return 0.0
    variance = sum((l - mean) ** 2 for l in lengths) / len(lengths)
    std = variance ** 0.5
    return std / mean


def sliding_window_burstiness(sentences: List[str],
                              window_size: int = 4) -> List[dict]:
    """
    Compute CV for each sliding window of N sentences.

    Returns a list of dicts:
    [
      {
        'window_start': 0,
        'window_end': 3,
        'sentences': [...],
        'lengths': [12, 14, 13, 11],
        'cv': 0.08
      },
      ...
    ]
    """
    results = []
    for i in range(len(sentences) - window_size + 1):
        window = sentences[i:i + window_size]
        lengths = [len(s) for s in window]
        cv = compute_burstiness_cv(lengths)
        results.append({
            'window_start': i,
            'window_end': i + window_size - 1,
            'lengths': lengths,
            'cv': round(cv, 4),
            'sentences_preview': [s[:20] + '...' if len(s) > 20 else s
                                  for s in window],
        })
    return results


def analyze_text(text: str, section: str = 'all',
                 window_size: int = 4) -> dict:
    """Run full burstiness analysis on input text."""
    sentences = split_sentences(text)

    if len(sentences) < window_size:
        return {
            'sentence_count': len(sentences),
            'window_size': window_size,
            'global_cv': None,
            'flagged_windows': [],
            'recommendation': '句子数量不足，无法计算',
        }

    # Global CV
    all_lengths = [len(s) for s in sentences]
    global_cv = compute_burstiness_cv(all_lengths)

    # Sliding window CVs
    window_results = sliding_window_burstiness(sentences, window_size)

    # Flag windows with low CV
    threshold = SECTION_THRESHOLDS.get(section, SECTION_THRESHOLDS['all'])
    flagged = [w for w in window_results if w['cv'] < threshold]

    # Stats
    cv_values = [w['cv'] for w in window_results]
    mean_cv = sum(cv_values) / len(cv_values) if cv_values else 0

    # Determine severity
    flag_ratio = len(flagged) / len(window_results) if window_results else 0
    if flag_ratio > 0.5:
        severity = 'high'
        recommendation = '过半窗口低突发度，全文节奏机械，需大幅改写句长'
    elif flag_ratio > 0.25:
        severity = 'medium'
        recommendation = '部分窗口低突发度，需调整若干段落的句长节奏'
    elif flag_ratio > 0:
        severity = 'low'
        recommendation = '少量窗口低突发度，局部修改即可'
    else:
        severity = 'none'
        recommendation = '突发度正常，节奏自然'

    return {
        'sentence_count': len(sentences),
        'window_size': window_size,
        'section': section,
        'threshold': threshold,
        'global_cv': round(global_cv, 4),
        'mean_window_cv': round(mean_cv, 4),
        'total_windows': len(window_results),
        'flagged_windows_count': len(flagged),
        'flag_ratio': round(flag_ratio, 3),
        'severity': severity,
        'recommendation': recommendation,
        'flagged_windows': flagged[:10],  # Top 10 worst
    }


def main():
    parser = argparse.ArgumentParser(
        description='Compute sentence-length burstiness for Chinese patent text')
    parser.add_argument('--input', required=True, help='Input text file')
    parser.add_argument('--section', default='all',
                        choices=list(SECTION_THRESHOLDS.keys()),
                        help='Section context (default: all)')
    parser.add_argument('--window', type=int, default=4,
                        help='Sliding window size (default: 4)')
    parser.add_argument('--output', default=None,
                        help='Output JSON path (defaults to stdout)')
    args = parser.parse_args()

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    text = Path(args.input).read_text(encoding='utf-8')
    result = analyze_text(text, args.section, args.window)

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(output_json, encoding='utf-8')
        print(f'Result saved to {args.output}')
        print(f'Sentences: {result["sentence_count"]}')
        print(f'Global CV: {result["global_cv"]} (threshold: {result["threshold"]})')
        print(f'Flagged windows: {result["flagged_windows_count"]}/{result["total_windows"]}')
        print(f'Severity: {result["severity"]}')
        print(f'Recommendation: {result["recommendation"]}')
    else:
        print(output_json)


if __name__ == '__main__':
    main()
