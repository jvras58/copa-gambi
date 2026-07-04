"""Decide which capabilities (tools, skills) each participant's model gets.

A weak local model must still be able to debate: instead of crashing on a
function call it cannot emit, it joins without tools and/or skills and argues
from its own knowledge. Resolution order for tools:

1. explicit `ParticipantSpecs.supports_tools` flag (the participant knows best);
2. COPA_NO_TOOLS_MODELS model-id substring match;
3. preflight probe against the participant's endpoint (COPA_PREFLIGHT_PROBE);
4. default: capable.

Skills cannot be probed (following the workflow is behavioral, not an API
feature), so they stay declarative — spec flag, then COPA_NO_SKILLS_MODELS.
"""

import logging
from dataclasses import dataclass

import httpx

from copa_gambi.core.config import Settings, settings
from copa_gambi.core.schemas import Participant

logger = logging.getLogger(__name__)

# Minimal no-op tool sent in the probe request: we only care whether the
# server accepts the `tools` field for this model, not what the model answers.
_PROBE_TOOL = {
    "type": "function",
    "function": {
        "name": "noop",
        "description": "capability probe",
        "parameters": {"type": "object", "properties": {}},
    },
}


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


def probe_tools_support(participant: Participant, cfg: Settings = settings) -> bool | None:
    """Ask the participant's endpoint for one token with a dummy tool attached.

    Returns True/False when the server answers conclusively, or None when the
    probe is inconclusive (network error, unrelated 4xx/5xx) — inconclusive
    must never downgrade a participant, since the debate will surface the real
    error anyway.
    """
    base = (participant.endpoint or cfg.openai_base_url).rstrip("/")
    payload = {
        "model": participant.model,
        "messages": [{"role": "user", "content": "ping"}],
        "tools": [_PROBE_TOOL],
        "max_tokens": 1,
    }
    try:
        response = httpx.post(
            f"{base}/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {cfg.api_key}"},
            timeout=cfg.request_timeout,
        )
    except httpx.HTTPError as exc:
        logger.warning(
            "%s: tools probe unreachable (%s); assuming capable.", participant.unique_id, exc
        )
        return None

    if response.is_success:
        return True
    # Ollama-style servers reject unsupported models with a 4xx whose body
    # mentions tools (e.g. "llama3.2:1b does not support tools").
    if 400 <= response.status_code < 500 and "tool" in response.text.lower():
        return False
    logger.warning(
        "%s: tools probe inconclusive (HTTP %s); assuming capable.",
        participant.unique_id,
        response.status_code,
    )
    return None


def resolve_capabilities(participant: Participant, cfg: Settings = settings) -> Capabilities:
    """Resolve tools/skills for one participant. May issue the probe request."""
    use_tools = participant.specs.supports_tools
    if use_tools is None and _matches_any(participant.model, cfg.no_tools_models):
        use_tools = False
    if use_tools is None and cfg.preflight_probe:
        use_tools = probe_tools_support(participant, cfg)
        if use_tools is False:
            logger.info("%s: endpoint rejected tools; joining without them.", participant.unique_id)
    if use_tools is None:
        use_tools = True

    use_skills = participant.specs.supports_skills
    if use_skills is None:
        use_skills = not _matches_any(participant.model, cfg.no_skills_models)

    # Skills are exercised through the get_skill_* tool calls, so a model that
    # cannot do function calling cannot use skills either.
    if not use_tools:
        use_skills = False

    return Capabilities(use_tools=use_tools, use_skills=use_skills)
