"""Regression tests for the 'medium' steps (same guarantees as the JS package)."""
from prompt_compressor import compress
from prompt_compressor.algorithms.deduplication import dedup_fuzzy, dedup_ngram, dedup_levenshtein
from prompt_compressor.algorithms.extractive import tf_compress, tfidf_compress, textrank_compress

PROSE = " ".join([
    "The weather was pleasant and the team enjoyed a relaxed afternoon together.",
    "Everyone agreed that the coffee in the new office tastes considerably better.",
    "Several people mentioned that the plants make the space feel much more welcoming.",
    "The quarterly offsite is scheduled for March 3 in Tel Aviv.",
    "Attendance is required for all team leads.",
    "Lunch conversations covered movies, travel plans and weekend hobbies.",
    "A few colleagues talked about learning to play the guitar this winter.",
])
SUMMARIZERS = [tf_compress, tfidf_compress, textrank_compress]


def test_dedup_keeps_short_lines_and_line_breaks():
    t = "Rules:\n- Be kind\n- Be brief\n\nOK.\nDone."
    for fn in (dedup_fuzzy, dedup_ngram, dedup_levenshtein):
        assert fn(t) == t, fn.__name__


def test_near_duplicates_with_different_numbers_are_kept():
    t = "Retrying payment for order ORD-1 (attempt 2/3) now.\nRetrying payment for order ORD-1 (attempt 3/3) now."
    assert dedup_fuzzy(t, 0.7) == t
    assert dedup_levenshtein(t) == t


def test_real_near_duplicates_are_removed():
    t = "Always answer in a friendly and professional tone please.\nAlways answer in a friendly and professional tone, please!"
    assert len(dedup_levenshtein(t).split("\n")) == 1


def test_summarizers_never_touch_fenced_code():
    t = PROSE + '\n\n```json\n{"a": 1, "b": 2}\n{"a": 1, "b": 2}\n```'
    for fn in SUMMARIZERS:
        assert '```json\n{"a": 1, "b": 2}\n{"a": 1, "b": 2}\n```' in fn(t), fn.__name__


def test_summarizers_keep_critical_and_drop_soft_prose():
    for fn in SUMMARIZERS:
        out = fn(PROSE)
        assert "March 3" in out and "required for all team leads" in out, fn.__name__
        assert len(out) < len(PROSE), fn.__name__


def test_questions_requests_and_deadlines_are_kept():
    t = " ".join([
        "The team discussed many things during the long meeting yesterday afternoon.",
        "Several ideas came up about the office layout and the kitchen schedule.",
        "People also chatted about the upcoming holidays and travel plans in general.",
        "What is the most likely root cause of the outage?",
        "Could you send the summary to the whole group when you get a chance.",
        "Please share your opinion on the billing page by the end of the week.",
        "Everyone seemed generally happy with how the discussion went overall.",
    ])
    for fn in SUMMARIZERS:
        out = fn(t, 0.3)
        for must in ("root cause", "Could you send", "end of the week"):
            assert must in out, (fn.__name__, must)


def test_medium_keeps_structure_rules_ids_and_variables():
    t = ('You are a bot for {{company}}.\nPlease note that you must never share data.\n\n'
         '- Refunds within 30 days\n- Code SORRY20\n\n```json\n{"id": "ORD-1", "total": 89}\n```')
    out = compress(t, level="medium").output
    for must in ("{{company}}", "never share data", "30 days", "SORRY20", "ORD-1", "89"):
        assert must in out, must
    assert "- Refunds within 30 days\n- Code SORRY20" in out


def test_json_and_code_stay_intact():
    import json, re
    data = {"orders": [
        {"id": "A", "status": "processing", "qty": 1, "currency": "USD", "note": None},
        {"id": "B", "status": "processing", "qty": 1, "currency": "USD", "note": ""},
    ]}
    t = ("Summarize:\n\n```json\n" + json.dumps(data, indent=2) + "\n```\n\n"
         "```js\nif (a) {\n  if (b) {\n    return 1;\n  }\n}\n```")
    strip = lambda v: ({k: strip(x) for k, x in v.items() if x not in (None, "")} if isinstance(v, dict)
                       else [strip(x) for x in v] if isinstance(v, list) else v)
    for level in ("very-low", "low", "medium"):
        out = compress(t, level=level).output
        block = re.search(r"```json\s*([\s\S]*?)```", out).group(1)
        assert strip(json.loads(block)) == strip(data), level
        assert out.count("}") >= 2 + 2, level  # both closing braces of the js block survive
