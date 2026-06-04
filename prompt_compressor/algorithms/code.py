"""Code algorithms — risk level: low / medium"""

import re
import json


# ─── COMMENT STRIPPING ───────────────────────────────────────────────────────

def strip_code_comments(text: str) -> str:
    """Remove single-line and inline // and # comments from code blocks."""
    # Only operate inside fenced code blocks
    def _strip_block(m: re.Match) -> str:
        lang = m.group(1).lower() if m.group(1) else ""
        code = m.group(2)
        if lang in ("python", "py", "ruby", "rb", "sh", "bash", ""):
            # Strip # comments (but not shebangs on line 1)
            lines = code.split("\n")
            out = []
            for i, line in enumerate(lines):
                if i == 0 and line.startswith("#!"):
                    out.append(line)
                else:
                    stripped = re.sub(r"\s*#(?!{).*$", "", line)
                    out.append(stripped)
            code = "\n".join(out)
        if lang in ("javascript", "js", "typescript", "ts", "java", "c", "cpp", "go", "rust", ""):
            code = re.sub(r"\s*//(?!/).*$", "", code, flags=re.MULTILINE)
            # Block comments /* ... */
            code = re.sub(r"/\*[\s\S]*?\*/", "", code)
        return m.group(0)[:m.group(0).find(m.group(2))] + code + "```"

    return re.sub(r"```(\w*)\n([\s\S]*?)```", _strip_block, text)


def strip_docstrings(text: str) -> str:
    """Remove Python docstrings inside fenced code blocks."""
    def _strip_block(m: re.Match) -> str:
        lang = m.group(1).lower() if m.group(1) else ""
        code = m.group(2)
        if lang in ("python", "py", ""):
            # Remove triple-quoted strings that are standalone statements
            code = re.sub(r'^\s*"""[\s\S]*?"""\s*$', "", code, flags=re.MULTILINE)
            code = re.sub(r"^\s*'''[\s\S]*?'''\s*$", "", code, flags=re.MULTILINE)
        return m.group(0)[:m.group(0).find(m.group(2))] + code + "```"

    return re.sub(r"```(\w*)\n([\s\S]*?)```", _strip_block, text)


# ─── JSON MINIFICATION ───────────────────────────────────────────────────────

def minify_json(text: str) -> str:
    """Minify JSON code blocks."""
    def _minify(m: re.Match) -> str:
        try:
            parsed = json.loads(m.group(1))
            minified = json.dumps(parsed, separators=(",", ":"), ensure_ascii=False)
            return f"```json\n{minified}\n```"
        except (json.JSONDecodeError, ValueError):
            return m.group(0)

    return re.sub(r"```json\n([\s\S]*?)```", _minify, text)


def remove_null_json_fields(text: str) -> str:
    """Remove null/None fields from JSON code blocks."""
    def _remove_nulls(m: re.Match) -> str:
        try:
            parsed = json.loads(m.group(1))
            if isinstance(parsed, dict):
                cleaned = {k: v for k, v in parsed.items() if v is not None}
                return f"```json\n{json.dumps(cleaned, indent=2, ensure_ascii=False)}\n```"
        except (json.JSONDecodeError, ValueError):
            pass
        return m.group(0)

    return re.sub(r"```json\n([\s\S]*?)```", _remove_nulls, text)


# ─── SQL MINIFICATION ────────────────────────────────────────────────────────

def minify_sql(text: str) -> str:
    """Minify SQL code blocks — remove comments and extra whitespace."""
    def _minify(m: re.Match) -> str:
        sql = m.group(1)
        # Remove -- comments
        sql = re.sub(r"--[^\n]*", "", sql)
        # Remove /* */ comments
        sql = re.sub(r"/\*[\s\S]*?\*/", "", sql)
        # Collapse whitespace
        sql = re.sub(r"\s+", " ", sql).strip()
        return f"```sql\n{sql}\n```"

    return re.sub(r"```sql\n([\s\S]*?)```", _minify, text, flags=re.IGNORECASE)


# ─── CSS MINIFICATION ────────────────────────────────────────────────────────

def minify_css(text: str) -> str:
    """Minify CSS code blocks."""
    def _minify(m: re.Match) -> str:
        css = m.group(1)
        css = re.sub(r"/\*[\s\S]*?\*/", "", css)  # comments
        css = re.sub(r"\s*([{}:;,])\s*", r"\1", css)
        css = re.sub(r"\s+", " ", css).strip()
        return f"```css\n{css}\n```"

    return re.sub(r"```css\n([\s\S]*?)```", _minify, text)


# ─── BASE64 / HEX STRIPPING ──────────────────────────────────────────────────

def strip_base64(text: str) -> str:
    """Replace long base64 strings with a placeholder."""
    return re.sub(
        r"\b([A-Za-z0-9+/]{60,}={0,2})\b",
        "[base64_data]",
        text,
    )


def strip_hex_dumps(text: str) -> str:
    """Replace long hex strings with a placeholder."""
    return re.sub(
        r"\b([0-9a-fA-F]{40,})\b",
        "[hex_data]",
        text,
    )


# ─── STACK TRACE TRUNCATION ──────────────────────────────────────────────────

def truncate_stack_traces(text: str, max_frames: int = 5) -> str:
    """Keep only the first N frames of stack traces."""
    def _truncate(m: re.Match) -> str:
        frames = re.findall(r"^\s+(?:at |File )[^\n]+$", m.group(0), re.MULTILINE)
        if len(frames) <= max_frames:
            return m.group(0)
        kept = frames[:max_frames]
        truncated_count = len(frames) - max_frames
        return m.group(0).split(frames[0])[0] + "\n".join(kept) + f"\n  ... ({truncated_count} more frames)"

    # Python-style tracebacks
    text = re.sub(
        r"Traceback \(most recent call last\):[\s\S]*?(?=\n\S|\Z)",
        _truncate,
        text,
    )
    return text


# ─── TYPESCRIPT TYPE ANNOTATION REMOVAL ─────────────────────────────────────

def strip_ts_types(text: str) -> str:
    """Remove TypeScript type annotations from TS code blocks."""
    def _strip(m: re.Match) -> str:
        lang = m.group(1).lower() if m.group(1) else ""
        code = m.group(2)
        if lang in ("typescript", "ts"):
            # Remove `: Type` annotations in function params/variables
            code = re.sub(r":\s*[A-Z][A-Za-z<>\[\]|&, ]+(?=[,)=\n;])", "", code)
            # Remove `<Type>` generics (basic)
            code = re.sub(r"<[A-Z][A-Za-z<>\[\]|& ,]+>(?=\()", "", code)
        return m.group(0)[:m.group(0).find(m.group(2))] + code + "```"

    return re.sub(r"```(\w*)\n([\s\S]*?)```", _strip, text)
