# prompt-compressor

> Rule-based LLM prompt compression — 30+ algorithms, zero dependencies.

[![PyPI version](https://badge.fury.io/py/prompt-compressor.svg)](https://pypi.org/project/prompt-compressor/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Compress prompts **before** sending them to any LLM API. No model required, no API calls, zero overhead. Works with OpenAI, Anthropic, AWS Bedrock, Cohere, or any token-based API.

🌐 **Web app**: [prompt-compressor.com](https://prompt-compressor.com)  
📦 **npm**: [prompt-compressor](https://www.npmjs.com/package/prompt-compressor)

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

| Level | Algorithms | Typical Reduction |
|-------|-----------|-------------------|
| `none` | Whitespace, unicode, ANSI, punctuation | 5–15% |
| `very-low` | + Filler removal, phrase shortening, JSON/SQL minify, license headers | 15–30% |
| `low` | + Hedging, meta-commentary, transitions, number normalization, code comments, exact dedup | 25–45% |
| `medium` | + Fuzzy/ngram/Levenshtein dedup, frequent patterns, TF-IDF, TextRank | 30–70% |

## Variable Protection

Variables in `{{var}}`, `{var}`, `<tag>`, and `${var}` format are **always protected** by default:

```python
result = compress("Hello {{name}}, query: {user_query}", level="medium")
# {{name}} and {user_query} are preserved exactly
```

Disable with `protect_vars=False`.

---

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
