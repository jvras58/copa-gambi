from typing import Any

from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from agno.skills import Skills

from copa_gambi.agents.instructions import AGENT_ROLE, SHARED_INSTRUCTIONS
from copa_gambi.agents.skills import load_shared_skills
from copa_gambi.agents.tools.registry import load_default_tools
from copa_gambi.core.config import Settings, settings
from copa_gambi.core.schemas import Participant


def build_model(participant: Participant, cfg: Settings = settings) -> OpenAILike:
    base_url = participant.endpoint or cfg.openai_base_url
    return OpenAILike(
        id=participant.model,
        base_url=base_url,
        api_key=cfg.api_key,
    )


def make_agent(
    participant: Participant,
    cfg: Settings = settings,
    skills: Skills | None = None,
    tools: list[Any] | None = None,
) -> Agent:
    return Agent(
        name=participant.unique_id,
        model=build_model(participant, cfg),
        role=AGENT_ROLE,
        instructions=SHARED_INSTRUCTIONS,
        skills=skills if skills is not None else load_shared_skills(cfg),
        tools=tools if tools is not None else load_default_tools(cfg),
    )
