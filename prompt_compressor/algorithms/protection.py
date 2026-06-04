"""Variable protection — placeholder substitution before compression, restore after."""

import re
from typing import Tuple, Dict


# Patterns for variable formats to protect
VARIABLE_PATTERNS = [
    r"\{\{[^}]+\}\}",      # {{variable}}
    r"\$\{[^}]+\}",        # ${variable}
    r"<[a-zA-Z_][a-zA-Z0-9_-]*>",  # <tag>
    r"\{[a-zA-Z_][a-zA-Z0-9_.]*\}",  # {variable}  (single braces, alpha-start)
]

_COMBINED = re.compile("|".join(VARIABLE_PATTERNS))
_PLACEHOLDER_TPL = "\x00VAR{index}\x00"


def protect_variables(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Replace all variable-like patterns with safe placeholders.
    Returns (protected_text, mapping) where mapping[placeholder] = original.
    """
    mapping: Dict[str, str] = {}
    index = 0

    def _replace(m: re.Match) -> str:
        nonlocal index
        placeholder = _PLACEHOLDER_TPL.format(index=index)
        mapping[placeholder] = m.group(0)
        index += 1
        return placeholder

    protected = _COMBINED.sub(_replace, text)
    return protected, mapping


def restore_variables(text: str, mapping: Dict[str, str]) -> str:
    """Restore original variables from the mapping."""
    for placeholder, original in mapping.items():
        text = text.replace(placeholder, original)
    return text
