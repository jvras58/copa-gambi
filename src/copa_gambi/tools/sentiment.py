"""Typed public-sentiment pipeline plus its Agno toolkit.

Single source of truth for sentiment aggregation: the `SentimentTools`
toolkit calls it in-process and the sentiment-skill script wraps it as a CLI.

Pipeline (inspired by engagement-first research skills):
1. multi-query expansion — the matchup plus each team with its common aliases;
2. explicit time window — only items published inside `days`;
3. engagement ranking — Reddit upvotes/comments weigh more than raw hits,
   everything decays with age;
4. cross-source dedupe — the same story from news and Reddit is merged.

Sources are free: DuckDuckGo News always, Reddit only when credentials are
provided.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from agno.tools import Toolkit

logger = logging.getLogger(__name__)

DEFAULT_WINDOW_DAYS = 14
DEFAULT_MAX_PER_QUERY = 10
TOP_ITEMS_PER_TEAM = 5
REDDIT_TEXT_PREVIEW_CHARS = 500
REDDIT_COMMENT_WEIGHT = 2  # a comment signals more engagement than an upvote
MIN_RECENCY = 0.1  # oldest in-window items keep 10% of their weight
UNDATED_RECENCY = 0.5  # items without a publish date get a neutral freshness
DEDUPE_KEY_CHARS = 60

MATCHUP_SEPARATOR = re.compile(r"\s+(?:x|vs\.?)\s+", re.I)

# Common aliases/hashtags per national team: searching only the official name
# misses how fans actually talk about the squad.
TEAM_ALIASES: dict[str, list[str]] = {
    "brasil": ["Seleção Brasileira", "Brazil national team"],
    "argentina": ["Albiceleste", "Argentina national team"],
    "frança": ["Les Bleus", "France national team"],
    "alemanha": ["Die Mannschaft", "Germany national team"],
    "inglaterra": ["Three Lions", "England national team"],
    "espanha": ["La Roja", "Spain national team"],
    "portugal": ["Seleção das Quinas", "Portugal national team"],
    "uruguai": ["Celeste", "Uruguay national team"],
    "holanda": ["Oranje", "Netherlands national team"],
    "itália": ["Azzurra", "Italy national team"],
}

# Tiny PT/EN lexicon — a heuristic signal, not real NLP. Scores are meant to
# be read as "crowd leaning", never as ground truth.
POSITIVE_WORDS = {
    "vitória",
    "favorito",
    "favorita",
    "embalado",
    "embalada",
    "confiante",
    "invicto",
    "invicta",
    "goleada",
    "craque",
    "ótimo",
    "ótima",
    "recuperado",
    "win",
    "favorite",
    "confident",
    "unbeaten",
    "in-form",
    "strong",
    "boost",
}
NEGATIVE_WORDS = {
    "crise",
    "lesão",
    "lesionado",
    "desfalque",
    "derrota",
    "pressão",
    "eliminado",
    "vaiado",
    "polêmica",
    "suspenso",
    "fraco",
    "instável",
    "loss",
    "injury",
    "injured",
    "crisis",
    "doubt",
    "struggling",
    "weak",
}


@dataclass(slots=True)
class Item:
    title: str
    text: str
    url: str
    team: str  # team name, or "geral" for matchup-wide queries
    published: datetime | None
    engagement: float  # raw engagement signal (log-scaled for Reddit)
    sources: set[str] = field(default_factory=set)


def expand_queries(matchup: str) -> dict[str, list[str]]:
    """Map each target ("geral" + one entry per team) to its search queries."""
    teams = [t.strip() for t in MATCHUP_SEPARATOR.split(matchup) if t.strip()]
    queries: dict[str, list[str]] = {"geral": [matchup]}
    for team in teams:
        # The bare team name alone drags in off-topic news (economy, tourism…),
        # so it is always scoped to the tournament.
        queries[team] = [f"{team} Copa do Mundo", *TEAM_ALIASES.get(team.lower(), [])]
    return queries


def _parse_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def fetch_ddg_news(query: str, team: str, days: int, max_results: int) -> list[Item]:
    from ddgs import DDGS

    timelimit = "d" if days <= 1 else "w" if days <= 7 else "m"
    with DDGS() as ddgs:
        rows = ddgs.news(query, timelimit=timelimit, max_results=max_results) or []
    return [
        Item(
            title=r.get("title", ""),
            text=r.get("body", ""),
            url=r.get("url", ""),
            team=team,
            published=_parse_date(r.get("date")),
            engagement=1.0,  # news has no engagement metric; freshness decides
            sources={"news"},
        )
        for r in rows
    ]


def fetch_reddit(
    query: str,
    team: str,
    days: int,
    max_results: int,
    *,
    client_id: str | None,
    client_secret: str | None,
    user_agent: str = "copa-gambi/0.1 (sentiment)",
) -> list[Item]:
    if not (client_id and client_secret):
        return []

    import praw

    reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
    time_filter = "day" if days <= 1 else "week" if days <= 7 else "month" if days <= 31 else "year"
    posts = reddit.subreddit("soccer+futebol+worldcup").search(
        query, sort="top", time_filter=time_filter, limit=max_results
    )
    return [
        Item(
            title=post.title,
            text=post.selftext[:REDDIT_TEXT_PREVIEW_CHARS],
            url=f"https://reddit.com{post.permalink}",
            team=team,
            published=datetime.fromtimestamp(post.created_utc, tz=UTC),
            engagement=math.log1p(max(post.score, 0) + REDDIT_COMMENT_WEIGHT * post.num_comments),
            sources={"reddit"},
        )
        for post in posts
    ]


def collect_items(
    matchup: str,
    days: int = DEFAULT_WINDOW_DAYS,
    max_per_query: int = DEFAULT_MAX_PER_QUERY,
    *,
    reddit_client_id: str | None = None,
    reddit_client_secret: str | None = None,
    reddit_user_agent: str = "copa-gambi/0.1 (sentiment)",
) -> list[Item]:
    """Run every source for every expanded query, then drop out-of-window items.

    One dead source never kills the run — failures are logged and skipped.
    """
    items: list[Item] = []
    for team, queries in expand_queries(matchup).items():
        for query in queries:
            try:
                items.extend(fetch_ddg_news(query, team, days, max_per_query))
            except Exception as exc:
                logger.warning("fetch_ddg_news(%r): %s", query, exc)
            try:
                items.extend(
                    fetch_reddit(
                        query,
                        team,
                        days,
                        max_per_query,
                        client_id=reddit_client_id,
                        client_secret=reddit_client_secret,
                        user_agent=reddit_user_agent,
                    )
                )
            except Exception as exc:
                logger.warning("fetch_reddit(%r): %s", query, exc)

    cutoff = datetime.now(tz=UTC) - timedelta(days=days)
    return [i for i in items if i.published is None or i.published >= cutoff]


def dedupe(items: list[Item]) -> list[Item]:
    """Merge the same story seen across queries/sources, summing engagement."""
    merged: dict[str, Item] = {}
    for item in items:
        key = re.sub(r"[^a-z0-9à-ü]+", " ", item.title.lower()).strip()[:DEDUPE_KEY_CHARS]
        if not key:
            continue
        if key in merged:
            kept = merged[key]
            kept.engagement += item.engagement
            kept.sources |= item.sources
            if kept.team != item.team:
                kept.team = "geral"
        else:
            merged[key] = item
    return list(merged.values())


def lexicon_score(text: str) -> float:
    """Crowd leaning in [-1, 1]; 0.0 when no lexicon word appears."""
    words = set(re.findall(r"[\wà-ü-]+", text.lower()))
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    return 0.0 if pos + neg == 0 else (pos - neg) / (pos + neg)


def weight(item: Item, window_days: int, now: datetime) -> float:
    """Engagement scaled by freshness: an old viral post < a fresh average one."""
    recency = UNDATED_RECENCY
    if item.published:
        age_days = max((now - item.published).total_seconds() / 86400, 0.0)
        recency = max(MIN_RECENCY, 1.0 - age_days / window_days)
    return (1.0 + item.engagement) * recency


def _team_summary(team_items: list[Item], window_days: int, now: datetime) -> dict:
    weighted = [(item, weight(item, window_days, now)) for item in team_items]
    total = sum(w for _, w in weighted)
    score = (
        sum(lexicon_score(f"{i.title} {i.text}") * w for i, w in weighted) / total if total else 0.0
    )
    ranked = sorted(weighted, key=lambda pair: pair[1], reverse=True)
    return {
        "count": len(team_items),
        "weighted_score": round(score, 3),
        "top_items": [
            {
                "title": item.title,
                "url": item.url,
                "sources": sorted(item.sources),
                "published": item.published.isoformat() if item.published else None,
                "weight": round(w, 2),
            }
            for item, w in ranked[:TOP_ITEMS_PER_TEAM]
        ],
    }


def aggregate(items: list[Item], window_days: int) -> dict:
    now = datetime.now(tz=UTC)
    return {
        "window_days": window_days,
        "total_items": len(items),
        "score_scale": "-1.0 (negativo) a 1.0 (positivo), heurística por léxico",
        "by_team": {
            team: _team_summary([i for i in items if i.team == team], window_days, now)
            for team in sorted({i.team for i in items})
        },
    }


class SentimentTools(Toolkit):
    """One-call typed sentiment for a matchup, cached across the whole debate.

    All debater agents share the same toolkit instance, so `cache_results`
    means the multi-query fan-out runs once per matchup instead of once per
    agent.
    """

    def __init__(
        self,
        reddit_client_id: str | None = None,
        reddit_client_secret: str | None = None,
        reddit_user_agent: str = "copa-gambi/0.1 (sentiment)",
        cache_ttl: int = 900,
    ) -> None:
        self._reddit_client_id = reddit_client_id
        self._reddit_client_secret = reddit_client_secret
        self._reddit_user_agent = reddit_user_agent
        super().__init__(
            name="sentiment",
            tools=[self.matchup_sentiment],
            instructions=(
                "Use matchup_sentiment para obter o sentimento popular agregado "
                "sobre o confronto (score por seleção, -1 a 1, com as histórias "
                "de maior engajamento). Trate como sinal complementar, nunca "
                "como única evidência."
            ),
            add_instructions=True,
            cache_results=True,
            cache_ttl=cache_ttl,
        )

    def matchup_sentiment(self, matchup: str, days: int = DEFAULT_WINDOW_DAYS) -> dict:
        """Aggregate news/Reddit sentiment for a matchup like "Brasil x Argentina".

        Returns per-team weighted scores (-1 negative .. 1 positive) plus the
        top-engagement items backing them.
        """
        items = collect_items(
            matchup,
            days=days,
            reddit_client_id=self._reddit_client_id,
            reddit_client_secret=self._reddit_client_secret,
            reddit_user_agent=self._reddit_user_agent,
        )
        return aggregate(dedupe(items), days)
