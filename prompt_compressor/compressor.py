"""
prompt_compressor — main entry point.

Levels:
  none      — whitespace, unicode, punctuation, ANSI (5–15%)
  very-low  — + filler, phrase shortening, license headers, indentation (15–30%)
  low       — + hedging, meta-commentary, transitions, parentheticals,
               number/date normalization, code comments, JSON/SQL minify,
               base64/hex stripping, stack traces, exact dedup (25–45%)
  medium    — + fuzzy/ngram/levenshtein dedup, frequent patterns, trie,
               TF-IDF, TextRank (30–70%)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, List, Optional

from .tokens import count_tokens
from .algorithms.protection import protect_variables, restore_variables
from .algorithms import structural, language, code, deduplication, extractive

Level = Literal["none", "very-low", "low", "medium"]

VALID_LEVELS: List[Level] = ["none", "very-low", "low", "medium"]


@dataclass
class CompressResult:
    output: str
    tokens_before: int
    tokens_after: int
    saved: int
    reduction_pct: float


def compress(
    text: str,
    level: Level = "low",
    protect_vars: bool = True,
) -> CompressResult:
    """
    Compress a prompt to the given risk level.

    Args:
        text:         The input prompt text.
        level:        Compression aggressiveness — 'none', 'very-low', 'low', 'medium'.
        protect_vars: If True, protect {{var}}, {var}, <tag>, ${var} from modification.

    Returns:
        CompressResult with output text and token statistics.
    """
    if level not in VALID_LEVELS:
        raise ValueError(f"level must be one of {VALID_LEVELS}, got {level!r}")

    tokens_before = count_tokens(text)

    # Protect variables before any processing
    mapping = {}
    if protect_vars:
        text, mapping = protect_variables(text)

    # ── NONE ────────────────────────────────────────────────────────────────
    text = structural.normalize_unicode(text)
    text = structural.strip_ansi(text)
    text = structural.normalize_punctuation(text)
    text = structural.normalize_whitespace(text)

    if level == "none":
        pass  # done

    # ── VERY-LOW ────────────────────────────────────────────────────────────
    elif level in ("very-low", "low", "medium"):
        text = language.remove_fillers(text)
        text = language.shorten_phrases(text)
        text = structural.strip_license_headers(text)
        text = structural.normalize_indentation(text)
        text = code.minify_json(text)
        text = code.minify_sql(text)
        text = code.minify_css(text)

        if level in ("low", "medium"):
            # ── LOW ─────────────────────────────────────────────────────────
            text = language.remove_hedging(text)
            text = language.remove_meta_commentary(text)
            text = language.remove_transitions(text)
            text = language.remove_parentheticals(text)
            text = language.normalize_numbers(text)
            text = language.normalize_dates(text)
            text = code.strip_code_comments(text)
            text = code.strip_docstrings(text)
            text = code.remove_null_json_fields(text)
            text = code.strip_base64(text)
            text = code.strip_hex_dumps(text)
            text = code.truncate_stack_traces(text)
            text = deduplication.dedup_exact_lines(text)
            text = deduplication.dedup_exact_sentences(text)

            if level == "medium":
                # ── MEDIUM ──────────────────────────────────────────────────
                text = deduplication.dedup_fuzzy(text)
                text = deduplication.dedup_ngram(text)
                text = deduplication.dedup_levenshtein(text)
                text = deduplication.remove_frequent_patterns(text)
                text = deduplication.trie_prefix_compress(text)
                text = extractive.tfidf_compress(text)
                text = extractive.textrank_compress(text)

    # Restore variables
    if protect_vars and mapping:
        text = restore_variables(text, mapping)

    # Final whitespace cleanup
    text = structural.normalize_whitespace(text)
    text = text.strip()

    tokens_after = count_tokens(text)
    saved = tokens_before - tokens_after
    reduction_pct = round((saved / tokens_before * 100), 1) if tokens_before > 0 else 0.0

    return CompressResult(
        output=text,
        tokens_before=tokens_before,
        tokens_after=tokens_after,
        saved=saved,
        reduction_pct=reduction_pct,
    )


def compress_text(text: str, level: Level = "low") -> str:
    """Convenience function — returns just the compressed string."""
    return compress(text, level).output
