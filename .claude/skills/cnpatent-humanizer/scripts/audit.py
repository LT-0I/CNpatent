#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cnpatent-humanizer audit script.

Performs Phase 1 multi-dimensional detection and Phase 2 weighted scoring
on Chinese patent text. Outputs a JSON report.

Usage:
    PYTHONUTF8=1 python -X utf8 audit.py \\
        --input draft.txt \\
        --section all \\
        --term-lock terms.json \\
        --output audit_report.json

This script does NOT rewrite text. It detects issues and scores them.
LLM-driven semantic rewrite happens in a separate step.
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────
# Tier 1 vocabulary (always-flagged, single occurrence triggers)
# Subset of references/three-tier-vocabulary.md
# ─────────────────────────────────────────────────────────────────────────
TIER1_WORDS: Dict[str, str] = {
    # 推销/夸大类
    '显著提升': '提高', '显著提高': '提高', '显著改善': '改善',
    '大幅提升': '提高', '大幅降低': '降低', '极大提升': '提高',
    '卓越的': '较高的', '优异的': '较高的', '出色的': '较高的',
    '颠覆性的': '', '革命性的': '', '突破性的': '',
    '划时代的': '', '开创性的': '', '创新性地': '',
    '巧妙地': '', '精妙地': '', '完美解决': '解决', '完美实现': '实现',
    '高效地': '', '高效的': '', '精准地': '', '精准的': '',
    '具有广阔的应用前景': '', '意义深远': '',
    # 过渡填充词
    '值得注意的是': '', '需要指出的是': '', '需要强调的是': '',
    '至关重要': '', '尤为关键': '关键', '旨在': '用于',
    '致力于': '', '得益于': '基于', '鉴于此': '', '有鉴于此': '',
    '综上所述': '', '总而言之': '', '总之': '',
    '毋庸置疑': '', '不言而喻': '', '在此基础上': '',
    '从本质上讲': '', '从根本上说': '',
    '充分利用': '利用', '充分考虑': '考虑',
    # 排比/结构连接词
    '首先': '', '其次': '', '然后': '', '最后': '',
    '其一': '', '其二': '', '其三': '',
    # 学术腔
    '本文': '本发明', '实验结果表明': '', '研究发现': '',
    '研究表明': '', '我们提出': '本发明提供', '笔者': '', '据报道': '',
    # AI 高频结构
    '进一步地': '', '更为重要的是': '', '值得一提的是': '',
    '具体来说': '', '具体而言': '', '与此同时': '',
    '由此可以看出': '', '事实上': '', '实际上': '',
    '换言之': '', '换句话说': '', '不难发现': '', '由此可见': '',
    '总的来说': '',
}


# ─────────────────────────────────────────────────────────────────────────
# Tier 2: cluster-flagged (only flag when count exceeds threshold)
# ─────────────────────────────────────────────────────────────────────────
TIER2_RULES: Dict[str, Dict] = {
    '基于': {'scope': 'paragraph', 'threshold': 3},
    '通过': {'scope': 'paragraph', 'threshold': 3},
    '利用': {'scope': 'paragraph', 'threshold': 3},
    '采用': {'scope': 'paragraph', 'threshold': 3},
    '使用': {'scope': 'paragraph', 'threshold': 3},
    '在...的过程中': {'scope': 'document', 'threshold': 3, 'regex': r'在.{1,15}的过程中'},
    '在...的基础上': {'scope': 'document', 'threshold': 3, 'regex': r'在.{1,15}的基础上'},
    '随着...的发展': {'scope': 'document', 'threshold': 2, 'regex': r'随着.{1,15}的(?:不断)?发展'},
    '在...的背景下': {'scope': 'document', 'threshold': 2, 'regex': r'在.{1,15}的背景下'},
    '同时': {'scope': 'document', 'threshold': 5},
    '此外': {'scope': 'document', 'threshold': 4},
    '另外': {'scope': 'document', 'threshold': 4},
    '较高的': {'scope': 'paragraph', 'threshold': 2},
    '较好的': {'scope': 'paragraph', 'threshold': 2},
    '较为': {'scope': 'paragraph', 'threshold': 2},
    '一定的': {'scope': 'paragraph', 'threshold': 2},
}


# ─────────────────────────────────────────────────────────────────────────
# Tier 3: density-flagged (only flag when global density exceeds threshold)
# ─────────────────────────────────────────────────────────────────────────
TIER3_RULES: Dict[str, float] = {
    '是': 0.020,
    '进行': 0.010,
    '实现': 0.008,
    '通过': 0.015,
    '利用': 0.010,
    '系统': 0.010,
    '方法': 0.015,
    '该': 0.010,
    '所述': 0.025,  # context-dependent (see below)
}


# ─────────────────────────────────────────────────────────────────────────
# Critical structural patterns (weight 8)
# ─────────────────────────────────────────────────────────────────────────
CRITICAL_STRUCTURAL = [
    ('三段式连接词', r'^(?:首先|其次|然后|最后)'),
    ('其一其二其三', r'其一[\u4e00-\u9fa5]{0,30}其二'),
    ('综上所述类', r'综上所述|总而言之|^总之[，,]'),
    ('第一人称', r'\b(?:我们|笔者)\b'),
    ('商业宣传语', r'颠覆性|革命性|突破性|划时代|开创性'),
]

HIGH_STRUCTURAL = [
    ('推销形容词', r'(?:显著|大幅|极大|卓越|优异|出色)的?(?:提升|提高|改善)?'),
    ('AI 高频虚词', r'旨在|致力于|得益于|有鉴于此|鉴于此'),
    ('平衡式句型', r'虽然.{1,30}但.{1,30}同时|不仅.{1,30}而且|既.{1,30}又'),
    ('模板套句', r'随着.{1,15}的(?:不断)?发展|在.{1,15}的背景下|众所周知'),
    ('值得注意类', r'值得注意的是|需要(?:指出|强调|说明)的是|值得一提'),
    ('学术引文', r'\[\d+\]|参见(?:文献|论文)|实验结果表明'),
    ('段尾总结', r'为后续.{1,15}(?:奠定|提供|打下).{0,10}基础'),
]

MEDIUM_STRUCTURAL = [
    ('过度对冲', r'可能|也许|或许|大概|大约'),
    ('破折号过用', r'——'),
    ('动词名词化', r'(?:对.{1,10})?进行[\u4e00-\u9fa5]{1,4}'),
    ('比较级模糊', r'更(?:好|高|快|强|准)(?!的具体)'),
    ('X 化处理', r'[\u4e00-\u9fa5]化处理'),
]


# ─────────────────────────────────────────────────────────────────────────
# Protected region detection
# ─────────────────────────────────────────────────────────────────────────
LEGAL_PREFIXES = [
    r'^为了更清楚地说明本发明实施例',
    r'^构成本申请的一部分的附图',
    r'^现详细说明本发明的多种示例性实施方式',
    r'^应理解本发明中所述的术语仅仅是为描述',
    r'^在不背离本发明的范围或精神的情况下',
    r'^关于本文中所使用的',
    r'^需要说明的是，在不冲突的情况下',
    r'^以上所述，仅为本申请较佳的具体实施方式',
]

HEADING_PATTERNS = [
    r'^[一二三四五六七]、',
    r'^发明目的$',
    r'^技术解决方案$',
    r'^3、技术效果',
]

FORMULA_INDICATORS = [r'\$[^$]+\$', r'\\frac', r'\\sum', r'\\int',
                      r'\\mathbf', r'\\sigma', r'\\alpha', r'\\nabla']

FIGURE_DESC_PATTERN = r'^图\s*\d+\s*[，,]?\s*为本发明'


def is_protected(paragraph_text: str) -> Tuple[bool, str]:
    """Return (is_protected, reason)"""
    text = paragraph_text.strip()
    if not text:
        return True, '空段'
    for pattern in LEGAL_PREFIXES:
        if re.match(pattern, text):
            return True, f'法律声明段'
    for pattern in HEADING_PATTERNS:
        if re.match(pattern, text):
            return True, f'章节标题段'
    for pattern in FORMULA_INDICATORS:
        if re.search(pattern, text):
            return True, f'含公式'
    if re.match(FIGURE_DESC_PATTERN, text):
        return True, f'附图描述行'
    return False, ''


def mask_terms(text: str, terms: List[str]) -> Tuple[str, Dict[str, str]]:
    """Replace term-lock entries with placeholders to avoid false positives."""
    mapping = {}
    masked = text
    for i, term in enumerate(sorted(terms, key=len, reverse=True)):
        placeholder = f'__TERM_{i:04d}__'
        if term in masked:
            masked = masked.replace(term, placeholder)
            mapping[placeholder] = term
    return masked, mapping


# ─────────────────────────────────────────────────────────────────────────
# Detection functions
# ─────────────────────────────────────────────────────────────────────────
def detect_tier1(text: str) -> List[Dict]:
    hits = []
    for word, replacement in TIER1_WORDS.items():
        for m in re.finditer(re.escape(word), text):
            hits.append({
                'tier': 1, 'word': word, 'replacement': replacement,
                'position': m.start(), 'category': 'critical_or_high',
            })
    return hits


def detect_tier2(text: str, paragraphs: List[str]) -> List[Dict]:
    hits = []
    for word, rule in TIER2_RULES.items():
        pattern = rule.get('regex', re.escape(word))
        if rule['scope'] == 'paragraph':
            for i, para in enumerate(paragraphs):
                if is_protected(para)[0]:
                    continue
                count = len(re.findall(pattern, para))
                if count >= rule['threshold']:
                    hits.append({
                        'tier': 2, 'word': word, 'count': count,
                        'paragraph': i, 'scope': 'paragraph',
                    })
        elif rule['scope'] == 'document':
            count = len(re.findall(pattern, text))
            if count >= rule['threshold']:
                hits.append({
                    'tier': 2, 'word': word, 'count': count,
                    'scope': 'document',
                })
    return hits


def detect_tier3(text: str) -> List[Dict]:
    hits = []
    total = len(text)
    if total == 0:
        return hits
    for word, threshold in TIER3_RULES.items():
        count = len(re.findall(re.escape(word), text))
        density = (count * len(word)) / total
        if density > threshold:
            hits.append({
                'tier': 3, 'word': word, 'count': count,
                'density': round(density, 4), 'threshold': threshold,
            })
    return hits


def detect_critical_structural(text: str, paragraphs: List[str]) -> List[Dict]:
    hits = []
    for name, pattern in CRITICAL_STRUCTURAL:
        # 段首匹配
        if pattern.startswith('^'):
            for i, para in enumerate(paragraphs):
                if is_protected(para)[0]:
                    continue
                if re.match(pattern[1:], para):
                    hits.append({
                        'category': 'critical', 'pattern': name,
                        'paragraph': i, 'weight': 8,
                    })
        else:
            for m in re.finditer(pattern, text):
                hits.append({
                    'category': 'critical', 'pattern': name,
                    'position': m.start(), 'weight': 8,
                })
    return hits


def detect_high_structural(text: str) -> List[Dict]:
    hits = []
    for name, pattern in HIGH_STRUCTURAL:
        for m in re.finditer(pattern, text):
            hits.append({
                'category': 'high', 'pattern': name,
                'position': m.start(), 'matched': m.group(0), 'weight': 4,
            })
    return hits


def detect_medium_structural(text: str) -> List[Dict]:
    hits = []
    for name, pattern in MEDIUM_STRUCTURAL:
        count = len(re.findall(pattern, text))
        # 过度对冲只有 ≥5 次才标记
        threshold = 5 if name == '过度对冲' else (
            10 if name == '动词名词化' else (
            3 if name == '破折号过用' else 1))
        if count >= threshold:
            hits.append({
                'category': 'medium', 'pattern': name,
                'count': count, 'threshold': threshold, 'weight': 2,
            })
    return hits


# ─────────────────────────────────────────────────────────────────────────
# Style detection (burstiness, paragraph uniformity)
# ─────────────────────────────────────────────────────────────────────────
def split_sentences(text: str) -> List[str]:
    """Split Chinese text into sentences by 。；！？"""
    sentences = re.split(r'[。；！？]', text)
    return [s.strip() for s in sentences if s.strip()]


def compute_burstiness(sentences: List[str], window: int = 4) -> List[float]:
    """Return CV (std/mean) for each sliding window of N sentences."""
    cvs = []
    for i in range(len(sentences) - window + 1):
        lens = [len(s) for s in sentences[i:i+window]]
        if not lens:
            continue
        mean = sum(lens) / len(lens)
        if mean == 0:
            continue
        var = sum((l - mean) ** 2 for l in lens) / len(lens)
        cv = (var ** 0.5) / mean
        cvs.append(cv)
    return cvs


def detect_style(text: str, paragraphs: List[str], section: str = 'all') -> List[Dict]:
    hits = []

    # 1. Sentence burstiness
    sentences = split_sentences(text)
    cvs = compute_burstiness(sentences, window=4)
    threshold = 0.12 if section == '六' else (0.15 if section == 'all' else 0.18)
    low_cv_count = sum(1 for cv in cvs if cv < threshold)
    if low_cv_count >= 3:
        hits.append({
            'category': 'style', 'pattern': '句长突发度低',
            'count': low_cv_count, 'threshold': threshold, 'weight': 1.5,
        })

    # 2. Paragraph length uniformity
    non_protected = [p for p in paragraphs if not is_protected(p)[0]]
    if len(non_protected) >= 4:
        for i in range(len(non_protected) - 3):
            window = non_protected[i:i+4]
            lens = [len(p) for p in window]
            mean = sum(lens) / len(lens)
            if mean == 0:
                continue
            max_dev = max(abs(l - mean) for l in lens) / mean
            if max_dev < 0.15:
                hits.append({
                    'category': 'style', 'pattern': '段落长度均匀',
                    'paragraphs': list(range(i, i+4)),
                    'max_deviation': round(max_dev, 3), 'weight': 1.5,
                })
                break  # one hit is enough for this category

    # 3. Repeated paragraph-start connectives
    starts = [p[:4] for p in non_protected if len(p) >= 4]
    connectives = ['因此', '同时', '此外', '另外', '所以', '由此']
    consecutive_count = 0
    max_consecutive = 0
    for s in starts:
        if any(s.startswith(c) for c in connectives):
            consecutive_count += 1
            max_consecutive = max(max_consecutive, consecutive_count)
        else:
            consecutive_count = 0
    if max_consecutive >= 3:
        hits.append({
            'category': 'style', 'pattern': '段首连续关联词',
            'count': max_consecutive, 'weight': 1.5,
        })

    return hits


# ─────────────────────────────────────────────────────────────────────────
# Patent-specific pattern detection
# ─────────────────────────────────────────────────────────────────────────
def detect_patent_specific(text: str, paragraphs: List[str], section: str) -> List[Dict]:
    hits = []

    # 1. Formulas in 发明内容
    if section == '四' or section == 'all':
        in_section_4 = False
        for p in paragraphs:
            if re.match(r'^四、', p):
                in_section_4 = True
                continue
            if re.match(r'^[五六七]、', p):
                in_section_4 = False
            if in_section_4 and re.search(r'\$[^$]+\$', p):
                hits.append({
                    'category': 'patent', 'pattern': '公式出现在发明内容',
                    'weight': 6,
                })
                break

    # 2. 所述 in 附图说明
    if section == '五' or section == 'all':
        in_section_5 = False
        for p in paragraphs:
            if re.match(r'^五、', p):
                in_section_5 = True
                continue
            if re.match(r'^六、', p):
                in_section_5 = False
            if in_section_5 and '所述' in p and not is_protected(p)[0]:
                hits.append({
                    'category': 'patent', 'pattern': '附图说明含所述',
                    'weight': 6,
                })

    # 3. Sub-step format check (only in section 六)
    sub_step_pattern = r'^[\(（]?(?:[a-zA-Z0-9]{1,3})[\)）][^：]'
    bad_format = r'^[\(（][a-zA-Z][\)）]|^[A-Z]\.|^\d\.'
    if section == '六' or section == 'all':
        for p in paragraphs:
            if re.match(bad_format, p):
                hits.append({
                    'category': 'patent', 'pattern': '子步骤格式错误',
                    'weight': 6,
                })
                break

    # 4. Even-number-of-steps detection (4/6/8)
    step_count = len(re.findall(r'^[（\(]\d+[）\)]', '\n'.join(paragraphs), re.MULTILINE))
    if step_count in (4, 6, 8):
        hits.append({
            'category': 'patent', 'pattern': f'步骤数为偶数({step_count})',
            'weight': 6,
        })

    return hits


# ─────────────────────────────────────────────────────────────────────────
# Term lock violation detection
# ─────────────────────────────────────────────────────────────────────────
def detect_term_drift(text: str, term_lock: Optional[Dict[str, List[str]]] = None) -> List[Dict]:
    """
    term_lock: dict mapping canonical term -> list of forbidden synonyms
    e.g., {"稀疏点云": ["初始点云", "原始点云"]}
    """
    hits = []
    if not term_lock:
        return hits
    for canonical, synonyms in term_lock.items():
        for syn in synonyms:
            count = len(re.findall(re.escape(syn), text))
            if count > 0:
                hits.append({
                    'category': 'critical', 'pattern': '术语漂移',
                    'canonical': canonical, 'forbidden_synonym': syn,
                    'count': count, 'weight': 8,
                })
    return hits


# ─────────────────────────────────────────────────────────────────────────
# Scoring
# ─────────────────────────────────────────────────────────────────────────
def compute_score(all_hits: List[Dict], enable_skeletal: bool = False,
                  enable_sentential: bool = False,
                  enable_rhetorical: bool = False) -> Dict:
    weights = {'critical': 8, 'high': 4, 'medium': 2, 'style': 1.5, 'patent': 6}
    if enable_skeletal:
        weights['skeletal'] = 10
    if enable_sentential:
        weights['sentential'] = 3
    if enable_rhetorical:
        weights['rhetorical'] = 6
    breakdown = {k: 0 for k in weights}
    for hit in all_hits:
        cat = hit.get('category', 'high')
        if cat == 'critical_or_high':
            cat = 'high'
        if cat in breakdown:
            # non_scoring flags contribute 0 regardless of weight
            if hit.get('non_scoring'):
                continue
            count = hit.get('count', 1)
            w = hit.get('weight', weights[cat])
            breakdown[cat] += count * w
    total = min(100, sum(breakdown.values()))
    if total < 25:
        level = 'low'
    elif total < 50:
        level = 'medium'
    elif total < 75:
        level = 'high'
    else:
        level = 'very_high'
    return {'score': round(total, 1), 'level': level, 'breakdown': breakdown}


def decide_action(score_obj: Dict, all_hits: List[Dict],
                  enable_skeletal: bool = False,
                  section: str = 'all') -> Dict:
    """Decide rewrite vs patch using avoid-ai-writing's threshold."""
    tier1_count = sum(1 for h in all_hits if h.get('tier') == 1)
    cat_set = set(h.get('category', '') for h in all_hits)
    # exclude term drift counted separately
    drift = sum(1 for h in all_hits
                if h.get('pattern') == '术语漂移')

    if drift >= 3:
        return {'action': 'rewrite',
                'reason': f'术语漂移 {drift} 处，必须整体重写'}

    # Skeletal gated rule (§1–5 only; §6 sub-steps are legitimately parallel).
    # Count only scoring-eligible skeletal flags (non_scoring=True is §6 gated).
    if enable_skeletal and section != '六':
        skel = [h for h in all_hits
                if h.get('category') == 'skeletal'
                and not h.get('non_scoring')]
        max_items = max((h.get('item_count', 0) for h in skel), default=0)
        if len(skel) >= 2 or max_items >= 4:
            return {'action': 'rewrite',
                    'reason': f'Skeletal 兄弟骨架/论证槽位穷尽 '
                              f'(flags={len(skel)}, max_items={max_items})'}

    if tier1_count >= 5 and len(cat_set) >= 3:
        return {'action': 'rewrite',
                'reason': f'Tier1 {tier1_count} 处 + {len(cat_set)} 类问题，整体重写'}

    if score_obj['score'] >= 75:
        return {'action': 'rewrite',
                'reason': f'总分 {score_obj["score"]} ≥ 75，整体重写'}

    if score_obj['score'] >= 25:
        return {'action': 'patch', 'reason': '局部修补即可'}

    return {'action': 'none', 'reason': '已合格，无需修改'}


# ─────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='cnpatent-humanizer audit')
    parser.add_argument('--input', required=True, help='Input text file path')
    parser.add_argument('--section', default='all',
                        help='Section context (一/二/三/四/五/六/all)')
    parser.add_argument('--term-lock', default=None,
                        help='JSON file with term lock dictionary')
    parser.add_argument('--output', default=None,
                        help='Output JSON path (defaults to stdout)')
    parser.add_argument('--enable-skeleton', action='store_true',
                        help='Enable Skeletal category (skeleton_sim + '
                             'argumentation_slots). Opt-in v1.3; OFF '
                             'preserves v1.2 byte-identical output.')
    parser.add_argument('--enable-sentential', action='store_true',
                        help='v1.4: enable Sentential category '
                             '(long_sentence + structural_density + '
                             'heading_length). Weight 3.')
    parser.add_argument('--enable-rhetorical', action='store_true',
                        help='v1.4: enable Rhetorical category '
                             '(triple_pattern + patent_boilerplate + '
                             'redundancy). Weight 6.')
    parser.add_argument('--enable-v15', action='store_true',
                        help='v1.5 opt-in: enable 7 new detectors '
                             '(topic_switch, enumeration_check, background_leak, '
                             'term_pronoun, unprepared_concept, param_segment, '
                             'merge_short). Flags map to critical/high/rhetorical/'
                             'style categories per rule.')
    parser.add_argument('--enable-all', action='store_true',
                        help='v1.4 shorthand: turn on skeleton + sentential '
                             '+ rhetorical + v1.5 detectors together.')
    parser.add_argument('--enable-reader', action='store_true',
                        help='Include reader_pass validated flags if '
                             '--reader-validated JSON exists')
    parser.add_argument('--reader-validated', default=None,
                        help='Path to reader_pass --mode validate output JSON')
    args = parser.parse_args()

    # Force UTF-8 on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    # --enable-all expands to all opt-in subsystems (v1.3 + v1.4 + v1.5)
    if args.enable_all:
        args.enable_skeleton = True
        args.enable_sentential = True
        args.enable_rhetorical = True
        args.enable_v15 = True

    # v1.5 rhetorical-category flags (topic_switch, unprepared_concept) rely on
    # rhetorical weight being loaded. Auto-enable rhetorical scoring so the
    # flags are not silently dropped.
    if args.enable_v15:
        args.enable_rhetorical = True

    text = Path(args.input).read_text(encoding='utf-8')
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    term_lock = None
    if args.term_lock:
        term_lock = json.loads(Path(args.term_lock).read_text(encoding='utf-8'))

    # Mask protected term-lock keys to avoid false positives
    all_terms = []
    if term_lock:
        for k, v in term_lock.items():
            all_terms.append(k)
    masked_text, mapping = mask_terms(text, all_terms)

    # Run all detectors
    all_hits = []
    all_hits.extend(detect_tier1(masked_text))
    all_hits.extend(detect_tier2(masked_text, paragraphs))
    all_hits.extend(detect_tier3(masked_text))
    all_hits.extend(detect_critical_structural(masked_text, paragraphs))
    all_hits.extend(detect_high_structural(masked_text))
    all_hits.extend(detect_medium_structural(masked_text))
    all_hits.extend(detect_style(masked_text, paragraphs, args.section))
    all_hits.extend(detect_patent_specific(text, paragraphs, args.section))
    all_hits.extend(detect_term_drift(text, term_lock))

    # Opt-in Skeletal detectors (v1.3). Default OFF preserves v1.2
    # byte-identical output.
    if args.enable_skeleton:
        # Import sibling detector modules from the same directory.
        import os
        _here = os.path.dirname(os.path.abspath(__file__))
        if _here not in sys.path:
            sys.path.insert(0, _here)
        import skeleton_sim
        import argumentation_slots
        skel_res = skeleton_sim.analyze(text, section=args.section)
        slot_res = argumentation_slots.analyze(text, section=args.section)
        for f in skel_res.get('flags', []):
            f.setdefault('category', 'skeletal')
            f.setdefault('weight', 10)
            f.setdefault('source', 'skeleton_sim')
            all_hits.append(f)
        for f in slot_res.get('flags', []):
            f.setdefault('category', 'skeletal')
            f.setdefault('weight', 10)
            f.setdefault('source', 'argumentation_slots')
            all_hits.append(f)

    # ── v1.4: Sentential detectors (H1/H16/H17 + H3/H4 + H18) ──
    if args.enable_sentential:
        import os
        _here = os.path.dirname(os.path.abspath(__file__))
        if _here not in sys.path:
            sys.path.insert(0, _here)
        import long_sentence
        import structural_density
        import heading_length

        # Gather term-lock tokens for noun-chunk false-positive suppression
        term_tokens = list(term_lock.keys()) if term_lock else []

        ls = long_sentence.detect(text, section=args.section)
        for f in (ls['flags_sentence'] + ls['flags_paragraph'] +
                  ls['flags_semicolon']):
            f.setdefault('category', 'sentential')
            wf = f.get('weight_factor', 1)
            f['weight'] = round(3 * wf, 1)
            f.setdefault('source', 'long_sentence')
            all_hits.append(f)

        sd = structural_density.detect(text, section=args.section,
                                       term_lock=term_tokens)
        for f in (sd['flags_long_premodifier'] +
                  sd['flags_compound_noun_chunk']):
            f.setdefault('category', 'sentential')
            f['weight'] = 3 * f.get('weight_factor', 1)
            f.setdefault('source', 'structural_density')
            all_hits.append(f)

        hl = heading_length.detect(text, section=args.section)
        for f in hl['flags']:
            f.setdefault('category', 'sentential')
            wf = f.get('weight_factor', 1)
            f['weight'] = 6 * wf  # H18 is weight=6 (double base) per plan
            f.setdefault('source', 'heading_length')
            all_hits.append(f)

    # ── v1.4: Rhetorical detectors (H5 + H6/H7/H8/H12 + H10) ──
    if args.enable_rhetorical:
        import os
        _here = os.path.dirname(os.path.abspath(__file__))
        if _here not in sys.path:
            sys.path.insert(0, _here)
        import triple_pattern
        import patent_boilerplate
        import redundancy

        term_tokens = list(term_lock.keys()) if term_lock else []

        tp = triple_pattern.detect(text, section=args.section)
        for f in tp['flags_cross_paragraph'] + tp['flags_hint_dense']:
            f.setdefault('category', 'rhetorical')
            f['weight'] = 6 * f.get('weight_factor', 1)
            f.setdefault('source', 'triple_pattern')
            all_hits.append(f)

        pb = patent_boilerplate.detect(text, section=args.section,
                                       term_lock=term_tokens)
        for f in (pb['flags_boilerplate'] + pb['flags_quote_coinage'] +
                  pb['flags_passive_written'] + pb['flags_end_summary']):
            f.setdefault('category', 'rhetorical')
            f.setdefault('weight', 6)
            f.setdefault('source', 'patent_boilerplate')
            all_hits.append(f)

        rd = redundancy.detect(text, section=args.section,
                               term_lock=term_tokens)
        for f in rd['flags_pairs'] + rd['flags_hubs']:
            f.setdefault('category', 'rhetorical')
            f['weight'] = 6 * f.get('weight_factor', 1)
            f.setdefault('source', 'redundancy')
            all_hits.append(f)

    # ── v1.5: 7 new detectors (R1-R14 coverage gaps + over-correction guard) ──
    if args.enable_v15:
        import os
        _here = os.path.dirname(os.path.abspath(__file__))
        if _here not in sys.path:
            sys.path.insert(0, _here)
        import topic_switch
        import enumeration_check
        import background_leak
        import term_pronoun
        import unprepared_concept
        import param_segment
        import merge_short

        term_tokens = list(term_lock.keys()) if term_lock else []

        ts = topic_switch.detect(text, section=args.section)
        for f in ts.get('flags_topic_switch', []) + ts.get('flags_long_switch', []):
            f.setdefault('source', 'topic_switch')
            all_hits.append(f)

        ec = enumeration_check.detect(text, section=args.section)
        for f in ec.get('flags_enumeration', []):
            f.setdefault('source', 'enumeration_check')
            all_hits.append(f)

        bl = background_leak.detect(text, section=args.section)
        for f in bl.get('flags_background_leak', []):
            f.setdefault('source', 'background_leak')
            all_hits.append(f)

        tp2 = term_pronoun.detect(text, section=args.section,
                                  term_lock=term_tokens if term_tokens else None)
        for f in tp2.get('flags_term_repeat', []):
            f.setdefault('source', 'term_pronoun')
            all_hits.append(f)

        uc = unprepared_concept.detect(text, section=args.section)
        for f in uc.get('flags_unprepared', []) + uc.get('flags_step_ref', []):
            f.setdefault('source', 'unprepared_concept')
            all_hits.append(f)

        ps = param_segment.detect(text, section=args.section)
        for f in ps.get('flags_param_mixed', []) + ps.get('flags_bracket_leak', []):
            f.setdefault('source', 'param_segment')
            all_hits.append(f)

        ms = merge_short.detect(text, section=args.section)
        for f in ms.get('flags_merge_pair', []) + ms.get('flags_over_segmented', []):
            f.setdefault('source', 'merge_short')
            all_hits.append(f)

    # Reader-pass validated flags (veto power when --reader-validated given).
    # Guarded behind --enable-skeleton: reader flags use skeletal category
    # and the 'skeletal' breakdown key / issues group only exist when the
    # Skeletal subsystem is enabled. Without this guard, reader flags would
    # contribute to all_hits but silently vanish from both score and report.
    if args.reader_validated and args.enable_skeleton:
        reader_data = json.loads(
            Path(args.reader_validated).read_text(encoding='utf-8'))
        for f in reader_data.get('flags', []):
            f.setdefault('category', 'skeletal')
            f.setdefault('weight', 10)
            f.setdefault('source', 'reader_pass')
            all_hits.append(f)
    elif args.reader_validated and not args.enable_skeleton:
        sys.stderr.write(
            'WARN: --reader-validated requires --enable-skeleton; '
            'reader flags ignored.\n')

    score_obj = compute_score(all_hits, enable_skeletal=args.enable_skeleton,
                              enable_sentential=args.enable_sentential,
                              enable_rhetorical=args.enable_rhetorical)
    action = decide_action(score_obj, all_hits,
                           enable_skeletal=args.enable_skeleton,
                           section=args.section)

    # Group issues by category for report. `skeletal` key appears only
    # when --enable-skeleton is on, to preserve v1.2 JSON shape.
    grouped = {'critical': [], 'high': [], 'medium': [], 'style': [],
               'patent': [], 'tier1': [], 'tier2': [], 'tier3': []}
    if args.enable_skeleton:
        grouped['skeletal'] = []
    if args.enable_sentential:
        grouped['sentential'] = []
    if args.enable_rhetorical:
        grouped['rhetorical'] = []
    for h in all_hits:
        cat = h.get('category', '')
        tier = h.get('tier')
        if tier == 1:
            grouped['tier1'].append(h)
        elif tier == 2:
            grouped['tier2'].append(h)
        elif tier == 3:
            grouped['tier3'].append(h)
        elif cat in grouped:
            grouped[cat].append(h)

    # Protected paragraphs
    protected = []
    for i, p in enumerate(paragraphs):
        is_p, reason = is_protected(p)
        if is_p:
            protected.append({'index': i, 'reason': reason,
                              'text_preview': p[:30] + '...'})

    report = {
        'score': score_obj['score'],
        'level': score_obj['level'],
        'breakdown': score_obj['breakdown'],
        'recommendation': action,
        'paragraph_count': len(paragraphs),
        'character_count': len(text),
        'protected_paragraphs': protected,
        'issues': grouped,
    }

    output_json = json.dumps(report, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(output_json, encoding='utf-8')
        print(f'Report saved to {args.output}')
        print(f'Score: {score_obj["score"]} ({score_obj["level"]})')
        print(f'Action: {action["action"]} - {action["reason"]}')
    else:
        print(output_json)


if __name__ == '__main__':
    main()
