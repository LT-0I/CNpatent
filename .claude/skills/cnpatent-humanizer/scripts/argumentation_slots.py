#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
argumentation_slots.py — Detect argumentation-slot exhaustion.

AI-generated patent prose tends to fill EVERY sibling list item with the
same rhetorical slots: mechanism + data + contrast + caveat. Human writers
vary slot density — some items are brief, some bear all the weight. When
a bulleted list has 5 items each carrying {mechanism, data, contrast},
that uniformity is the 4c_effect.md failure mode in semantic form, even
if the word choices differ across items.

Slots detected (keyword-anchored regex, deterministic):

  mechanism : explanatory connective, how-clauses, causal markers
              e.g. "通过 ... 实现", "经 ... 校验", "由 ... 组成"
  data      : quantitative words or measurement units
              e.g. "约八成", "5 个百分点", "平均值 ±", 百分号, 数字+单位
  contrast  : comparative/ablation reference
              e.g. "相较 ...", "相比 ...", "较 ... 下降", "消融测试"
  caveat    : acknowledged limitation / scoping clause
              e.g. "仅 ...", "限于 ...", "在 ... 条件下",
                   "退化 ...", "触发条件 ..."
  motivation: reason-for-being, problem-statement
              e.g. "为解决 ...", "针对 ...", "由于 ...", "避免 ..."

Flag logic:
  - For each sibling group (numbered list items), count slot occurrences
    per item.
  - If ≥3 items each carry ≥3 distinct slots → emit an argumentation
    exhaustion flag (Skeletal category, weight 10).
  - If ≥3 items share the SAME slot set (e.g. all have {mechanism, data,
    contrast}) → emit a slot-uniform flag (Skeletal, weight 10).

Section gating: §6 具体实施方式 substeps legitimately use this scaffold;
  flag is emitted but marked non_scoring=True.

CLI:
  PYTHONUTF8=1 python -X utf8 argumentation_slots.py \\
      --input 4c_effect.md \\
      --section 四 \\
      --output slots.json

No external dependencies — regex-only.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

NUMBERED_ITEM_RE = re.compile(
    r'^\s*[（(]\s*([0-9]+|[一二三四五六七八九十]+|[a-zA-Z])\s*[）)]\s*'
)


# ─────────────────────────────────────────────────────────────────────────
# Slot-marker patterns
# ─────────────────────────────────────────────────────────────────────────
SLOT_PATTERNS = {
    # Mechanism: instrumental or causative construct. Bag-of-markers
    # because Chinese realizes this slot through many prepositional /
    # verbal marks; narrow pattern regex misses too much.
    'mechanism': [
        r'通过[^，。；：]{2,30}',
        r'利用[^，。；：]{2,25}',
        r'基于[^，。；：]{2,25}',
        r'经[^，。；：]{2,25}(?:后|校验|处理|修正|融合|滤波|拟合|计算)',
        r'由[^，。；：]{2,25}(?:组成|构成|形成|包括|产生|获取|拟合)',
        r'以[^，。；：]{2,25}(?:方式|比例|阻尼|注入|方法)',
        r'从[^，。；：]{2,25}推断',
        r'采用[^，。；：]{2,20}',
        r'将[^，。；：]{2,30}(?:输入|映射|投影|转化|降维|反馈|注入|施加)',
        r'使[^，。；：]{2,30}(?:更新|衰减|收敛|减小|增大|校正|修正)',
        r'令[^，。；：]{2,20}',
        r'借助',
    ],
    'data': [
        r'[零一二三四五六七八九十百千万]{1,4}成',
        r'\d+(?:\.\d+)?\s*个?百分点',
        r'\d+(?:\.\d+)?\s*%',
        r'约\s*[零一二三四五六七八九十百千万\d]',
        r'下降(?:约)?\s*[\d零一二三四五六七八九十]',
        r'提高(?:约)?\s*[\d零一二三四五六七八九十]',
        r'\d+(?:\.\d+)?\s*(?:倍|分贝|毫秒|微秒|米|厘米|毫米)',
        r'平均(?:值)?\s*[±]',
        r'\d+\s*×\s*\d+',
        r'(?<![\w\d])[hHwWαβγKN]\s*[=取为]\s*\d',
        r'测试(?:集|中)[^，。；：]{0,30}(?:未|已|经|约|下降|提高)',
    ],
    'contrast': [
        r'相(?:较|比)(?:于)?',
        r'较[^，。；：]{2,15}(?:下降|降低|提高|增加|显著)',
        r'消融',
        r'对照(?:组|实验)?',
        r'基线',
        r'单向(?:流水线|架构|方案)',
        r'仅(?:修正|采用|保留|选取|依赖)',
        r'打破[^，。；：]{2,30}',
        r'不再(?:单向|累积|依赖)',
        r'之外(?:存在|还|另外|独立)',
    ],
    'caveat': [
        r'触发条件',
        r'条件不满足',
        r'退化(?:为|模式|场景)',
        r'仅限',
        r'在[^，。；：]{2,20}条件下',
        r'暂停',
        r'(?:不足时|超阈值|超过\s*阈值|不可观测)',
        r'异常(?:帧|场景|条件)?',
        r'告警',
        r'未观察到',
        r'过\s*修正(?:振荡|风险)',
    ],
    'motivation': [
        r'为解决',
        r'针对[^，。；：]{2,30}(?:的)?(?:问题|难题|挑战|缺陷|不足|失效)',
        r'由于[^，。；：]{2,30}',
        r'鉴于',
        r'为(?:避免|防止|抑制)',
        r'以解决',
    ],
}


def extract_numbered_siblings(paragraphs):
    """Reuse skeleton_sim's sibling-group extraction logic."""
    groups = []
    current = []
    last_num = None
    for pi, p in enumerate(paragraphs):
        m = NUMBERED_ITEM_RE.match(p)
        if m:
            marker = m.group(1)
            body = p[m.end():].strip()
            try:
                num = int(marker) if marker.isdigit() else None
            except Exception:
                num = None
            if num is not None and (last_num is None or num == last_num + 1):
                current.append({'index': len(current), 'marker': marker,
                                'text': body, 'para_index': pi})
                last_num = num
            else:
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


def detect_slots(text):
    """Return list of slot names present in text."""
    found = []
    for slot_name, patterns in SLOT_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text):
                found.append(slot_name)
                break
    return found


def analyze(text, section='all', min_items=3, min_slots_per_item=2):
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    groups = extract_numbered_siblings(paragraphs)
    flags = []
    total_items = 0

    for group in groups:
        if len(group) < min_items:
            continue

        item_slots = []
        for item in group:
            slots = detect_slots(item['text'])
            item_slots.append({'item': item, 'slots': slots})
        total_items += len(item_slots)

        # Flag A: "exhaustive argumentation" — N items each with ≥K slots
        heavy_items = [x for x in item_slots
                       if len(set(x['slots'])) >= min_slots_per_item]
        if len(heavy_items) >= min_items:
            flags.append({
                'pattern': '兄弟条目论证完备度均匀',
                'subtype': 'exhaustive',
                'category': 'skeletal',
                'weight': 10,
                'item_count': len(heavy_items),
                'total_siblings_in_group': len(group),
                'items': [
                    {'marker': x['item']['marker'],
                     'slots_detected': sorted(set(x['slots'])),
                     'excerpt': x['item']['text'][:60]
                                + ('...' if len(x['item']['text']) > 60 else '')}
                    for x in heavy_items
                ],
                'non_scoring': (section == '六'),
                'description': (
                    f'≥{len(heavy_items)} 条兄弟条目各承载 ≥'
                    f'{min_slots_per_item} 个论证槽位 '
                    f'(机制/数据/对比/caveat/motivation)，论证穷尽同质'
                ),
            })

        # Flag B: "slot-uniform" — N items share SAME slot set
        slot_set_counter = Counter()
        for x in item_slots:
            slot_set_counter[tuple(sorted(set(x['slots'])))] += 1
        for slot_set, count in slot_set_counter.items():
            if count >= min_items and len(slot_set) >= 2:
                matched = [x for x in item_slots
                           if tuple(sorted(set(x['slots']))) == slot_set]
                flags.append({
                    'pattern': '兄弟条目论证槽位相同',
                    'subtype': 'uniform',
                    'category': 'skeletal',
                    'weight': 10,
                    'item_count': count,
                    'total_siblings_in_group': len(group),
                    'slot_set': list(slot_set),
                    'items': [
                        {'marker': x['item']['marker'],
                         'excerpt': x['item']['text'][:60]
                                    + ('...' if len(x['item']['text']) > 60 else '')}
                        for x in matched
                    ],
                    'non_scoring': (section == '六'),
                    'description': (
                        f'≥{count} 条兄弟条目拥有完全相同的 '
                        f'{list(slot_set)} 槽位组合'
                    ),
                })

    return {
        'flags': flags,
        'sibling_groups_detected': len(groups),
        'total_items_analyzed': total_items,
    }


def main():
    parser = argparse.ArgumentParser(
        description='Argumentation-slot exhaustion detector')
    parser.add_argument('--input', required=True)
    parser.add_argument('--section', default='all')
    parser.add_argument('--min-items', type=int, default=3)
    parser.add_argument('--min-slots-per-item', type=int, default=2,
                        help='Slots per item needed for exhaustive flag '
                             '(default 2; 3 is patent-engineer-grade strict)')
    parser.add_argument('--output', default=None)
    args = parser.parse_args()

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    text = Path(args.input).read_text(encoding='utf-8')
    result = analyze(text, section=args.section,
                     min_items=args.min_items,
                     min_slots_per_item=args.min_slots_per_item)
    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(out, encoding='utf-8')
        print(f'argumentation_slots → {args.output}')
        print(f'  sibling_groups={result["sibling_groups_detected"]} '
              f'items={result["total_items_analyzed"]} '
              f'flags={len(result["flags"])}')
    else:
        print(out)


if __name__ == '__main__':
    main()
