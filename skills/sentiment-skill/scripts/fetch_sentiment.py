"""Aggregate public sentiment around a matchup. Plug your providers in fetch_*()."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass


@dataclass(slots=True)
class SentimentSample:
    source: str
    score: float  # -1.0 (negative) .. 1.0 (positive)
    text: str


def fetch_x(query: str) -> list[SentimentSample]:
    # TODO: wire up X/Twitter API. Returning empty by default.
    _ = query
    return []


def fetch_reddit(query: str) -> list[SentimentSample]:
    # TODO: wire up Reddit API.
    _ = query
    return []


def aggregate(samples: list[SentimentSample]) -> dict:
    if not samples:
        return {"count": 0, "avg_score": 0.0, "by_source": {}}

    by_source: dict[str, list[float]] = {}
    for s in samples:
        by_source.setdefault(s.source, []).append(s.score)

    return {
        "count": len(samples),
        "avg_score": sum(s.score for s in samples) / len(samples),
        "by_source": {src: sum(scores) / len(scores) for src, scores in by_source.items()},
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('usage: fetch_sentiment.py "Brasil x Argentina"', file=sys.stderr)
        raise SystemExit(2)
    query = sys.argv[1]
    samples = fetch_x(query) + fetch_reddit(query)
    print(json.dumps(aggregate(samples), indent=2, ensure_ascii=False))
