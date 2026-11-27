# prompt-compressor

> Rule-based LLM prompt compression — 30+ algorithms, zero dependencies.

[![PyPI version](https://badge.fury.io/py/prompt-compressor.svg)](https://pypi.org/project/prompt-compressor/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Compress prompts **before** sending them to any LLM API. No model required, no API calls, zero overhead. Works with OpenAI, Anthropic, AWS Bedrock, Cohere, or any token-based API.

**No model. No API key. Deterministic. Zero dependencies. Your data never leaves your machine.**
Most prompt compressors (e.g. LLMLingua) run a language model to decide what to cut. This one uses 30+ rule-based algorithms, so the same input always gives the same output and it is safe for data you can't send anywhere. **At the default level it cut 20% of tokens across 8 real-world prompt types while keeping 94/94 critical instructions** ([benchmark](#benchmark)).

🌐 **Web app**: [prompt-compressor.com](https://prompt-compressor.com)  
📦 **npm**: [prompt-compressor](https://www.npmjs.com/package/prompt-compressor)  
🤖 **MCP server** (Claude, Cursor, VS Code): `claude mcp add prompt-compressor -- npx -y prompt-compressor-mcp`

⭐ **Find it useful? [Star it on GitHub](https://github.com/kettertom/prompt-compressor-py)** · 🐛 **Found a bug or have an idea? [Open an issue](https://github.com/kettertom/prompt-compressor-py/issues/new)**

---

## Install

```bash
pip install prompt-compressor
```

## Python API

```python
from prompt_compressor import compress

result = compress(system_prompt, level="low")

print(result.output)           # compressed text
print(result.tokens_before)    # e.g. 1200
print(result.tokens_after)     # e.g. 820
print(result.saved)            # 380
print(result.reduction_pct)    # 31.7
```

### Convenience function

```python
from prompt_compressor import compress_text

compressed = compress_text(my_prompt, level="very-low")
```

### With AWS Bedrock

```python
import boto3
from prompt_compressor import compress

bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

result = compress(system_prompt, level="low")

response = bedrock.invoke_model(
    modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "system": result.output,   # compressed!
        "messages": [{"role": "user", "content": user_message}],
        "max_tokens": 1024,
    }),
)
```

---

## CLI

```bash
# Compress a file
prompt-compressor system_prompt.txt --level low

# With stats
prompt-compressor system_prompt.txt --level medium --stats

# Pipe
cat my_prompt.txt | prompt-compressor --level very-low

# Save to file
prompt-compressor input.txt --level low --output compressed.txt
```

---

## Levels

| Level | Algorithms | Measured reduction ([benchmark](#benchmark)) |
|-------|-----------|-------------------|
| `none` | Whitespace, unicode, ANSI, punctuation | 3% avg (0–10%) |
| `very-low` | + Filler removal, phrase shortening, JSON/SQL minify, license headers | 9% avg (1–31%) |
| `low` ✅ default | + Hedging, meta-commentary, transitions, number normalization, code comments, exact dedup | **20% avg (0–61%)**, 100% of critical facts kept |
| `medium` ⚠️ | + Fuzzy/ngram/Levenshtein dedup, frequent patterns, TF-IDF, TextRank | 86% avg, but **only 34% of critical facts kept** |

> ⚠️ **`medium` is lossy summarization, not compression.** It keeps a fraction of the sentences and can drop instructions, numbers and IDs. Use it only for background context you'd be happy to see summarized, never for system prompts, tool output or anything with rules in it. Savings are biggest on code, logs and repeated content. Prose that is already concise saves only a few percent at the safe levels.

## Variable Protection

Variables in `{{var}}`, `{var}`, `<tag>`, and `${var}` format are **always protected** by default:

```python
result = compress("Hello {{name}}, query: {user_query}", level="medium")
# {{name}} and {user_query} are preserved exactly
```

Disable with `protect_vars=False`.

---

## Benchmark

The same 8 production-style prompts and must-keep facts as the [JS package benchmark](https://github.com/kettertom/prompt-compressor#benchmark), run against this Python implementation: support system prompt, RAG context, agent instructions, tool JSON, code review, logs, chat history and an email thread ([`bench/prompts`](bench/prompts), [`bench/facts.json`](bench/facts.json)).

### Results at the default level (`low`)

| Prompt | Tokens before | Tokens after | Saved | $ saved per 1M calls* | Must-keep facts kept |
|---|---:|---:|---:|---:|:---:|
| Support bot system prompt | 325 | 306 | **6%** | $57 | 12/12 ✅ |
| RAG context (4 retrieved docs) | 431 | 338 | **22%** | $279 | 13/13 ✅ |
| Agent instructions + tool specs | 333 | 316 | **5%** | $51 | 17/17 ✅ |
| Tool output (JSON orders) | 448 | 398 | **11%** | $150 | 11/11 ✅ |
| Code review request (Python) | 292 | 114 | **61%** | $534 | 9/9 ✅ |
| Production logs + stack trace | 873 | 564 | **35%** | $927 | 9/9 ✅ |
| Chat history (8 turns) | 310 | 309 | **0%** | $3 | 11/11 ✅ |
| Email thread to summarize | 327 | 312 | **5%** | $45 | 12/12 ✅ |
| **Total** | **3,339** | **2,657** | **20%** | **$2,046** | **94/94** |

\* At $3 per 1M input tokens. For your model, multiply by (your price ÷ 3). Tokens counted with OpenAI's `o200k_base` tokenizer.

### By risk level

| Level | Avg. saved | Must-keep facts kept |
|---|---:|:---:|
| `very-low` | 9% | 94/94 (100%) |
| `low` | 20% | 94/94 (100%) |
| `medium` | 86% | 32/94 (34%) |

Facts lost (if any):

- `medium` · Support bot system prompt: lost 10/12
- `medium` · RAG context (4 retrieved docs): lost 11/13
- `medium` · Agent instructions + tool specs: lost 10/17
- `medium` · Tool output (JSON orders): lost 11/11
- `medium` · Production logs + stack trace: lost 8/9
- `medium` · Chat history (8 turns): lost 5/11
- `medium` · Email thread to summarize: lost 7/12

The exact facts lost are listed in [`bench/results.json`](bench/results.json).

**Reproduce it:** `pip install tiktoken && python bench/run.py`

## Algorithm Reference

### Structural (none / very-low)
| Algorithm | Description |
|-----------|-------------|
| `normalize_whitespace` | Collapse spaces, trailing whitespace, blank lines |
| `normalize_unicode` | Replace fancy quotes, dashes, NBSP with ASCII |
| `strip_ansi` | Remove ANSI escape codes |
| `normalize_punctuation` | Remove `!!!!` → `!`, `....` → `...` |
| `strip_license_headers` | Remove MIT/Apache/GPL header blocks |
| `normalize_indentation` | 4-space → 2-space indent |

### Language (very-low / low)
| Algorithm | Description |
|-----------|-------------|
| `remove_fillers` | "It is important to note that", "basically", "actually" |
| `shorten_phrases` | "in order to" → "to", "make use of" → "use" (50+ rules) |
| `remove_hedging` | "I think that", "In my opinion" |
| `remove_meta_commentary` | "Sure, I'd be happy to help!", "Let me know if..." |
| `remove_transitions` | Redundant "Furthermore,", "Additionally," |
| `remove_parentheticals` | Cross-reference parentheses |
| `normalize_numbers` | "twenty" → "20", "five" → "5" |
| `normalize_dates` | "January 5th, 2024" → "2024-01-05" |

### Code (low)
| Algorithm | Description |
|-----------|-------------|
| `strip_code_comments` | `#` and `//` comments in fenced blocks |
| `strip_docstrings` | Python triple-quoted docstrings |
| `minify_json` | JSON code blocks → minified |
| `remove_null_json_fields` | Remove `null` fields from JSON |
| `minify_sql` | SQL blocks → whitespace-collapsed |
| `minify_css` | CSS blocks → minified |
| `strip_base64` | Long base64 strings → `[base64_data]` |
| `strip_hex_dumps` | Long hex strings → `[hex_data]` |
| `truncate_stack_traces` | Keep first 5 frames |
| `strip_ts_types` | TypeScript type annotations |

### Deduplication (low / medium)
| Algorithm | Description |
|-----------|-------------|
| `dedup_exact_lines` | Consecutive duplicate lines |
| `dedup_exact_sentences` | Exact duplicate sentences |
| `dedup_fuzzy` | Jaccard similarity ≥ 0.85 |
| `dedup_ngram` | N-gram overlap ≥ 0.7 |
| `dedup_levenshtein` | Edit distance < 15% |
| `remove_frequent_patterns` | Apriori-style repeated phrases |
| `trie_prefix_compress` | Bullet groups with shared prefix |

### Extractive (medium)
| Algorithm | Description |
|-----------|-------------|
| `tf_compress` | Keep sentences by term frequency |
| `tfidf_compress` | Keep sentences by TF-IDF score |
| `textrank_compress` | PageRank-style sentence scoring |

---

## Zero Dependencies

`prompt-compressor` uses only the Python standard library. No `numpy`, `nltk`, `spacy`, `tiktoken`, or anything else to install.

---

## License

MIT © Tom Ketter
