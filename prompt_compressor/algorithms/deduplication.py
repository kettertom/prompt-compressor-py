"""Deduplication algorithms — risk level: low / medium"""

import re
from collections import Counter
from typing import List

from ._units import CODE_LIKE_LINE, dedup_by, outside_fences


# ─── EXACT LINE DEDUPLICATION ────────────────────────────────────────────────

def dedup_exact_lines(text: str) -> str:
    """Remove consecutive duplicate lines. Never inside ``` blocks, and never
    lines that look like code/JSON (they legitimately repeat: "}", "qty": 1)."""
    def block_fn(block: str) -> str:
        lines = block.split("\n")
        result = [lines[0]] if lines else []
        for line in lines[1:]:
            if line.strip() and line == result[-1] and not CODE_LIKE_LINE.search(line):
                continue
            result.append(line)
        return "\n".join(result)
    return outside_fences(text, block_fn)


# ─── EXACT SENTENCE DEDUPLICATION ───────────────────────────────────────────

def dedup_exact_sentences(text: str) -> str:
    """Remove duplicate sentences (keep first occurrence). Never inside ``` blocks."""
    return outside_fences(text, _dedup_exact_sentences_block)


def _dedup_exact_sentences_block(text: str) -> str:
    # split but keep separators, so line breaks and paragraphs survive
    parts = re.split(r"((?<=[.!?])\s+)", text)
    seen = set()
    out = ""
    for i in range(0, len(parts), 2):
        sent, sep = parts[i], (parts[i + 1] if i + 1 < len(parts) else "")
        key = sent.strip().lower()
        if key not in seen:
            seen.add(key)
            out += sent + sep
        elif "\n" in sep and not re.search(r"\n\s*$", out):
            out = out.rstrip(" \t") + "\n"
    return re.sub(r"\n{3,}", "\n\n", out).strip()



# ─── FUZZY DEDUPLICATION (JACCARD) ──────────────────────────────────────────

def _tokenize(text: str) -> set:
    return set(re.findall(r"\b\w+\b", text.lower()))


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def dedup_fuzzy(text: str, threshold: float = 0.85) -> str:
    """Remove sentences that are >= threshold Jaccard similarity to a prior one.
    Keeps line structure; sentences that differ in numbers/IDs are never duplicates."""
    return dedup_by(text, lambda a, b: _jaccard(_tokenize(a), _tokenize(b)) >= threshold, 20)


# ─── N-GRAM SIMILARITY DEDUPLICATION ────────────────────────────────────────

def _ngrams(text: str, n: int = 3) -> set:
    words = re.findall(r"\b\w+\b", text.lower())
    return set(zip(*[words[i:] for i in range(n)])) if len(words) >= n else set()


def dedup_ngram(text: str, n: int = 3, threshold: float = 0.7) -> str:
    """Remove sentences with high n-gram overlap to prior sentences.
    Keeps line structure; numbers/IDs must match."""
    def dup(a: str, b: str) -> bool:
        ga, gb = _ngrams(a, n), _ngrams(b, n)
        return bool(ga and gb) and len(ga & gb) / len(ga | gb) >= threshold
    return dedup_by(text, dup, 15)


# ─── LEVENSHTEIN DEDUPLICATION ───────────────────────────────────────────────

def _levenshtein(a: str, b: str) -> int:
    """Classic Levenshtein distance."""
    if len(a) > len(b):
        a, b = b, a
    prev = list(range(len(a) + 1))
    for j, cb in enumerate(b):
        curr = [j + 1]
        for i, ca in enumerate(a):
            curr.append(min(prev[i + 1] + 1, curr[-1] + 1, prev[i] + (ca != cb)))
        prev = curr
    return prev[-1]


def dedup_levenshtein(text: str, threshold: float = 0.15) -> str:
    """
    Remove sentences whose normalized Levenshtein distance to a prior sentence
    is below threshold (i.e., very similar). threshold=0.15 means <=15% of
    characters differ. Keeps line structure; numbers/IDs must match.
    """
    def dup(a: str, b: str) -> bool:
        m = max(len(a), len(b))
        return m > 0 and _levenshtein(a[:200].lower(), b[:200].lower()) / m < threshold
    return dedup_by(text, dup, 20)


# ─── FREQUENT PATTERN MINING (APRIORI-STYLE) ────────────────────────────────

def remove_frequent_patterns(text: str, min_freq: int = 3, min_len: int = 20) -> str:
    """
    Find phrases (5-15 word n-grams) that repeat ≥ min_freq times
    and keep only the first occurrence.
    """
    words = re.findall(r"\S+", text)
    phrase_counts: Counter = Counter()

    for n in range(5, 16):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i:i + n])
            if len(phrase) >= min_len:
                phrase_counts[phrase] += 1

    # Sort longest first to avoid partial matches
    repeated = sorted(
        [p for p, c in phrase_counts.items() if c >= min_freq],
        key=len, reverse=True
    )

    for phrase in repeated:
        escaped = re.escape(phrase)
        # Keep first, remove subsequent
        occurrences = list(re.finditer(escaped, text))
        if len(occurrences) > 1:
            for m in reversed(occurrences[1:]):
                text = text[:m.start()] + text[m.end():]

    return text


# ─── TRIE PREFIX COMPRESSION ────────────────────────────────────────────────

def trie_prefix_compress(text: str) -> str:
    """
    Find lines that share long common prefixes and group them.
    E.g.:
        - The user should be able to login
        - The user should be able to logout
        - The user should be able to view
    → The user should be able to: login, logout, view
    """
    lines = text.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.startswith(("- ", "* ", "  - ")):
            result.append(lines[i])
            i += 1
            continue

        prefix_len = 4  # minimum common prefix word count
        words = line.split()
        # look ahead for siblings
        siblings = [line]
        j = i + 1
        while j < len(lines):
            next_line = lines[j].rstrip()
            if not next_line.startswith(("- ", "* ", "  - ")):
                break
            next_words = next_line.split()
            # find common prefix length
            common = 0
            for w1, w2 in zip(words, next_words):
                if w1 == w2:
                    common += 1
                else:
                    break
            if common >= prefix_len:
                siblings.append(next_line)
                j += 1
            else:
                break

        if len(siblings) >= 3:
            # Extract common prefix and suffixes
            first_words = siblings[0].split()
            # Recompute actual common prefix
            common = len(first_words)
            for sib in siblings[1:]:
                sib_words = sib.split()
                c = 0
                for w1, w2 in zip(first_words, sib_words):
                    if w1 == w2:
                        c += 1
                    else:
                        break
                common = min(common, c)
            if common >= prefix_len:
                bullet = "- " if siblings[0].startswith("- ") else "* "
                prefix_text = " ".join(first_words[:common])
                suffixes = [" ".join(sib.split()[common:]) for sib in siblings]
                suffixes = [s for s in suffixes if s]
                if suffixes:
                    result.append(f"{bullet}{prefix_text}: {', '.join(suffixes)}")
                    i = j
                    continue

        result.append(lines[i])
        i += 1

    return "\n".join(result)
