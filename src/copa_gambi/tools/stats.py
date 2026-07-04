"""football-data.org Agno toolkit.

Free tier: 10 requests/minute, no card required. Sign up at
https://www.football-data.org/client/register and put the token in
COPA_FOOTBALL_DATA_TOKEN.
"""

from typing import Any

import httpx
from agno.tools import Toolkit

API_BASE = "https://api.football-data.org/v4"


class FootballDataTools(Toolkit):
    def __init__(self, token: str, timeout: float = 15.0) -> None:
        self._token = token
        self._timeout = timeout
        super().__init__(
            name="football_data",
            tools=[self.search_team, self.recent_matches, self.head_to_head],
            instructions=(
                "Use football_data tools to ground predictions in real numbers. "
                "Call search_team first to resolve a team name into an id, then "
                "recent_matches for form and head_to_head for the rivalry history."
            ),
            add_instructions=True,
        )

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = httpx.get(
            f"{API_BASE}{path}",
            params=params,
            headers={"X-Auth-Token": self._token},
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()

    def search_team(self, name: str) -> dict[str, Any]:
        """Resolve a team name into a football-data.org team id and short name."""
        data = self._get("/teams", params={"name": name})
        teams = [
            {
                "id": t["id"],
                "name": t["name"],
                "tla": t.get("tla"),
                "area": t.get("area", {}).get("name"),
            }
            for t in data.get("teams", [])
        ]
        return {"query": name, "matches": teams[:10]}

    def recent_matches(self, team_id: int, limit: int = 5) -> dict[str, Any]:
        """Last `limit` finished matches for a team — score, opponent and date."""
        data = self._get(
            f"/teams/{team_id}/matches",
            params={"status": "FINISHED", "limit": limit},
        )
        return {
            "team_id": team_id,
            "matches": [
                {
                    "date": m.get("utcDate"),
                    "home": m["homeTeam"]["name"],
                    "away": m["awayTeam"]["name"],
                    "score": m.get("score", {}).get("fullTime"),
                    "competition": m.get("competition", {}).get("name"),
                }
                for m in data.get("matches", [])
            ],
        }

    def head_to_head(self, match_id: int, limit: int = 10) -> dict[str, Any]:
        """Direct-confrontation history around a given match id."""
        data = self._get(f"/matches/{match_id}/head2head", params={"limit": limit})
        return {
            "aggregates": data.get("aggregates"),
            "matches": [
                {
                    "date": m.get("utcDate"),
                    "home": m["homeTeam"]["name"],
                    "away": m["awayTeam"]["name"],
                    "score": m.get("score", {}).get("fullTime"),
                }
                for m in data.get("matches", [])
            ],
        }
