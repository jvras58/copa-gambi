"""Decide which capabilities (tools, skills) each participant's model gets.

A weak local model must still be able to debate: instead of crashing on a
function call it cannot emit, it joins without tools and/or skills and argues
from its own knowledge. Explicit `ParticipantSpecs` flags win; when the spec
is unknown (None), the COPA_NO_TOOLS_MODELS / COPA_NO_SKILLS_MODELS settings
decide by model-id substring; the default is fully capable.
"""

from dataclasses import dataclass

from copa_gambi.core.config import Settings, settings
from copa_gambi.core.schemas import Participant


@dataclass(frozen=True, slots=True)
class Capabilities:
    use_tools: bool
    use_skills: bool

    @property
    def research_capable(self) -> bool:
        return self.use_tools or self.use_skills


def _matches_any(model_id: str, patterns: str) -> bool:
    model_lower = model_id.lower()
    return any(p.strip().lower() in model_lower for p in patterns.split(",") if p.strip())


def resolve_capabilities(participant: Participant, cfg: Settings = settings) -> Capabilities:
    use_tools = participant.specs.supports_tools
    if use_tools is None:
        use_tools = not _matches_any(participant.model, cfg.no_tools_models)

    use_skills = participant.specs.supports_skills
    if use_skills is None:
        use_skills = not _matches_any(participant.model, cfg.no_skills_models)

    # Skills are exercised through the get_skill_* tool calls, so a model that
    # cannot do function calling cannot use skills either.
    if not use_tools:
        use_skills = False

    return Capabilities(use_tools=use_tools, use_skills=use_skills)
