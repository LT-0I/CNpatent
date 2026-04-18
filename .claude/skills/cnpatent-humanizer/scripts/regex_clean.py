#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cnpatent-humanizer regex cleanup script (Step 9 of the 9-step pipeline).

Hard-coded regex replacements as the final fallback. Compatible with
cnpatent's `final_deai_cleanup()` but adds patent-specific patches.

Use this AFTER the LLM has done semantic rewriting. This is a safety net,
not the main rewrite mechanism.

Usage:
    PYTHONUTF8=1 python -X utf8 regex_clean.py \\
        --input draft.txt \\
        --output cleaned.txt
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


# Protected legal-statement prefixes — paragraphs starting with these are
# left completely untouched.
PROTECTED_PREFIXES = [
    '为了更清楚地说明本发明实施例',
    '构成本申请的一部分的附图',
    '现详细说明本发明的多种示例性实施方式',
    '应理解本发明中所述的术语',
    '在不背离本发明的范围或精神',
    '关于本文中所使用的',
    '需要说明的是，在不冲突的情况下',
    '以上所述，仅为本申请较佳的具体实施方式',
]


# Replacement rules. Each entry is (regex_pattern, replacement, description).
# Order matters: longer patterns first to avoid sub-string conflicts.
REPLACEMENTS: List[Tuple[str, str, str]] = [
    # ────── 推销/夸大类 ──────
    (r'显著(?:提升|提高|改善)', '提高', '显著X→提高'),
    (r'大幅(?:提升|提高)', '提高', '大幅X→提高'),
    (r'大幅降低', '降低', '大幅降低→降低'),
    (r'极大(?:提升|提高)', '提高', '极大X→提高'),
    (r'(?:颠覆|革命|突破|划时代|开创)性(?:地|的)?', '', '颠覆性地/的→删'),
    (r'(?:巧妙|精妙|独创)(?:地|的)?', '', '巧妙地/的→删'),
    (r'(?:卓越|优异|出色)的', '较高的', '卓越的→较高的'),
    (r'高效地?', '', '高效地→删'),
    (r'精准地?', '', '精准地→删'),
    (r'具有广阔的应用前景', '', '广阔前景→删'),
    (r'意义深远', '', '意义深远→删'),
    (r'完美(?:解决|实现)', lambda m: m.group(0).replace('完美', ''), '完美X→X'),
    (r'创新性地', '', '创新性地→删'),

    # ────── 过渡填充词 ──────
    (r'值得注意的是[，,]?', '', '值得注意的是→删'),
    (r'需要(?:指出|强调|说明)的是[，,]?', '', '需要X的是→删'),
    (r'值得一提的是[，,]?', '', '值得一提→删'),
    (r'至关重要', '', '至关重要→删'),
    (r'尤为关键', '关键', '尤为关键→关键'),
    (r'(?<![\u4e00-\u9fa5])旨在', '用于', '旨在→用于'),
    (r'致力于', '', '致力于→删'),
    (r'得益于', '基于', '得益于→基于'),
    (r'(?:有)?鉴于此[，,]?', '', '鉴于此→删'),
    (r'综上所述[，,]?', '', '综上所述→删'),
    (r'总而言之[，,]?', '', '总而言之→删'),
    (r'^总之[，,]', '', '总之→删（仅段首）'),
    (r'毋庸置疑[，,]?', '', '毋庸置疑→删'),
    (r'不言而喻[，,]?', '', '不言而喻→删'),
    (r'在此基础上[，,]?', '', '在此基础上→删'),
    (r'从本质上讲[，,]?', '', '从本质上讲→删'),
    (r'从根本上说[，,]?', '', '从根本上说→删'),
    (r'充分利用', '利用', '充分利用→利用'),
    (r'充分考虑', '考虑', '充分考虑→考虑'),

    # ────── 排比连接词（仅段首） ──────
    (r'^首先[，,]?', '', '首先→删（仅段首）'),
    (r'^其次[，,]?', '', '其次→删（仅段首）'),
    (r'^然后[，,]?', '', '然后→删（仅段首）'),
    (r'^最后[，,]?', '', '最后→删（仅段首）'),
    (r'其一[，,]', '', '其一→删'),
    (r'其二[，,]', '', '其二→删'),
    (r'其三[，,]', '', '其三→删'),

    # ────── AI 高频结构 ──────
    (r'进一步地[，,]?', '', '进一步地→删'),
    (r'更为重要的是[，,]?', '', '更为重要的是→删'),
    (r'具体来说[，,]?', '', '具体来说→删'),
    (r'具体而言[，,]?', '', '具体而言→删'),
    (r'与此同时[，,]?', '', '与此同时→删'),
    (r'由此可以看出[，,]?', '', '由此可以看出→删'),
    (r'(?<![\u4e00-\u9fa5])事实上[，,]?', '', '事实上→删'),
    (r'(?<![\u4e00-\u9fa5])实际上[，,]?', '', '实际上→删'),
    (r'换言之[，,]?', '', '换言之→删'),
    (r'换句话说[，,]?', '', '换句话说→删'),
    (r'不难发现[，,]?', '', '不难发现→删'),
    (r'由此可见[，,]?', '', '由此可见→删'),

    # ────── 学术腔（注意：法律段已在段落级被保护，此处只做 lookahead 防误伤） ──────
    (r'本文(?!中所使用的)', '本发明', '本文→本发明（法律段已段级保护）'),
    (r'实验结果表明[，,]?', '', '实验结果表明→删'),
    (r'研究(?:发现|表明)[，,]?', '', '研究发现/表明→删'),
    (r'(?<![\u4e00-\u9fa5])我们提出', '本发明提供', '我们提出→本发明提供'),
    (r'(?<![\u4e00-\u9fa5])我们(?![\u4e00-\u9fa5]?(?:可以|能))', '本发明',
     '我们→本发明'),
    (r'(?<![\u4e00-\u9fa5])笔者', '', '笔者→删'),

    # ────── 中文独有：动词名词化 ──────
    (r'(?<![\u4e00-\u9fa5])进行预处理', '预处理', 'X化处理修正'),
    (r'(?<![\u4e00-\u9fa5])进行训练', '训练', 'X化处理修正'),
    (r'(?<![\u4e00-\u9fa5])进行(?:特征)?提取', '提取', 'X化处理修正'),
    (r'(?<![\u4e00-\u9fa5])进行(?:数据)?处理', '处理', 'X化处理修正'),
    (r'(?<![\u4e00-\u9fa5])做出判断', '判断', '做出判断→判断'),
    (r'(?<![\u4e00-\u9fa5])做出选择', '选择', '做出选择→选择'),
    (r'([\u4e00-\u9fa5])化处理', r'\1化', 'X化处理→X化'),

    # ────── 中英标点混用 ──────
    (r'([\u4e00-\u9fa5]),(?=\s|[\u4e00-\u9fa5])', r'\1，', '中英逗号混用'),
    (r'([\u4e00-\u9fa5]);(?=\s|[\u4e00-\u9fa5])', r'\1；', '中英分号混用'),
    (r'([\u4e00-\u9fa5]):(?=\s|[\u4e00-\u9fa5])', r'\1：', '中英冒号混用'),
    (r'([\u4e00-\u9fa5])\((?=[\u4e00-\u9fa5])', r'\1（', '中英括号混用'),
    (r'([\u4e00-\u9fa5])\)(?=\s|[\u4e00-\u9fa5]|$)', r'\1）', '中英括号混用'),

    # ────── 副词堆叠（保守） ──────
    (r'非常的?显著', '', '副词堆叠'),

    # ────── 比较级模糊（保守） ──────
    (r'(?<![\u4e00-\u9fa5])更(?:好|高|快|强|准)的(?=[\u4e00-\u9fa5])', '',
     '更X的→删（保守）'),

    # ────── v1.4 Tier 1.6 发明八股句（整句删除） ──────
    (r'本发明的目的是提供[，,]?', '', 'H6 本发明的目的是提供→删'),
    (r'本发明的优势体现[在如][下：:][，,]?', '', 'H6 本发明的优势体现→删'),
    (r'本发明的技术效果为[，,：:]?', '', 'H6 本发明的技术效果为→删'),
    (r'相比现有技术具有(?:以下)?(?:技术效果|优势)[，,：:]?', '',
     'H6 相比现有技术具有→删'),
    (r'本步骤为本发明的核心技术创新所在[，,。]?', '', 'H6 本步骤核心创新→删'),
    (r'本方案.{0,6}必要性.{0,6}具有[必要性]*[，,。]?', '', 'H6 必要性→删'),
    (r'本方案.{0,6}收敛性.{0,12}支撑[，,。]?', '', 'H6 收敛性→删'),
    (r'本方案.{0,6}效果.{0,6}消融.{0,6}佐证[，,。]?', '', 'H6 效果佐证→删'),

    # ────── v1.4 Tier 1.7 强调副词（紧跟技术名词时删） ──────
    (r'持续(?=[追更新校修扩累生覆识输发])', '', 'H9 持续X→X'),
    (r'严重(?=[不影降损制误])', '', 'H9 严重X→X'),
    (r'固有(?:的)?(?=[问缺风特局振])', '', 'H9 固有→删'),
    (r'(?<![\u4e00-\u9fa5])根本(?=[上地])', '', 'H9 根本上/地→删'),
    (r'专门(?=[技设处方针])', '', 'H9 专门X→X'),
    (r'有机(?=[组结])', '', 'H9 有机组成/结合→删'),
    # 整体/全局：保留"全局坐标系"等术语，删"全局残余偏差"类修饰
    (r'整体(?=[重修改])', '', 'H9 整体重写/修改→删'),

    # ────── v1.4 Tier 1.8 风格标签动词（替换为平实动词） ──────
    (r'锚定在', '依据', 'H13 锚定在→依据'),
    (r'(?<![\u4e00-\u9fa5])锚定(?=[\u4e00-\u9fa5])', '依据', 'H13 锚定→依据'),
    (r'降维为', '简化为', 'H13 降维为→简化为'),
    (r'(?<![\u4e00-\u9fa5])降维(?=[\u4e00-\u9fa5])', '简化', 'H13 降维→简化'),
    (r'阻尼注入', '阻尼施加', 'H13 阻尼注入→阻尼施加'),
    (r'退化兜底', '退化处理', 'H13 退化兜底→退化处理'),
    (r'(?<![\u4e00-\u9fa5])兜底(?=[\u4e00-\u9fa5])', '保底', 'H13 兜底→保底'),
    (r'自举闭环', '相互校正闭环', 'H13 自举闭环→相互校正闭环'),
    (r'同根验证源', '同源验证', 'H13 同根验证源→同源验证'),
    (r'(?<![\u4e00-\u9fa5])同根(?![验\u4e00-\u9fa5])', '同源', 'H13 同根→同源'),
    (r'落于同一参数集合', '属于同一参数集合', 'H13 落于→属于'),
    (r'共同形成', '形成', 'H13 共同形成→形成'),
    (r'(?<![\u4e00-\u9fa5])由此打破', '打破', 'H13 由此打破→打破'),
    (r'(?<![\u4e00-\u9fa5])由此构成', '构成', 'H13 由此构成→构成'),
    (r'施加分布式反向修正', '做分布式反向修正', 'H13 施加修正→做修正'),
    (r'予以限制', '限制', 'H13 予以限制→限制'),

    # ────── v1.4 H8 被动书面化 ──────
    (r'对([\u4e00-\u9fa5]{1,15})施加([\u4e00-\u9fa5]{1,10})',
     lambda m: f'{m.group(2)}{m.group(1)}', 'H8 对X施加Y→YX'),
    (r'由([\u4e00-\u9fa5]{1,15})予以([\u4e00-\u9fa5]{1,10})',
     lambda m: f'{m.group(1)}{m.group(2)}', 'H8 由X予以Y→XY'),
    (r'以([\u4e00-\u9fa5]{0,10})方式对', r'以\1对', 'H8 以X方式对→以X对'),

    # ────── v1.5 Rule 1 破折号列举引导 ──────
    # "亦有成熟应用——X；Y；Z。" → "亦有成熟应用：X；Y；Z。"
    (r'——(?=[\u4e00-\u9fa5]{3,}[；;，,])', '：',
     'R1 破折号列举引导符→：'),

    # ────── v1.5 Rule 5 / 10 "为解决...问题，" 类导语整句删除 ──────
    (r'为解决上述[^，。；]{0,20}问题[，,]', '', 'R5 为解决上述X问题，→删'),
    (r'为解决该问题[，,]', '', 'R5 为解决该问题，→删'),
    (r'为解决[^，。；]{0,30}问题[，,]', '', 'R5 为解决X问题，→删'),
    (r'^为此[，,]', '', 'R5 ^为此，→删（段首）'),
    (r'。\s*为此[，,]', '。', 'R5 。为此，→。（句末）'),
    (r'针对[^，。；]{0,20}[，,]\s*本步骤', '', 'R5 针对X，本步骤→删前缀'),

    # ────── v1.5 Rule 12 "本步骤" 元话语删除 ──────
    (r'本步骤(利用|通过|将|引入|采用|根据|借助)', r'\1',
     'R12 本步骤+动词→删本步骤'),
    (r'本步骤为本发明的?核心技术创新所在[，,。]?', '',
     'R12 本步骤核心创新→删'),
    (r'本实施例(定义|采用|利用)', r'\1',
     'R12 本实施例+动词→动词'),

    # ────── v1.5 Rule 9 空洞元描述删除 ──────
    (r'其中步骤[（(]\d+[）)][^。]{0,10}至步骤[（(]\d+[）)][^。]{0,30}链路[。]?',
     '', 'R9 构成...链路→删'),
    (r'本(方法|发明|实施例)相比[^。]{0,30}取得以下(?:技术)?效果[。：:]?', '',
     'R9 本X相比Y取得以下效果→删'),
    (r'^具体操作步骤如下[。：:]?\s*$', '',
     'R9 具体操作步骤如下。→删（独立段）'),
    (r'本实施例定义[^。]{0,20}[：:]', '',
     'R9 本实施例定义X种：→删'),

    # ────── v1.5 Rule 14 "将 X，获得 Y" 翻译腔 ──────
    # 常见变体："将 X [动介] Y，获得/得到/取得/产出 Z"
    (r'将([^，。；]{3,40})(至|到)([^，。；]{2,20})[，,]\s*(获得|得到|取得|产出)',
     lambda m: f'对{m.group(1)}做投影{m.group(2)}{m.group(3)}后{m.group(4)}',
     'R14 将X至Y，获得Z→对X做投影至Y后，得到Z'),

    # ────── v1.5 Rule 11 话题切换标志词缀（发明目的子项标题前缀删除）──────
    # 段首 "架构方面，" / "观测方面，" 等，仅当不是子项正文时保留
    # 保守策略：发现段首这类标志词时，标注但不自动删（交给 LLM / reader pass）
    # 此处不做 regex 替换，通过 topic_switch.py 生成 flag

    # ────── v1.5 Rule 8 长术语段内代词化（由 term_pronoun.py 检测，regex 仅对超高频术语做首次自动替换）──────
    # 保守：不做自动替换（避免破坏术语锁定）；交给 LLM pass
]


def is_protected_paragraph(paragraph: str) -> bool:
    """Check if paragraph starts with any protected legal prefix."""
    p = paragraph.strip()
    for prefix in PROTECTED_PREFIXES:
        if p.startswith(prefix):
            return True
    # Also protect heading paragraphs
    if re.match(r'^[一二三四五六七]、', p):
        return True
    if p in ('发明目的', '技术解决方案'):
        return True
    if re.match(r'^3、技术效果', p):
        return True
    # Protect formula paragraphs
    if re.search(r'\$[^$]+\$|\\frac|\\sum|\\int', p):
        return True
    # Protect figure description lines
    if re.match(r'^图\s*\d+\s*[，,]?\s*为本发明', p):
        return True
    return False


def clean_paragraph(text: str) -> Tuple[str, List[str]]:
    """Apply all regex replacements to a single paragraph."""
    applied = []
    cleaned = text
    for pattern, repl, desc in REPLACEMENTS:
        if re.search(pattern, cleaned):
            old = cleaned
            if callable(repl):
                cleaned = re.sub(pattern, repl, cleaned)
            else:
                cleaned = re.sub(pattern, repl, cleaned, flags=re.MULTILINE)
            if old != cleaned:
                applied.append(desc)

    # Cleanup: collapse multiple commas/spaces produced by deletions
    cleaned = re.sub(r'[，,]{2,}', '，', cleaned)
    cleaned = re.sub(r'^[，,。]+', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'[，,]([。；！？])', r'\1', cleaned)
    cleaned = re.sub(r'[ \t]{2,}', ' ', cleaned)

    return cleaned, applied


def clean_text(text: str) -> Tuple[str, List[Tuple[int, str, List[str]]]]:
    """Clean entire text, paragraph by paragraph, respecting protections."""
    paragraphs = text.split('\n')
    output_paragraphs = []
    change_log = []

    for i, p in enumerate(paragraphs):
        if not p.strip():
            output_paragraphs.append(p)
            continue
        if is_protected_paragraph(p):
            output_paragraphs.append(p)
            continue
        cleaned, applied = clean_paragraph(p)
        output_paragraphs.append(cleaned)
        if applied:
            change_log.append((i, p[:30] + '...', applied))

    return '\n'.join(output_paragraphs), change_log


def main():
    parser = argparse.ArgumentParser(
        description='cnpatent-humanizer regex cleanup (Step 9)')
    parser.add_argument('--input', required=True, help='Input text file')
    parser.add_argument('--output', required=True, help='Output text file')
    parser.add_argument('--changelog', default=None,
                        help='Optional changelog file path')
    args = parser.parse_args()

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    text = Path(args.input).read_text(encoding='utf-8')
    cleaned, change_log = clean_text(text)
    Path(args.output).write_text(cleaned, encoding='utf-8')

    print(f'Cleaned text saved to {args.output}')
    print(f'Modified {len(change_log)} paragraphs')

    if args.changelog:
        log_lines = []
        for idx, preview, applied in change_log:
            log_lines.append(f'§{idx}: {preview}')
            for a in applied:
                log_lines.append(f'   - {a}')
        Path(args.changelog).write_text('\n'.join(log_lines), encoding='utf-8')
        print(f'Changelog saved to {args.changelog}')


if __name__ == '__main__':
    main()
