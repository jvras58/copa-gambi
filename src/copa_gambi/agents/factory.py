import logging
from typing import Any

from agno.agent import Agent
from agno.models.openai.like import OpenAILike
from agno.skills import Skills

from copa_gambi.core.capabilities import resolve_capabilities
from copa_gambi.core.config import Settings, settings
from copa_gambi.core.instructions import (
    AGENT_ROLE,
    NO_RESEARCH_INSTRUCTIONS,
    SHARED_INSTRUCTIONS,
)
from copa_gambi.core.schemas import Participant
from copa_gambi.core.skill_loader import load_shared_skills
from copa_gambi.tools.registry import load_default_tools

logger = logging.getLogger(__name__)


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
    """Build a debater agent, degrading gracefully for less capable models.

    `skills`/`tools` are the shared instances built once per team; whether this
    participant actually receives them is decided per model, so a model without
    function calling still joins the debate arguing from its own knowledge.
    """
    caps = resolve_capabilities(participant, cfg)
    instructions = list(SHARED_INSTRUCTIONS)
    if not caps.research_capable:
        instructions += NO_RESEARCH_INSTRUCTIONS
        logger.info(
            "%s: no tools/skills — debating from model knowledge only.", participant.unique_id
        )
    elif not caps.use_skills:
        logger.info("%s: tools only, skills disabled.", participant.unique_id)

    return Agent(
        name=participant.unique_id,
        model=build_model(participant, cfg),
        role=AGENT_ROLE,
        instructions=instructions,
        skills=(skills if skills is not None else load_shared_skills(cfg))
        if caps.use_skills
        else None,
        tools=(tools if tools is not None else load_default_tools(cfg)) if caps.use_tools else None,
    )
