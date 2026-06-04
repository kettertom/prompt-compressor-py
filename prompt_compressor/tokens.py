"""Token counting — simple regex-based approximation (no external deps)."""

import re


def count_tokens(text: str) -> int:
    """
    Approximate token count using a simple word/punctuation split.
    Rule of thumb: tokens ≈ words * 1.3 for English prose,
    but code has more tokens per word.
    This function uses a character-level split that matches tiktoken's
    behavior reasonably well without requiring the library.
    """
    if not text:
        return 0

    # Split on whitespace and punctuation boundaries (rough cl100k_base approximation)
    tokens = re.findall(r"""
        \w+(?:'\w+)*   |   # words with contractions
        [^\w\s]            # punctuation/symbols
    """, text, re.VERBOSE)

    # Adjust for long words that would be split into sub-tokens
    adjusted = 0
    for token in tokens:
        length = len(token)
        if length <= 4:
            adjusted += 1
        elif length <= 8:
            adjusted += 1.3
        elif length <= 12:
            adjusted += 1.6
        else:
            adjusted += length / 4.0  # long tokens are split more aggressively

    return max(1, round(adjusted))
