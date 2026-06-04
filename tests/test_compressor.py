"""Tests for prompt-compressor Python package."""

import pytest
from prompt_compressor import compress, compress_text, count_tokens
from prompt_compressor.algorithms.protection import protect_variables, restore_variables


# ─── PROTECTION ──────────────────────────────────────────────────────────────

def test_protect_double_brace():
    text = "Hello {{name}}, your score is {{score}}."
    protected, mapping = protect_variables(text)
    assert "{{name}}" not in protected
    assert "{{score}}" not in protected
    restored = restore_variables(protected, mapping)
    assert restored == text


def test_protect_single_brace():
    text = "Query: {user_query}\nSystem: {system_prompt}"
    protected, mapping = protect_variables(text)
    restored = restore_variables(protected, mapping)
    assert restored == text


def test_protect_dollar_brace():
    text = "Value is ${MY_VAR} here."
    protected, mapping = protect_variables(text)
    restored = restore_variables(protected, mapping)
    assert restored == text


def test_protect_xml_tag():
    text = "Fill in <topic> and <audience>."
    protected, mapping = protect_variables(text)
    restored = restore_variables(protected, mapping)
    assert restored == text


# ─── STRUCTURAL ──────────────────────────────────────────────────────────────

def test_normalize_whitespace():
    from prompt_compressor.algorithms.structural import normalize_whitespace
    result = normalize_whitespace("Hello   world\n\n\n\n\nfoo")
    assert "   " not in result
    assert result.count("\n") < 4


def test_strip_ansi():
    from prompt_compressor.algorithms.structural import strip_ansi
    result = strip_ansi("\x1b[31mHello\x1b[0m world")
    assert result == "Hello world"


def test_normalize_unicode():
    from prompt_compressor.algorithms.structural import normalize_unicode
    result = normalize_unicode("\u201cHello\u201d \u2013 world")
    assert '"Hello"' in result
    assert " - " in result


# ─── LANGUAGE ────────────────────────────────────────────────────────────────

def test_remove_fillers():
    from prompt_compressor.algorithms.language import remove_fillers
    result = remove_fillers("It is important to note that you should use Python.")
    assert "It is important to note that" not in result
    assert "Python" in result


def test_shorten_phrases():
    from prompt_compressor.algorithms.language import shorten_phrases
    result = shorten_phrases("In order to run the test, you need to make use of pytest.")
    assert "make use of" not in result
    assert "make use of" not in result
    assert "pytest" in result


def test_remove_hedging():
    from prompt_compressor.algorithms.language import remove_hedging
    result = remove_hedging("I think that Python is great.")
    assert "I think that" not in result
    assert "Python" in result


def test_remove_meta_commentary():
    from prompt_compressor.algorithms.language import remove_meta_commentary
    result = remove_meta_commentary("Sure, I'd be happy to help! Here is the answer.\nLet me know if you have any other questions.")
    assert "Sure" not in result
    assert "Let me know" not in result


def test_normalize_numbers():
    from prompt_compressor.algorithms.language import normalize_numbers
    result = normalize_numbers("There are five items and twenty users.")
    assert "5" in result
    assert "20" in result


def test_normalize_dates():
    from prompt_compressor.algorithms.language import normalize_dates
    result = normalize_dates("The deadline is January 5th, 2024.")
    assert "2024-01-05" in result


# ─── CODE ────────────────────────────────────────────────────────────────────

def test_minify_json():
    from prompt_compressor.algorithms.code import minify_json
    text = '```json\n{\n  "key": "value",\n  "num": 42\n}\n```'
    result = minify_json(text)
    assert "\n  " not in result
    assert '"key":"value"' in result


def test_minify_sql():
    from prompt_compressor.algorithms.code import minify_sql
    text = "```sql\nSELECT   *\nFROM   users\n-- get all users\nWHERE id = 1\n```"
    result = minify_sql(text)
    assert "-- get all users" not in result
    assert "SELECT" in result


def test_strip_base64():
    from prompt_compressor.algorithms.code import strip_base64
    b64 = "SGVsbG8gV29ybGQhIFRoaXMgaXMgYSBsb25nIGJhc2U2NCBzdHJpbmcgZm9yIHRlc3Rpbmc="
    result = strip_base64(f"data: {b64}")
    assert b64 not in result
    assert "[base64_data]" in result


# ─── DEDUPLICATION ───────────────────────────────────────────────────────────

def test_dedup_exact_lines():
    from prompt_compressor.algorithms.deduplication import dedup_exact_lines
    text = "line one\nline one\nline two"
    result = dedup_exact_lines(text)
    assert result.count("line one") == 1


def test_dedup_exact_sentences():
    from prompt_compressor.algorithms.deduplication import dedup_exact_sentences
    text = "The cat sat on the mat. The cat sat on the mat. The dog barked."
    result = dedup_exact_sentences(text)
    assert result.count("The cat sat on the mat") == 1


def test_dedup_fuzzy():
    from prompt_compressor.algorithms.deduplication import dedup_fuzzy
    text = (
        "The quick brown fox jumps over the lazy dog. "
        "A quick brown fox jumps over a lazy dog. "
        "Python is a great programming language."
    )
    result = dedup_fuzzy(text, threshold=0.7)
    # Should keep first fox sentence and the python sentence, drop second fox
    assert "Python" in result


# ─── EXTRACTIVE ──────────────────────────────────────────────────────────────

def test_tf_compress():
    from prompt_compressor.algorithms.extractive import tf_compress
    text = (
        "Machine learning is a type of artificial intelligence. "
        "It allows computers to learn from data without explicit programming. "
        "Deep learning is a subfield of machine learning using neural networks. "
        "The weather is nice today. "
        "Machine learning models require training data."
    )
    result = tf_compress(text, keep_ratio=0.6)
    assert len(result) < len(text)


def test_textrank_compress():
    from prompt_compressor.algorithms.extractive import textrank_compress
    text = (
        "Natural language processing is a branch of AI. "
        "It deals with the interaction between computers and humans. "
        "NLP enables machines to understand human language. "
        "The sky is blue today and it looks great. "
        "Machine translation is an important NLP application."
    )
    result = textrank_compress(text, keep_ratio=0.6)
    assert len(result) < len(text)


# ─── FULL PIPELINE ───────────────────────────────────────────────────────────

def test_compress_levels():
    text = (
        "It is important to note that in order to make use of this system, "
        "you need to provide a large number of examples. "
        "I think that basically, the system is quite good. "
        "The system uses machine learning. The system uses machine learning. "
        "Please note that you should configure the settings prior to starting."
    )
    for level in ["none", "very-low", "low", "medium"]:
        result = compress(text, level=level)
        assert result.output
        assert result.tokens_before > 0
        assert result.tokens_after > 0
        assert result.tokens_after <= result.tokens_before


def test_compress_preserves_variables():
    text = "Dear {{name}}, your query was: {query}. Tag: <topic>. Env: ${API_KEY}."
    result = compress(text, level="medium")
    assert "{{name}}" in result.output
    assert "{query}" in result.output
    assert "<topic>" in result.output
    assert "${API_KEY}" in result.output


def test_compress_text_shorthand():
    text = "In order to use this tool, you should make use of the compress function."
    result = compress_text(text, level="low")
    assert isinstance(result, str)
    assert len(result) <= len(text)


def test_empty_input():
    result = compress("", level="low")
    assert result.output == ""
    assert result.tokens_before == 0


def test_token_counter():
    assert count_tokens("Hello world") > 0
    assert count_tokens("") == 0
    assert count_tokens("a" * 100) > count_tokens("a" * 10)
