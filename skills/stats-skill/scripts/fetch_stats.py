"""Fetch match statistics. Replace the stub call with the real provider."""

from __future__ import annotations

import json
import os
import sys

import httpx

API_BASE = "https://api.football-data.org/v4"


def fetch(team_a: str, team_b: str, *, token: str | None = None) -> dict:
    headers = {"X-Auth-Token": token} if token else {}
    params = {"home": team_a, "away": team_b}
    response = httpx.get(f"{API_BASE}/matches", params=params, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: fetch_stats.py <team_a> <team_b>", file=sys.stderr)
        raise SystemExit(2)
    token = os.environ.get("COPA_FOOTBALL_DATA_TOKEN")
    print(json.dumps(fetch(sys.argv[1], sys.argv[2], token=token), indent=2, ensure_ascii=False))
