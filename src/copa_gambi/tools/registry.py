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

from copa_gambi.core.config import Settings, settings
from copa_gambi.tools.sentiment import SentimentTools
from copa_gambi.tools.stats import FootballDataTools

logger = logging.getLogger(__name__)


def load_default_tools(cfg: Settings = settings) -> list[Any]:
    tools: list[Any] = [
        DuckDuckGoTools(enable_news=True, fixed_max_results=5),
        SentimentTools(
            reddit_client_id=cfg.reddit_client_id,
            reddit_client_secret=cfg.reddit_client_secret,
            reddit_user_agent=cfg.reddit_user_agent,
        ),
    ]

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
