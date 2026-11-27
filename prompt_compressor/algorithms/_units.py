"""
Shared core for the 'medium' steps (same rules as the JS package).

Every medium step works on "units" (sentences / lines) and only ever REMOVES
units it has positively chosen to drop. Everything else, including short
units, line breaks and paragraph breaks, is kept as-is.

Never dropped:
  - anything inside ``` fenced blocks
  - structured lines: lists, headings, tables, quotes, "Key: value", JSON-ish,
    log lines starting with a date (chat lines "User: ..." count as prose)
  - "critical" units: rules, numbers, IDs, variables, emails, URLs, code
  - "task" units: questions, direct requests, word-based deadlines
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, List, Sequence

UNIT_SPLIT = re.compile(r"((?<=[.!?])[ \t]+|[ \t]*\n\s*)")
SPEAKER = re.compile(r"^\s*(?:user|assistant|human|ai|system|customer|agent|bot)\s*:", re.I)
STRUCTURED_RE = re.compile(r"""^\s*(?:[-*+•>|#]|\d+[.)]\s|[\[{"'`]|[A-Za-z][\w .'-]{0,30}:\s|\d{4}-\d{2}-\d{2})""")
CRITICAL = re.compile(
    r"\d|\{\{?|\$\{|%\w+%|@|https?://|`|\x00|\b(?:must|never|always|only|not|don't|do not|cannot|can't|"
    r"required?|forbidden|no later than|deadline|exactly|at least|at most)\b",
    re.I,
)
TASK = re.compile(
    r"\?\s*$|\b(?:could|can|would|will) you\b|\b(?:today|tomorrow|tonight|by (?:the )?end of|eod|eow|asap|due|"
    r"by (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b",
    re.I,
)
NUM_SIG = re.compile(r"[\w-]*\d[\w./-]*")
FENCE = re.compile(r"(```[\s\S]*?```)")
# Lines that look like code or JSON legitimately repeat ("}", "qty": 1, return x;)
CODE_LIKE_LINE = re.compile(r"""^[\s\[\]{}(),;:"'`]*$|^\s*"[^"]*"\s*:|[{\[,;]\s*$|^\s*(?:return|break|continue|end|fi|done|else)\b""")


def is_structured(line: str) -> bool:
    return not SPEAKER.match(line) and bool(STRUCTURED_RE.match(line))


@dataclass
class Unit:
    text: str
    sep_before: str
    line: str


def parse_units(text: str) -> List[Unit]:
    parts = UNIT_SPLIT.split(text)
    units: List[Unit] = []
    line = ""
    for i in range(0, len(parts), 2):
        sep = "" if i == 0 else parts[i - 1]
        if i == 0 or "\n" in sep:
            j, l = i, parts[i]
            while j + 2 < len(parts) and "\n" not in parts[j + 1]:
                l += parts[j + 1] + parts[j + 2]
                j += 2
            line = l
        units.append(Unit(parts[i], sep, line))
    return units


def rebuild(units: Sequence[Unit], keep: Sequence[bool]) -> str:
    out, pending = "", ""
    for u, k in zip(units, keep):
        sep = pending if pending.count("\n") > u.sep_before.count("\n") else u.sep_before
        if k:
            out += (sep if out else u.sep_before) + u.text
            pending = ""
        else:
            pending = sep
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def outside_fences(text: str, fn: Callable[[str], str]) -> str:
    out = []
    for p in FENCE.split(text):
        if p.startswith("```") or not p.strip():
            out.append(p)
            continue
        lead = re.match(r"^\s*", p).group(0)
        trail = re.search(r"\s*$", p).group(0)
        out.append(lead + fn(p.strip()) + trail)
    return "".join(out)


def is_protected(u: Unit) -> bool:
    return (not u.text.strip() or is_structured(u.line)
            or bool(CRITICAL.search(u.text)) or bool(TASK.search(u.text)))


def num_sig(s: str) -> str:
    return "|".join(NUM_SIG.findall(s))


def dedup_by(text: str, is_dup: Callable[[str, str], bool], min_len: int) -> str:
    def block_fn(block: str) -> str:
        units = parse_units(block)
        keep = [True] * len(units)
        seen: List[str] = []
        for i, u in enumerate(units):
            t = u.text.strip()
            if len(t) <= min_len or is_structured(u.line):
                continue
            if any(num_sig(k) == num_sig(t) and is_dup(k, t) for k in seen):
                keep[i] = False
            else:
                seen.append(t)
        return rebuild(units, keep)
    return outside_fences(text, block_fn)


def summarize_by(text: str, keep_ratio: float, score_fn: Callable[[List[str]], List[float]]) -> str:
    def block_fn(block: str) -> str:
        units = parse_units(block)
        cand = [i for i, u in enumerate(units) if not is_protected(u) and len(u.text.strip()) > 20]
        if len(cand) < 3:
            return block
        drop = int(len(cand) * (1 - keep_ratio))
        if drop <= 0:
            return block
        scores = score_fn([units[i].text for i in cand])
        dropped = {i for _, i in sorted(zip(scores, cand))[:drop]}
        return rebuild(units, [i not in dropped for i in range(len(units))])
    return outside_fences(text, block_fn)
