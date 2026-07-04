"""CLI wrapper over the shared sentiment pipeline.

The actual logic lives in `copa_gambi.tools.sentiment` (single source of
truth, also exposed to agents as the SentimentTools toolkit). This script
only parses arguments, reads Reddit credentials from the environment and
prints the aggregate as JSON.

Usage:
    python fetch_sentiment.py "Brasil x Argentina" [--days 14] [--max-per-query 10]
"""

import argparse
import json
import logging
import os
import sys

from copa_gambi.tools.sentiment import (
    DEFAULT_MAX_PER_QUERY,
    DEFAULT_WINDOW_DAYS,
    aggregate,
    collect_items,
    dedupe,
)


def main() -> None:
    # Windows defaults stdout to cp1252, which chokes on emoji in post titles.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr, format="[warn] %(message)s")

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("matchup", help='ex.: "Brasil x Argentina"')
    parser.add_argument(
        "--days",
        type=int,
        default=DEFAULT_WINDOW_DAYS,
        help=f"janela temporal em dias (default: {DEFAULT_WINDOW_DAYS})",
    )
    parser.add_argument(
        "--max-per-query",
        type=int,
        default=DEFAULT_MAX_PER_QUERY,
        help=f"máximo de itens por query por fonte (default: {DEFAULT_MAX_PER_QUERY})",
    )
    args = parser.parse_args()

    items = collect_items(
        args.matchup,
        days=args.days,
        max_per_query=args.max_per_query,
        reddit_client_id=os.environ.get("COPA_REDDIT_CLIENT_ID"),
        reddit_client_secret=os.environ.get("COPA_REDDIT_CLIENT_SECRET"),
        reddit_user_agent=os.environ.get("COPA_REDDIT_USER_AGENT", "copa-gambi/0.1 (sentiment)"),
    )
    print(json.dumps(aggregate(dedupe(items), args.days), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
