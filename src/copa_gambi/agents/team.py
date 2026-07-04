from agno.team import Team
from agno.team.mode import TeamMode
from agno.tools.reasoning import ReasoningTools

from copa_gambi.agents.factory import build_model, make_agent
from copa_gambi.core.capabilities import resolve_capabilities
from copa_gambi.core.config import Settings, settings
from copa_gambi.core.hub import elect_moderator, fetch_participants
from copa_gambi.core.schemas import Participant
from copa_gambi.instructions import MODERATOR_INSTRUCTIONS, TEAM_NAME
from copa_gambi.skills import load_shared_skills
from copa_gambi.tools.registry import load_default_tools


def build_team(participants: list[Participant], cfg: Settings = settings) -> Team:
    moderator = elect_moderator(participants)
    shared_skills = load_shared_skills(cfg)
    shared_tools = load_default_tools(cfg)
    debaters = [
        make_agent(p, cfg, skills=shared_skills, tools=shared_tools)
        for p in participants
        if p.participant_id != moderator.participant_id
    ]

    moderator_tools = (
        [ReasoningTools(add_instructions=True)]
        if resolve_capabilities(moderator, cfg).use_tools
        else []
    )

    return Team(
        name=TEAM_NAME,
        mode=TeamMode.broadcast,
        model=build_model(moderator, cfg),
        members=debaters,
        tools=moderator_tools,
        instructions=MODERATOR_INSTRUCTIONS,
        show_members_responses=True,
        markdown=True,
    )


def build_team_from_hub(cfg: Settings = settings) -> Team:
    return build_team(fetch_participants(cfg), cfg)
