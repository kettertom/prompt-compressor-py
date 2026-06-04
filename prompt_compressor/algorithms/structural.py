"""Structural algorithms — risk level: none / very-low"""

import re
import unicodedata


# ─── NONE ────────────────────────────────────────────────────────────────────

def normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces/tabs into one, strip trailing whitespace per line."""
    lines = text.split("\n")
    lines = [re.sub(r"[ \t]+", " ", line).rstrip() for line in lines]
    # collapse 3+ blank lines into 2
    result, blank_count = [], 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                result.append(line)
        else:
            blank_count = 0
            result.append(line)
    return "\n".join(result)


def normalize_unicode(text: str) -> str:
    """Replace fancy unicode punctuation with ASCII equivalents."""
    replacements = {
        "\u2018": "'", "\u2019": "'",   # curly single quotes
        "\u201c": '"', "\u201d": '"',   # curly double quotes
        "\u2013": "-", "\u2014": "-",   # en/em dash
        "\u2026": "...",               # ellipsis
        "\u00a0": " ",                 # non-breaking space
        "\u200b": "",                  # zero-width space
        "\ufeff": "",                  # BOM
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return unicodedata.normalize("NFC", text)


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes."""
    return re.sub(r"\x1b\[[0-9;]*[mGKHF]", "", text)


def normalize_punctuation(text: str) -> str:
    """Remove redundant punctuation (e.g. '!!!!' -> '!')."""
    text = re.sub(r"([!?]){2,}", r"\1", text)
    text = re.sub(r"\.{4,}", "...", text)
    return text


# ─── VERY-LOW ────────────────────────────────────────────────────────────────

def strip_license_headers(text: str) -> str:
    """Remove common license header blocks at the top of files."""
    patterns = [
        r"^/\*[\s\S]*?(?:license|copyright|MIT|Apache|GPL)[\s\S]*?\*/\s*",
        r"^(?:#[^\n]*(?:license|copyright|MIT|Apache|GPL)[^\n]*\n)+",
    ]
    for p in patterns:
        text = re.sub(p, "", text, flags=re.IGNORECASE | re.MULTILINE)
    return text


def normalize_indentation(text: str) -> str:
    """Convert 4-space indents to 2-space (reduces tokens in code-heavy prompts)."""
    lines = text.split("\n")
    result = []
    for line in lines:
        stripped = line.lstrip(" ")
        spaces = len(line) - len(stripped)
        # only compress if multiple of 4
        if spaces > 0 and spaces % 4 == 0:
            new_indent = " " * (spaces // 2)
            result.append(new_indent + stripped)
        else:
            result.append(line)
    return "\n".join(result)
