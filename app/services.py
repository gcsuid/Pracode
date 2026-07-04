from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Iterable

DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "by",
    "for",
    "from",
    "get",
    "how",
    "if",
    "in",
    "is",
    "it",
    "must",
    "of",
    "on",
    "or",
    "return",
    "show",
    "the",
    "their",
    "to",
    "use",
    "using",
    "with",
    "without",
    "you",
}

PATTERN_RULES = [
    ("Sliding Window", ("sliding window", "window", "substring", "subarray", "contiguous")),
    ("Two Pointers", ("two pointers", "two pointer", "left and right", "left/right", "inward pointers")),
    ("Binary Search", ("binary search", "lower bound", "upper bound", "mid point", "monotonic")),
    ("Dynamic Programming", ("dynamic programming", "memo", "memoization", "dp", "state transition")),
    ("Depth First Search", ("depth first search", "dfs", "backtracking", "recursion", "tree traversal")),
    ("Breadth First Search", ("breadth first search", "bfs", "level order", "queue traversal", "graph traversal")),
    ("Greedy", ("greedy", "locally optimal", "sort then choose", "choose the best")),
    ("Backtracking", ("backtracking", "branch and bound", "choose explore unchoose")),
    ("Stack", ("stack", "monotonic stack", "nested expression", "parentheses")),
    ("Queue", ("queue", "deque", "breadth", "level order")),
    ("Heap", ("heap", "priority queue", "top k", "k largest", "k smallest")),
    ("Trie", ("trie", "prefix tree", "dictionary tree")),
    ("Prefix Sum", ("prefix sum", "running sum", "cumulative sum", "difference array")),
    ("Union Find", ("union find", "disjoint set", "connected components")),
    ("Topological Sort", ("topological", "dependency order", "dag", "prerequisite")),
    ("Linked List", ("linked list", "fast and slow", "list node", "pointer manipulation")),
    ("Tree", ("binary tree", "tree", "inorder", "preorder", "postorder")),
    ("Graph", ("graph", "node", "edge", "adjacency", "shortest path")),
]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _tokenize(value: str) -> list[str]:
    cleaned = re.sub(r"[^a-z0-9\s]+", " ", value.lower())
    return [token for token in cleaned.split() if token and token not in STOPWORDS]


def _unique_preserve_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def _ollama_host() -> str:
    return os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST).rstrip("/")


def _ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)


def _ai_provider() -> str:
    return os.getenv("AI_PROVIDER", "ollama").strip().lower()


def _use_ollama() -> bool:
    return _ai_provider() == "ollama" and _ollama_is_available()


@lru_cache(maxsize=1)
def _ollama_is_available() -> bool:
    request = urllib.request.Request(f"{_ollama_host()}/api/tags", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=1.0):
            return True
    except Exception:
        return False


def _ollama_generate(prompt: str) -> str:
    payload = {
        "model": _ollama_model(),
        "prompt": prompt,
        "stream": False,
    }
    request = urllib.request.Request(
        f"{_ollama_host()}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=6.0) as response:
        data = json.loads(response.read().decode("utf-8"))
    text = data.get("response") or data.get("message", {}).get("content") or ""
    return text.strip()


def _canonical_pattern(text: str) -> str:
    normalized = _normalize_text(text)
    for pattern, keywords in PATTERN_RULES:
        if pattern.lower() in normalized:
            return pattern
        if any(keyword in normalized for keyword in keywords):
            return pattern
    return "Unknown"


def detect_pattern(approach: str) -> str:
    if _use_ollama():
        prompt = (
            "Classify the primary DSA pattern in the following approach.\n"
            "Return only one concise pattern name from this set if possible: "
            "Sliding Window, Two Pointers, Binary Search, Dynamic Programming, "
            "Depth First Search, Breadth First Search, Greedy, Backtracking, Stack, Queue, Heap, Trie, Prefix Sum, Union Find, Topological Sort, Linked List, Tree, Graph.\n"
            f"Approach: {approach}"
        )
        try:
            return _canonical_pattern(_ollama_generate(prompt))
        except Exception:
            pass
    return _canonical_pattern(approach)


def rephrase_question(title: str, approach: str) -> str:
    prompt_seed = (
        "Rewrite this DSA practice prompt so it feels new while preserving the same logic, "
        "constraints, and reasoning target. Return one sentence.\n"
        f"Problem title: {title}\n"
        f"Known solution clue: {approach}"
    )
    if _use_ollama():
        try:
            rephrased = _ollama_generate(prompt_seed)
            if rephrased:
                return rephrased
        except Exception:
            pass

    pattern = detect_pattern(approach)
    base = title.strip() or "the original problem"
    if pattern == "Unknown":
        return f"Practice prompt: solve {base} while preserving the original constraints and edge cases."
    return f"Practice prompt: revisit {base} with a {pattern.lower()} strategy and keep the same constraints in focus."


def evaluate_recall(expected_approach: str, recall_attempt: str) -> dict[str, object]:
    expected_tokens = _tokenize(expected_approach)
    attempt_tokens = set(_tokenize(recall_attempt))
    common_tokens = _unique_preserve_order(token for token in expected_tokens if token in attempt_tokens)

    expected_patterns = [pattern for pattern, _ in PATTERN_RULES if pattern.lower() in expected_approach.lower()]
    if not expected_patterns:
        extracted = detect_pattern(expected_approach)
        if extracted != "Unknown":
            expected_patterns.append(extracted)

    strengths = list(common_tokens[:6])
    if expected_patterns and any(pattern.lower() in recall_attempt.lower() for pattern in expected_patterns):
        strengths = _unique_preserve_order([*strengths, *expected_patterns])

    missing_concepts = [token for token in expected_tokens if token not in attempt_tokens]
    if expected_patterns and not any(pattern.lower() in recall_attempt.lower() for pattern in expected_patterns):
        missing_concepts = [*expected_patterns, *missing_concepts]
    missing_concepts = _unique_preserve_order(missing_concepts)[:6]

    coverage = len(common_tokens) / max(1, len(_unique_preserve_order(expected_tokens)))
    score = round(min(100, 25 + coverage * 70))
    if expected_patterns and any(pattern.lower() in recall_attempt.lower() for pattern in expected_patterns):
        score = min(100, score + 10)
    if len(recall_attempt.strip()) < 20:
        score = max(0, score - 15)

    if score >= 90:
        feedback = "Strong recall. You captured the core strategy and most supporting details."
    elif score >= 70:
        feedback = "Good recall. The main approach is present, but a few supporting ideas are missing."
    elif score >= 50:
        feedback = "Partial recall. You remembered part of the approach, but some important steps are missing."
    else:
        feedback = "Needs review. The response misses key parts of the stored approach."

    if missing_concepts:
        feedback = f"{feedback} Missing concepts: {', '.join(missing_concepts)}."

    return {
        "score": score,
        "strengths": strengths,
        "missing_concepts": missing_concepts,
        "feedback": feedback,
    }


def build_review_schedule(
    score: int,
    current_interval_days: int | None = None,
    review_count: int = 0,
    reference_time: datetime | None = None,
) -> dict[str, object]:
    base_time = reference_time or now_utc()
    if score >= 90:
        interval_days = max((current_interval_days or 7) * 2, 7)
    elif score >= 75:
        interval_days = max((current_interval_days or 3) + 2, 3)
    elif score >= 50:
        interval_days = max(current_interval_days or 2, 1)
    else:
        interval_days = 1

    return {
        "interval_days": interval_days,
        "review_count": review_count + 1,
        "next_review_at": base_time + timedelta(days=interval_days),
        "updated_at": base_time,
    }
