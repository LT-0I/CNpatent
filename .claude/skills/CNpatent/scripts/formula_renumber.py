"""Global formula renumbering for CNpatent Phase 3 (safety net for Issue 3).

Writer-C and Writer-D run in parallel during Phase 1. The orchestrator pre-
allocates formula ranges (e.g. Writer-C uses (1)-(10), Writer-D from (11)),
but LLM Writers can ignore soft constraints. 2026-04-15 testing found both
Writers starting from (1), producing duplicates in the merged file.

This module is Phase 3's deterministic safety net. It walks the merged section
file, collects formula definitions in first-appearance order, and rewrites
them as (1), (2), (3)... regardless of what the Writers emitted. References
(式（N）/ 公式（N）) are renumbered consistently.

Two-phase placeholder substitution prevents chain-replacement bugs.

Usage (Python):
    from formula_renumber import renumber_formulas_in_file
    report = renumber_formulas_in_file(Path("sections/6_implementation.md"))

Usage (CLI):
    python -X utf8 formula_renumber.py sections/6_implementation.md
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

_PAREN_N = re.compile(r"\uff08(\d+)\uff09")
_REF = re.compile(r"(\u516c\u5f0f|\u5f0f)\uff08(\d+)\uff09")


@dataclass
class RenumberReport:
    path: Path
    old_to_new: Dict[int, int] = field(default_factory=dict)
    definition_count: int = 0
    reference_count: int = 0
    changed: bool = False

    def __str__(self) -> str:
        if self.definition_count == 0:
            return f"{self.path}: no formula definitions found"
        if not self.changed:
            return (
                f"{self.path}: already correct "
                f"({self.definition_count} defs, {self.reference_count} refs)"
            )
        pairs = ", ".join(
            f"({old})->({new})"
            for old, new in self.old_to_new.items()
            if old != new
        )
        return (
            f"{self.path}: renumbered "
            f"({self.definition_count} defs, {self.reference_count} refs) [{pairs}]"
        )


def _is_reference(text: str, pos: int) -> bool:
    if pos < 1:
        return False
    return text[pos - 1] == "\u5f0f"


def _find_definition_order(text: str) -> List[int]:
    seen: List[int] = []
    seen_set: set = set()
    for match in _PAREN_N.finditer(text):
        if _is_reference(text, match.start()):
            continue
        num = int(match.group(1))
        if num not in seen_set:
            seen.append(num)
            seen_set.add(num)
    return seen


def renumber_formulas_in_file(path: Path) -> RenumberReport:
    path = Path(path)
    text = path.read_text(encoding="utf-8")

    order = _find_definition_order(text)
    def_count = len(order)
    ref_count = len(_REF.findall(text))
    report = RenumberReport(
        path=path, definition_count=def_count, reference_count=ref_count,
    )

    if def_count == 0:
        return report

    old_to_new: Dict[int, int] = {
        old: new for new, old in enumerate(order, start=1)
    }
    report.old_to_new = old_to_new

    if all(old == new for old, new in old_to_new.items()):
        return report

    # Phase A: definitions -> placeholders (skip references)
    def a_sub(match: re.Match) -> str:
        if _is_reference(text, match.start()):
            return match.group(0)
        num = int(match.group(1))
        return f"__FDEF_{num}__"

    stage_a = _PAREN_N.sub(a_sub, text)

    # Phase B: references -> placeholders (preserve prefix word)
    def b_sub(match: re.Match) -> str:
        prefix_word = match.group(1)
        num = int(match.group(2))
        return f"{prefix_word}__FREF_{num}__"

    stage_b = _REF.sub(b_sub, stage_a)

    # Phase C: placeholders -> new numbers
    def c_def(match: re.Match) -> str:
        old = int(match.group(1))
        return f"\uff08{old_to_new[old]}\uff09"

    def c_ref(match: re.Match) -> str:
        old = int(match.group(1))
        new = old_to_new.get(old, old)
        return f"\uff08{new}\uff09"

    stage_c = re.sub(r"__FDEF_(\d+)__", c_def, stage_b)
    stage_d = re.sub(r"__FREF_(\d+)__", c_ref, stage_c)

    path.write_text(stage_d, encoding="utf-8")
    report.changed = True
    return report


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python -X utf8 formula_renumber.py <file.md> [...]",
              file=sys.stderr)
        sys.exit(2)
    for arg in sys.argv[1:]:
        print(renumber_formulas_in_file(Path(arg)))
