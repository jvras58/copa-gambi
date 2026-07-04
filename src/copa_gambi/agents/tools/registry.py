"""Compose the default tool list for debater agents.

Each tool is optional: when the corresponding credential is missing in
`Settings` the tool is just skipped, instead of raising. DuckDuckGo needs
no credential and is always on.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.exa import ExaTools
from agno.tools.reddit import RedditTools

from copa_gambi.agents.tools.stats import FootballDataTools
from copa_gambi.core.config import Settings, settings

logger = logging.getLogger(__name__)


def load_default_tools(cfg: Settings = settings) -> list[Any]:
    tools: list[Any] = [DuckDuckGoTools(enable_news=True, fixed_max_results=5)]

    if cfg.reddit_client_id and cfg.reddit_client_secret:
        tools.append(
            RedditTools(
                client_id=cfg.reddit_client_id,
                client_secret=cfg.reddit_client_secret,
                user_agent=cfg.reddit_user_agent,
            )
        )
    else:
        logger.info("RedditTools skipped: COPA_REDDIT_CLIENT_ID/SECRET not set.")

    if cfg.football_data_token:
        tools.append(FootballDataTools(token=cfg.football_data_token))
    else:
        logger.info("FootballDataTools skipped: COPA_FOOTBALL_DATA_TOKEN not set.")

    if cfg.exa_api_key:
        # Semantic search restricted to the last 30 days: stale takes about a
        # squad are worse than no take at all. Only search + get_contents are
        # exposed to keep the tool surface small for local models.
        month_ago = (datetime.now(tz=UTC) - timedelta(days=30)).strftime("%Y-%m-%d")
        tools.append(
            ExaTools(
                api_key=cfg.exa_api_key,
                enable_find_similar=False,
                enable_answer=False,
                num_results=5,
                start_published_date=month_ago,
            )
        )
    else:
        logger.info("ExaTools skipped: COPA_EXA_API_KEY not set.")

    return tools
