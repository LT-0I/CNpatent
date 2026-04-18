#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
skeleton_sim.py — Sibling-list skeleton similarity detector.

Catches AI-style parallel骨架 in sibling list items that share the same
syntactic shell even when content words differ. The specific failure mode
this was built to catch (from 4c_effect.md of a real patent disclosure):

  （1）长距离巡检下几何先验场边界偏差不再单向累积：...
  （2）稀疏、延迟、含噪三重观测障碍下仍可完成 ... ：...；消融测试中 ...
  （3）射线深度查询之外存在同根于 ... ：... ；消融测试中 ...
  （4）闭环系统不出现过修正振荡：...
  （5）退化场景下系统行为可预测、下游可识别：...

All 5 items share skeleton:
  [locative/adverbial prefix] + [subject NP] + [negation/modal] + [main verb]
  + [：mechanism NP] + [；quantitative VP optional]

The old audit.py scored this 0/100 clean because its detectors only looked
at surface keywords and character-count variance.

Algorithm (POS-only signature, v1 — jieba + surface markers):
  1. Extract sibling groups (numbered `（N）...` items or same-paragraph
     `；`-separated clauses with parallel numbering).
  2. For each item compute feature tuple:
       (has_locative_prefix, has_negation_or_modal, has_colon_separator,
        has_semicolon_separator, main_verb_pos_class, length_bucket)
  3. Group items by signature. If any group has ≥3 items (`--min-siblings`),
     emit a Skeletal flag with signature + item excerpts.

Section gating:
  - --section 六 (具体实施方式): Skeletal flags emitted but marked
    non_scoring=True (numbered substeps are legitimately parallel).
  - --section all / 一～五: flags contribute to score.

Output JSON schema (to stdout or --output):
  {
    "flags": [
      {
        "signature": {...feature tuple as dict...},
        "item_count": N,
        "items": [{"index": 0, "excerpt": "..."}, ...],
        "non_scoring": false
      },
      ...
    ],
    "sibling_groups_detected": N,
    "total_items_analyzed": N
  }

CLI:
  PYTHONUTF8=1 python -X utf8 skeleton_sim.py \\
      --input 4c_effect.md \\
      --section 四 \\
      --min-siblings 3 \\
      --output flags.json

Dependencies: jieba (posseg). Standard-library only otherwise.
"""

import argparse
import io
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

try:
    import jieba.posseg as pseg
except ImportError:
    sys.stderr.write(
        "ERROR: jieba not installed. Run: pip install jieba\n"
    )
    sys.exit(2)


# ─────────────────────────────────────────────────────────────────────────
# Marker sets
# ─────────────────────────────────────────────────────────────────────────
# 否定副词 + 情态动词 (skeleton marker — AI 爱用对偶否定/情态)
NEGATION_WORDS = {'不', '不再', '未', '未曾', '非', '无', '别', '勿'}
MODAL_WORDS = {'可', '能', '将', '仍', '可以', '能够', '应', '应当',
               '须', '必须', '得以', '尚', '依然', '依旧', '仍然', '仍可'}
# 存在-类准情态动词 (4c 样本 3 的 "存在" 模式)
EXISTENCE_VERBS = {'存在', '具有', '具备', '拥有'}

# Locative markers that sit after a prefix NP (`...下`, `...中`, `...之外`)
LOCATIVE_SUFFIXES = {'下', '中', '内', '外', '之外', '之中', '之内',
                     '时', '际', '后', '前', '间', '里', '上'}

# Numbered item markers (sibling list detection)
NUMBERED_ITEM_RE = re.compile(
    r'^\s*[（(]\s*([0-9]+|[一二三四五六七八九十]+|[a-zA-Z])\s*[）)]\s*'
)


# ─────────────────────────────────────────────────────────────────────────
# Sibling group extraction
# ─────────────────────────────────────────────────────────────────────────
def extract_numbered_siblings(paragraphs):
    """Return list of sibling-groups.
    Each group is a list of dicts {index, marker, text, para_index}.
    A group is a run of consecutive paragraphs all starting with numbered
    items at the same depth (`（1）`, `（2）`, `（3）`, ...).
    """
    groups = []
    current = []
    last_num = None
    for pi, p in enumerate(paragraphs):
        m = NUMBERED_ITEM_RE.match(p)
        if m:
            marker = m.group(1)
            body = p[m.end():].strip()
            # Heuristic: parse numeric / Chinese numeral sequence
            try:
                num = int(marker) if marker.isdigit() else None
            except Exception:
                num = None
            if num is not None and (last_num is None or num == last_num + 1):
                current.append({'index': len(current), 'marker': marker,
                                'text': body, 'para_index': pi})
                last_num = num
            else:
                # New group start
                if len(current) >= 2:
                    groups.append(current)
                current = [{'index': 0, 'marker': marker, 'text': body,
                            'para_index': pi}]
                last_num = num
        else:
            if len(current) >= 2:
                groups.append(current)
            current = []
            last_num = None
    if len(current) >= 2:
        groups.append(current)
    return groups


# ─────────────────────────────────────────────────────────────────────────
# Signature computation
# ─────────────────────────────────────────────────────────────────────────
def compute_signature(text):
    """Compute a POS-based skeleton signature for a single sibling item."""
    tokens = list(pseg.cut(text))
    if not tokens:
        return None
    words = [t.word for t in tokens]
    pos_seq = [t.flag for t in tokens]

    # Feature 1: locative prefix in the first 8 tokens?
    # Either a /f POS (方位词) or a known locative-suffix word.
    first_window = tokens[:8]
    has_locative_prefix = any(
        t.flag == 'f' or t.word in LOCATIVE_SUFFIXES
        for t in first_window
    )

    # Feature 2: has negation or modal or existence-verb in first 12 tokens
    first12 = tokens[:12]
    has_neg_or_modal = any(
        t.word in NEGATION_WORDS
        or t.word in MODAL_WORDS
        or t.word in EXISTENCE_VERBS
        for t in first12
    )

    # Feature 3: colon separator present (`：` or `:`)
    has_colon = '：' in text or ':' in text

    # Feature 4: semicolon separator present (`；` or `;`)
    has_semicolon = '；' in text or ';' in text

    # Feature 5: main verb POS class (first v/vn after pos 2)
    # (skip the very first token to avoid `退化/v 场景` being treated
    #  as main verb — usually prefix modifier)
    main_verb_pos = 'none'
    for t in tokens[1:]:
        if t.flag in ('v', 'vn'):
            main_verb_pos = t.flag
            break

    # Feature 6: token count bucket — 2-level coarse bucket only.
    # Fine buckets split near-parallel items across bucket boundaries
    # and under-report the flag size. Patent siblings are rarely uniform
    # in length by ±5 tokens anyway; the骨架 signal lives elsewhere.
    n = len(tokens)
    bucket = 'short' if n < 25 else 'long'

    return {
        'has_locative_prefix': has_locative_prefix,
        'has_neg_or_modal': has_neg_or_modal,
        'has_colon': has_colon,
        'has_semicolon': has_semicolon,
        'main_verb_pos': main_verb_pos,
        'length_bucket': bucket,
    }


def signature_key(sig):
    """Convert signature dict to a hashable key for grouping.
    length_bucket intentionally excluded — patent siblings rarely share
    exact length, and including it fragments otherwise-parallel groups
    across bucket boundaries. The skeleton signal lives in the marker
    features, not the length.
    """
    return (sig['has_locative_prefix'], sig['has_neg_or_modal'],
            sig['has_colon'], sig['main_verb_pos'])


# ─────────────────────────────────────────────────────────────────────────
# Main analysis
# ─────────────────────────────────────────────────────────────────────────
def analyze(text, section='all', min_siblings=3):
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    groups = extract_numbered_siblings(paragraphs)

    flags = []
    total_items = 0
    for group in groups:
        if len(group) < min_siblings:
            continue
        # Compute signature per item
        sigs = []
        for item in group:
            sig = compute_signature(item['text'])
            if sig is None:
                continue
            sig['__key'] = signature_key(sig)
            sig['__item'] = item
            sigs.append(sig)
        total_items += len(sigs)

        # Cluster by signature key
        buckets = defaultdict(list)
        for sig in sigs:
            buckets[sig['__key']].append(sig)

        for key, matched in buckets.items():
            if len(matched) < min_siblings:
                continue
            # Drop trivial signatures (all-False, non-verb) — less interesting
            has_locative, has_neg, has_colon, main_verb = key
            # Require at least 2 meaningful structural markers
            # (otherwise we'd flag plain prose lists that share no骨架).
            # Treat has_colon OR has_semicolon as ONE separator marker —
            # items with `；数据` tails but no `：机制` colon (e.g. 4c
            # item 1's variant form) should still qualify.
            any_separator = has_colon or any(
                sig['has_semicolon'] for sig in matched
            )
            marker_score = sum([has_locative, has_neg, any_separator])
            if marker_score < 2:
                continue

            items_excerpt = [
                {'marker': sig['__item']['marker'],
                 'excerpt': (sig['__item']['text'][:60]
                             + ('...' if len(sig['__item']['text']) > 60
                                else ''))}
                for sig in matched
            ]
            flag = {
                'signature': {
                    'has_locative_prefix': has_locative,
                    'has_neg_or_modal': has_neg,
                    'has_colon_separator': has_colon,
                    'main_verb_pos': main_verb,
                },
                'item_count': len(matched),
                'total_siblings_in_group': len(group),
                'items': items_excerpt,
                # Section gate: §6 numbered substeps are legitimately
                # parallel (per patent style); mark non_scoring.
                'non_scoring': (section == '六'),
                'category': 'skeletal',
                'weight': 10,
                'pattern': '兄弟条目骨架高度平行',
            }
            flags.append(flag)

    return {
        'flags': flags,
        'sibling_groups_detected': len(groups),
        'total_items_analyzed': total_items,
    }


# ─────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description='Sibling-list skeleton similarity detector')
    parser.add_argument('--input', required=True)
    parser.add_argument('--section', default='all',
                        help='Section context (一/二/三/四/五/六/all)')
    parser.add_argument('--min-siblings', type=int, default=3,
                        help='Minimum parallel items to trigger flag (default 3)')
    parser.add_argument('--output', default=None)
    args = parser.parse_args()

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    text = Path(args.input).read_text(encoding='utf-8')
    result = analyze(text, section=args.section,
                     min_siblings=args.min_siblings)
    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(out, encoding='utf-8')
        print(f'skeleton_sim → {args.output}')
        print(f'  sibling_groups={result["sibling_groups_detected"]} '
              f'items={result["total_items_analyzed"]} '
              f'flags={len(result["flags"])}')
    else:
        print(out)


if __name__ == '__main__':
    main()
