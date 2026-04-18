#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
reader_pass.py — Reader-view LLM evaluation wiring + post-hoc citation guard.

This script has NO LLM SDK dependency. It only:
  1. Generates a section-parameterized reader-view prompt text file that
     an orchestrator can feed to the `humanizer-reader` agent.
  2. Validates the JSON response from that agent by re-checking every
     citation.substring literally against the original text; drops
     fabricated citations and drops flags whose surviving citations
     fall below the minimum (default 2).

This is Phase 4.5 of the cnpatent-humanizer pipeline (spec.md Task D5).
The reader agent sees ONLY the rewritten text + section label — no
audit scores, no Tier hits, no term-lock — to preserve an independent
yardstick.

Two modes (`--mode`):

  prompt    Read input Chinese text, emit the reader-view prompt as .txt.
            Used before calling the humanizer-reader agent.

  validate  Read a JSON file (reader's response) + original text.
            Run post-hoc regex validation on every citation.substring;
            drop citations not found literally in the text;
            drop flags with fewer than `--min-citations` surviving
            citations; tag surviving flags with
            category='skeletal', weight=10, source='reader_pass'.
            Output validated flags + summary.

Example orchestration:

  PYTHONUTF8=1 python -X utf8 reader_pass.py --mode prompt \\
      --input 4c_effect.md --section 四 \\
      --prompt-out reader_prompt.txt

  # orchestrator sends reader_prompt.txt to humanizer-reader agent,
  # saves response as reader_response.json

  PYTHONUTF8=1 python -X utf8 reader_pass.py --mode validate \\
      --input reader_response.json --text 4c_effect.md \\
      --output validated.json

Validation output JSON schema:
  {
    "flags": [ ... surviving flags with category/weight/source added ... ],
    "dropped_flag_count": N,
    "dropped_citation_count": N,
    "validated": true
  }

No external dependencies — stdlib only.
"""

import argparse
import json
import sys
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────
# Section label lookup
# ─────────────────────────────────────────────────────────────────────────
SECTION_NAMES = {
    '一': '发明名称 (一、)',
    '二': '技术领域 (二、)',
    '三': '背景技术 (三、)',
    '四': '发明内容 (四、)',
    '五': '附图说明 (五、)',
    '六': '具体实施方式 (六、)',
    'all': '完整文档',
}


# ─────────────────────────────────────────────────────────────────────────
# Prompt template (section-parameterized)
# ─────────────────────────────────────────────────────────────────────────
PROMPT_TEMPLATE = """你正在审阅一份中国发明专利技术交底书的{section_name}部分。
作为资深专利工程师/审查员，请把下文当作一位同行代理人写的初稿阅读，
而不是作为格式检查器。

只关注修辞与结构层面，不改动内容，不提出技术建议。如果发现下列问题之一，
请用 JSON 数组输出 flag。每个 flag 必须同时包含:
  - pattern_template: 骨架模板引用 (如 "[状语前置]+[主语]+[否定/情态]+[动词]+[：机制]+[；数据]")
  - description: 一句中文描述问题
  - citations: 至少 2 个引用，每个含 item_ref (如 "（1）") 和 substring (从原文逐字摘取的一段，至少 8 字，用于事后校验)

需要识别的问题类型:
1. 兄弟条目修辞骨架重复 — 每条都按同一模板展开 (句首状语/主语/动词/分隔符/补语位置一致)
2. 信息密度均匀 — 每条都同时填满 {{机制, 量化数据, 对比基线, caveat}} 多个槽位
3. 论证完备度过高 — 每个主张都同时给出机制+数据+基线比较
4. 否定/情态并行 — 多条使用 [否定副词]+[情态]+[动词] 同一结构
5. 段首同类状语堆积 — 连续多条以「X下/X中/X之外」开头

如果没有发现骨架级问题，输出空数组 []。
不要评论内容对错、不要改写、不要建议，只识别骨架。

<section_name>{section_name}</section_name>
<text>
{text}
</text>
"""


# ─────────────────────────────────────────────────────────────────────────
# Prompt mode
# ─────────────────────────────────────────────────────────────────────────
def build_prompt(text: str, section: str) -> str:
    """Render the reader-view prompt with section label + text body."""
    section_name = SECTION_NAMES.get(section, SECTION_NAMES['all'])
    return PROMPT_TEMPLATE.format(section_name=section_name, text=text)


# ─────────────────────────────────────────────────────────────────────────
# Validate mode
# ─────────────────────────────────────────────────────────────────────────
def validate_flags(flags, text, min_citations=2):
    """Drop citations whose substring is not literally in text.
    Drop flags whose surviving citation count < min_citations.
    Tag surviving flags with category/weight/source.
    Return (surviving_flags, dropped_flag_count, dropped_citation_count).
    """
    surviving = []
    dropped_flag_count = 0
    dropped_citation_count = 0

    if not isinstance(flags, list):
        return [], 0, 0

    for flag in flags:
        if not isinstance(flag, dict):
            dropped_flag_count += 1
            continue
        citations = flag.get('citations', [])
        if not isinstance(citations, list):
            dropped_flag_count += 1
            continue

        kept_citations = []
        for cit in citations:
            if not isinstance(cit, dict):
                dropped_citation_count += 1
                continue
            substring = cit.get('substring', '')
            if not isinstance(substring, str) or len(substring) < 1:
                dropped_citation_count += 1
                continue
            # post-hoc hallucination guard: substring must exist literally
            if substring in text:
                kept_citations.append(cit)
            else:
                dropped_citation_count += 1

        if len(kept_citations) < min_citations:
            dropped_flag_count += 1
            continue

        validated = dict(flag)
        validated['citations'] = kept_citations
        validated['category'] = 'skeletal'
        validated['weight'] = 10
        validated['source'] = 'reader_pass'
        surviving.append(validated)

    return surviving, dropped_flag_count, dropped_citation_count


def load_reader_response(path: Path):
    """Read reader JSON; accept either a bare list or an object with
    a top-level 'flags' key. Returns the list of flags.
    """
    raw = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        flags = raw.get('flags', [])
        if isinstance(flags, list):
            return flags
    return []


# ─────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description='Reader-view prompt generator + post-hoc citation guard')
    parser.add_argument('--mode', required=True, choices=['prompt', 'validate'])
    parser.add_argument('--input', required=True,
                        help='prompt mode: original text file; '
                             'validate mode: reader response JSON file')
    parser.add_argument('--section', default='all',
                        help='Section context (一/二/三/四/五/六/all)')
    parser.add_argument('--prompt-out', default=None,
                        help='prompt mode: output .txt path')
    parser.add_argument('--text', default=None,
                        help='validate mode: path to the original Chinese '
                             'text used for citation substring check')
    parser.add_argument('--output', default=None,
                        help='validate mode: output JSON path')
    parser.add_argument('--min-citations', type=int, default=2,
                        help='validate mode: minimum surviving citations '
                             'required to keep a flag (default 2)')
    args = parser.parse_args()

    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    if args.mode == 'prompt':
        text = Path(args.input).read_text(encoding='utf-8')
        prompt = build_prompt(text, args.section)
        if args.prompt_out:
            Path(args.prompt_out).write_text(prompt, encoding='utf-8')
            print(f'reader_pass prompt → {args.prompt_out}')
            print(f'  section={args.section} chars={len(text)}')
        else:
            print(prompt)
        return

    # validate mode
    if not args.text:
        sys.stderr.write('ERROR: --text is required in validate mode\n')
        sys.exit(2)
    text = Path(args.text).read_text(encoding='utf-8')
    flags = load_reader_response(Path(args.input))
    surviving, dropped_flags, dropped_cits = validate_flags(
        flags, text, min_citations=args.min_citations)

    result = {
        'flags': surviving,
        'dropped_flag_count': dropped_flags,
        'dropped_citation_count': dropped_cits,
        'validated': True,
    }
    out = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(out, encoding='utf-8')
        print(f'reader_pass validated → {args.output}')
        print(f'  surviving_flags={len(surviving)} '
              f'dropped_flags={dropped_flags} '
              f'dropped_citations={dropped_cits}')
    else:
        print(out)


if __name__ == '__main__':
    main()
