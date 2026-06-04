"""Language algorithms — risk level: low"""

import re

# ─── FILLER REMOVAL ──────────────────────────────────────────────────────────

FILLER_PATTERNS = [
    # Sentence openers
    (r"\bBasically,?\s*", ""),
    (r"\bEssentially,?\s*", ""),
    (r"\bActually,?\s*", ""),
    (r"\bObviously,?\s*", ""),
    (r"\bClearly,?\s*", ""),
    (r"\bSimply put,?\s*", ""),
    (r"\bAt the end of the day,?\s*", ""),
    (r"\bIn order to\b", "To"),
    (r"\bin order to\b", "to"),
    (r"\bDue to the fact that\b", "Because"),
    (r"\bdue to the fact that\b", "because"),
    (r"\bIn the event that\b", "If"),
    (r"\bin the event that\b", "if"),
    (r"\bIt is important to note that\s*", ""),
    (r"\bit is important to note that\s*", ""),
    (r"\bIt should be noted that\s*", ""),
    (r"\bit should be noted that\s*", ""),
    (r"\bIt is worth noting that\s*", ""),
    (r"\bit is worth noting that\s*", ""),
    (r"\bPlease note that\s*", ""),
    (r"\bplease note that\s*", ""),
    (r"\bAs mentioned (?:above|previously|earlier),?\s*", ""),
    (r"\bas mentioned (?:above|previously|earlier),?\s*", ""),
    # Trailing filler
    (r",?\s*as (?:mentioned|stated|noted) (?:above|previously|earlier)\.?", "."),
    (r"\s+in order to achieve this\b", ""),
    (r"\s+for the purpose of\b", " for"),
]


def remove_fillers(text: str) -> str:
    for pattern, replacement in FILLER_PATTERNS:
        text = re.sub(pattern, replacement, text)
    return text


# ─── PHRASE SHORTENING ───────────────────────────────────────────────────────

PHRASE_REPLACEMENTS = [
    # Verbose → concise
    ("a large number of", "many"),
    ("a number of", "several"),
    ("a majority of", "most"),
    ("a small number of", "few"),
    ("at this point in time", "now"),
    ("at the present time", "now"),
    ("at the current time", "now"),
    ("in the near future", "soon"),
    ("in the not too distant future", "soon"),
    ("on a regular basis", "regularly"),
    ("on a daily basis", "daily"),
    ("on a weekly basis", "weekly"),
    ("with the exception of", "except"),
    ("with regard to", "regarding"),
    ("with respect to", "regarding"),
    ("in relation to", "about"),
    ("in terms of", "in"),
    ("as a result of", "due to"),
    ("as a consequence of", "due to"),
    ("prior to", "before"),
    ("subsequent to", "after"),
    ("in addition to", "besides"),
    ("in spite of", "despite"),
    ("in the case of", "for"),
    ("make use of", "use"),
    ("take into consideration", "consider"),
    ("take into account", "consider"),
    ("is able to", "can"),
    ("are able to", "can"),
    ("was able to", "could"),
    ("were able to", "could"),
    ("it is possible that", "maybe"),
    ("there is a possibility that", "maybe"),
    ("for the reason that", "because"),
    ("owing to the fact that", "because"),
    ("in light of the fact that", "because"),
    ("the fact that", "that"),
    ("a wide variety of", "various"),
    ("a wide range of", "various"),
    ("a large amount of", "much"),
    ("an increasing number of", "more"),
]


def shorten_phrases(text: str) -> str:
    for verbose, concise in PHRASE_REPLACEMENTS:
        pattern = re.compile(re.escape(verbose), re.IGNORECASE)
        _c = concise
        def _replace(m: re.Match, c=_c) -> str:
            matched = m.group(0)
            if c and matched[0].isupper():
                return c[0].upper() + c[1:]
            return c
        text = pattern.sub(_replace, text)
    return text


# ─── HEDGING REMOVAL ─────────────────────────────────────────────────────────

HEDGING_PATTERNS = [
    (r"\bI think that\b\s*", ""),
    (r"\bI believe that\b\s*", ""),
    (r"\bI feel that\b\s*", ""),
    (r"\bIn my opinion,?\s*", ""),
    (r"\bIn my view,?\s*", ""),
    (r"\bFrom my perspective,?\s*", ""),
    (r"\bIt seems (?:to me )?that\b\s*", ""),
    (r"\bIt appears (?:to me )?that\b\s*", ""),
    (r"\bOne might say that\b\s*", ""),
    (r"\bIt could be argued that\b\s*", ""),
    (r"\bSome might say that\b\s*", ""),
]


def remove_hedging(text: str) -> str:
    for pattern, replacement in HEDGING_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


# ─── META-COMMENTARY REMOVAL ─────────────────────────────────────────────────

META_PATTERNS = [
    r"^(?:Sure|Certainly|Of course|Absolutely|Gladly)[,!.]?\s*(?:I(?:'d| would) (?:be happy|love) to (?:help|assist)[^.]*\.)?\s*",
    r"^(?:Great|Excellent|Wonderful|Fantastic) (?:question|point|observation)[!.]?\s*",
    r"^I(?:'d| would) (?:be happy|love) to (?:help|assist) (?:you )?with that[.!]\s*",
    r"I hope (?:this|that) (?:helps|answers)[^.]*\.\s*$",
    r"Let me know if you (?:have any (?:other|more|further) (?:questions|concerns)|need (?:anything else|more help))[.!]\s*$",
    r"Feel free to (?:ask|reach out)[^.]*\.\s*$",
    r"Don't hesitate to (?:ask|reach out)[^.]*\.\s*$",
    r"Is there anything else I can (?:help|assist) you with[?!\.]\s*$",
]


def remove_meta_commentary(text: str) -> str:
    for pattern in META_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
    return text.strip()


# ─── TRANSITION PHRASES ──────────────────────────────────────────────────────

TRANSITION_REMOVALS = [
    r"^(?:Furthermore|Moreover|Additionally|In addition),?\s+",
    r"^(?:However|Nevertheless|Nonetheless),?\s+(?=\w)",
    r"^(?:Therefore|Thus|Hence|Consequently|As a result),?\s+",
    r"^(?:For example|For instance),?\s+(?=\w)",
]


def remove_transitions(text: str) -> str:
    """Remove redundant transition words at the start of sentences."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    result = []
    for sent in sentences:
        for pattern in TRANSITION_REMOVALS:
            new_sent = re.sub(pattern, "", sent, flags=re.IGNORECASE)
            if new_sent != sent:
                # capitalize first letter after removal
                new_sent = new_sent[0].upper() + new_sent[1:] if new_sent else new_sent
                sent = new_sent
                break  # one removal per sentence
        result.append(sent)
    return " ".join(result)


# ─── PARENTHETICAL REMOVAL ───────────────────────────────────────────────────

def remove_parentheticals(text: str) -> str:
    """Remove parenthetical phrases that don't add meaning."""
    # Remove parentheses containing only cross-references or obvious clarifications
    text = re.sub(r"\s*\((?:see|cf\.|compare|note|i\.e\.|e\.g\.)[^)]{0,60}\)", "", text, flags=re.IGNORECASE)
    # Remove empty parentheses
    text = re.sub(r"\(\s*\)", "", text)
    return text


# ─── NUMBER NORMALIZATION ────────────────────────────────────────────────────

NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13",
    "fourteen": "14", "fifteen": "15", "sixteen": "16", "seventeen": "17",
    "eighteen": "18", "nineteen": "19", "twenty": "20", "thirty": "30",
    "forty": "40", "fifty": "50", "sixty": "60", "seventy": "70",
    "eighty": "80", "ninety": "90", "hundred": "100", "thousand": "1000",
    "million": "1000000",
}


def normalize_numbers(text: str) -> str:
    """Convert spelled-out numbers to digits (only isolated words)."""
    for word, digit in NUMBER_WORDS.items():
        text = re.sub(rf"\b{word}\b", digit, text, flags=re.IGNORECASE)
    return text


# ─── DATE NORMALIZATION ──────────────────────────────────────────────────────

MONTH_MAP = {
    "january": "01", "february": "02", "march": "03", "april": "04",
    "may": "05", "june": "06", "july": "07", "august": "08",
    "september": "09", "october": "10", "november": "11", "december": "12",
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "jun": "06", "jul": "07", "aug": "08", "sep": "09",
    "oct": "10", "nov": "11", "dec": "12",
}


def normalize_dates(text: str) -> str:
    """Convert verbose dates to ISO-style (January 5th, 2024 → 2024-01-05)."""
    def _replace(m: re.Match) -> str:
        month = MONTH_MAP.get(m.group(1).lower(), "??")
        day = m.group(2).zfill(2)
        year = m.group(3)
        return f"{year}-{month}-{day}"

    pattern = (
        r"\b(January|February|March|April|May|June|July|August|September|"
        r"October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
        r"\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b"
    )
    return re.sub(pattern, _replace, text, flags=re.IGNORECASE)
