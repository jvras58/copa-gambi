from agno.team import Team
from agno.team.mode import TeamMode
from agno.tools.reasoning import ReasoningTools

from copa_gambi.agents.factory import build_model, make_agent
from copa_gambi.agents.instructions import MODERATOR_INSTRUCTIONS, TEAM_NAME
from copa_gambi.agents.skills import load_shared_skills
from copa_gambi.core.config import Settings, settings
from copa_gambi.core.hub import elect_moderator, fetch_participants
from copa_gambi.core.schemas import Participant


def build_team(participants: list[Participant], cfg: Settings = settings) -> Team:
    moderator = elect_moderator(participants)
    shared_skills = load_shared_skills(cfg)
    debaters = [
        make_agent(p, cfg, skills=shared_skills)
        for p in participants
        if p.participant_id != moderator.participant_id
    ]

    return Team(
        name=TEAM_NAME,
        mode=TeamMode.broadcast,
        model=build_model(moderator, cfg),
        members=debaters,
        tools=[ReasoningTools(add_instructions=True)],
        instructions=MODERATOR_INSTRUCTIONS,
        show_members_responses=True,
        markdown=True,
    )


def build_team_from_hub(cfg: Settings = settings) -> Team:
    return build_team(fetch_participants(cfg), cfg)
