"""Debate orchestration for the web UI — no Streamlit imports here.

Keeping this module UI-framework-free means the same setup/run helpers can be
reused by tests or another front end.
"""

from dataclasses import dataclass

from agno.run.team import TeamRunOutput

from copa_gambi.agents.team import build_team
from copa_gambi.core.capabilities import Capabilities, resolve_capabilities
from copa_gambi.core.config import Settings, settings
from copa_gambi.core.hub import elect_moderator, fetch_participants
from copa_gambi.core.schemas import Participant


@dataclass(frozen=True, slots=True)
class ParticipantView:
    participant: Participant
    caps: Capabilities
    is_moderator: bool

    @property
    def label(self) -> str:
        return self.participant.unique_id


@dataclass(frozen=True, slots=True)
class DebateSetup:
    views: list[ParticipantView]

    @property
    def participants(self) -> list[Participant]:
        return [v.participant for v in self.views]

    def caps_for(self, agent_name: str) -> Capabilities | None:
        for view in self.views:
            if view.label == agent_name:
                return view.caps
        return None


def load_setup(cfg: Settings = settings) -> DebateSetup:
    """Fetch the room and resolve, per participant, moderator role and capabilities."""
    participants = fetch_participants(cfg)
    moderator = elect_moderator(participants)
    return DebateSetup(
        views=[
            ParticipantView(
                participant=p,
                caps=resolve_capabilities(p, cfg),
                is_moderator=p.participant_id == moderator.participant_id,
            )
            for p in participants
        ]
    )


def run_debate(matchup: str, setup: DebateSetup, cfg: Settings = settings) -> TeamRunOutput:
    team = build_team(setup.participants, cfg)
    return team.run(matchup)
