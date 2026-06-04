"""Extractive algorithms — risk level: medium"""

import re
import math
from collections import Counter
from typing import List, Dict, Tuple


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

def tf_compress(text: str, keep_ratio: float = 0.6) -> str:
    """
    Score each sentence by the average term frequency of its non-stopword tokens.
    Keep the top `keep_ratio` fraction of sentences (by score), preserving order.
    """
    sentences = _split_sentences(text)
    if len(sentences) <= 3:
        return text

    # Compute TF over full document
    all_tokens = _tokenize(text)
    tf: Counter = Counter(t for t in all_tokens if t not in STOPWORDS)
    total = sum(tf.values()) or 1

    def _score(sent: str) -> float:
        tokens = [t for t in _tokenize(sent) if t not in STOPWORDS]
        if not tokens:
            return 0.0
        return sum(tf[t] / total for t in tokens) / len(tokens)

    scored = [(i, s, _score(s)) for i, s in enumerate(sentences)]
    threshold = sorted([x[2] for x in scored], reverse=True)[
        max(0, int(len(scored) * keep_ratio) - 1)
    ]
    kept = [s for i, s, score in scored if score >= threshold]
    return " ".join(kept)


# ─── TF-IDF COMPRESSION ──────────────────────────────────────────────────────

def tfidf_compress(text: str, keep_ratio: float = 0.6) -> str:
    """
    Score each sentence by TF-IDF, treating each sentence as a document.
    Keep the top `keep_ratio` fraction.
    """
    sentences = _split_sentences(text)
    if len(sentences) <= 3:
        return text

    # Tokenize per sentence
    sent_tokens = [
        [t for t in _tokenize(s) if t not in STOPWORDS]
        for s in sentences
    ]
    N = len(sentences)

    # IDF
    df: Counter = Counter()
    for tokens in sent_tokens:
        for t in set(tokens):
            df[t] += 1

    def _idf(term: str) -> float:
        return math.log((N + 1) / (df.get(term, 0) + 1)) + 1

    def _score(tokens: List[str]) -> float:
        if not tokens:
            return 0.0
        tf: Counter = Counter(tokens)
        total = len(tokens)
        return sum((tf[t] / total) * _idf(t) for t in tokens) / len(tokens)

    scored = [(i, sentences[i], _score(sent_tokens[i])) for i in range(N)]
    threshold = sorted([x[2] for x in scored], reverse=True)[
        max(0, int(len(scored) * keep_ratio) - 1)
    ]
    kept = [s for i, s, score in scored if score >= threshold]
    return " ".join(kept)


# ─── TEXTRANK COMPRESSION ────────────────────────────────────────────────────

def _similarity(tokens_a: set, tokens_b: set) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    denom = math.log(len(tokens_a) + 1) + math.log(len(tokens_b) + 1)
    return len(intersection) / denom if denom else 0.0


def textrank_compress(text: str, keep_ratio: float = 0.5, damping: float = 0.85, iterations: int = 30) -> str:
    """
    PageRank-style sentence scoring. Keep top `keep_ratio` sentences by rank.
    """
    sentences = _split_sentences(text)
    if len(sentences) <= 3:
        return text

    sent_tokens = [
        set(_tokenize(s)) - STOPWORDS
        for s in sentences
    ]
    N = len(sentences)

    # Build similarity matrix
    sim: List[List[float]] = [[0.0] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            if i != j:
                sim[i][j] = _similarity(sent_tokens[i], sent_tokens[j])

    # Normalize rows
    for i in range(N):
        row_sum = sum(sim[i]) or 1
        sim[i] = [v / row_sum for v in sim[i]]

    # Power iteration
    scores = [1.0 / N] * N
    for _ in range(iterations):
        new_scores = [
            (1 - damping) / N + damping * sum(sim[j][i] * scores[j] for j in range(N))
            for i in range(N)
        ]
        scores = new_scores

    # Keep top keep_ratio sentences, preserve original order
    n_keep = max(1, int(N * keep_ratio))
    top_indices = set(sorted(range(N), key=lambda i: scores[i], reverse=True)[:n_keep])
    kept = [sentences[i] for i in range(N) if i in top_indices]
    return " ".join(kept)
