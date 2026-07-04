from pathlib import Path

from agno.skills import LocalSkills, Skills

from copa_gambi.core.config import Settings, settings

SKILL_DIRS: tuple[str, ...] = ("stats-skill", "tactical-skill", "sentiment-skill")


def _resolve_skill_path(base: Path, name: str) -> Path:
    path = base / name
    if not path.is_dir():
        raise FileNotFoundError(
            f"skill directory not found: {path} — set COPA_SKILLS_DIR or run from the repo root."
        )
    return path


def load_shared_skills(cfg: Settings = settings) -> Skills:
    """Load the shared skills as a single Agno `Skills` container.

    `Agent.skills` takes one `Skills` instance holding every skill, not a list.
    Every debater agent gets the same container; the difference between agents
    is the local model behind each `Participant`, not the skills they can use.
    """
    base = cfg.skills_dir.resolve()
    return Skills(
        loaders=[LocalSkills(str(_resolve_skill_path(base, name))) for name in SKILL_DIRS]
    )
