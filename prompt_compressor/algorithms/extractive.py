"""Extractive algorithms — risk level: medium"""

import re
import math
from collections import Counter
from typing import List, Dict, Tuple

from ._units import summarize_by


def _split_sentences(text: str) -> List[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\b[a-z]{2,}\b", text.lower())


STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "this", "that", "these", "those", "it", "its",
    "as", "if", "then", "than", "so", "up", "out", "no", "not", "can",
    "about", "into", "through", "during", "before", "after", "above", "below",
    "between", "each", "more", "most", "other", "some", "such", "own",
    "same", "both", "few", "more", "most", "other", "into", "through",
    "i", "you", "we", "they", "he", "she", "me", "him", "her", "us", "them",
}


# ─── TF COMPRESSION ──────────────────────────────────────────────────────────

def tf_compress(text: str, keep_ratio: float = 0.75) -> str:
    """
    Drop the lowest-scoring prose sentences by term frequency.
    `keep_ratio` is the fraction of *droppable* prose sentences to keep.
    Code blocks, structured lines, questions and sentences with rules,
    numbers, IDs or variables are always kept.
    """
    def scores(sents: List[str]) -> List[float]:
        tf: Counter = Counter(t for s in sents for t in _tokenize(s) if t not in STOPWORDS)
        out = []
        for s in sents:
            toks = [t for t in _tokenize(s) if t not in STOPWORDS]
            out.append(sum(tf[t] for t in toks) / len(toks) if toks else 0.0)
        return out
    return summarize_by(text, keep_ratio, scores)


# ─── TF-IDF COMPRESSION ──────────────────────────────────────────────────────

def tfidf_compress(text: str, keep_ratio: float = 0.75) -> str:
    """
    Drop the lowest-scoring prose sentences by TF-IDF.
    `keep_ratio` is the fraction of *droppable* prose sentences to keep.
    Code blocks, structured lines, questions and sentences with rules,
    numbers, IDs or variables are always kept.
    """
    def scores(sents: List[str]) -> List[float]:
        toks = [[t for t in _tokenize(s) if t not in STOPWORDS] for s in sents]
        n = len(sents)
        df: Counter = Counter(t for ts in toks for t in set(ts))
        out = []
        for ts in toks:
            if not ts:
                out.append(0.0)
                continue
            tf = Counter(ts)
            out.append(sum((tf[t] / len(ts)) * math.log((n + 1) / (df[t] + 1)) for t in ts) / len(ts))
        return out
    return summarize_by(text, keep_ratio, scores)


# ─── TEXTRANK COMPRESSION ────────────────────────────────────────────────────

def _similarity(tokens_a: set, tokens_b: set) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    denom = math.log(len(tokens_a) + 1) + math.log(len(tokens_b) + 1)
    return len(intersection) / denom if denom else 0.0


def textrank_compress(text: str, keep_ratio: float = 0.75, damping: float = 0.85, iterations: int = 30) -> str:
    """
    TextRank: drop the least "central" prose sentences.
    `keep_ratio` is the fraction of *droppable* prose sentences to keep.
    Code blocks, structured lines, questions and sentences with rules,
    numbers, IDs or variables are always kept.
    """
    def scores(sents: List[str]) -> List[float]:
        n = len(sents)
        sets = [set(t for t in _tokenize(s) if t not in STOPWORDS) for s in sents]
        sim = [[0.0 if i == j else _similarity(sets[i], sets[j]) for j in range(n)] for i in range(n)]
        row = [sum(r) for r in sim]
        sc = [1.0 / n] * n
        for _ in range(iterations):
            sc = [(1 - damping) / n + damping * sum(sc[j] * (sim[j][i] / row[j] if row[j] else 1.0 / n) for j in range(n))
                  for i in range(n)]
        return sc
    return summarize_by(text, keep_ratio, scores)
