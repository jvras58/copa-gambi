from pydantic import BaseModel, ConfigDict, Field


class ParticipantSpecs(BaseModel):
    model_config = ConfigDict(extra="allow")

    gpu_vram_gb: float = Field(
        default=0.0,
        description="GPU VRAM (GB). Used to elect the moderator.",
    )
    cpu_cores: int | None = None
    ram_gb: float | None = None

    supports_tools: bool | None = Field(
        default=None,
        description=(
            "Whether the model can do function calling. None = unknown, "
            "decided by the COPA_NO_TOOLS_MODELS setting."
        ),
    )
    supports_skills: bool | None = Field(
        default=None,
        description=(
            "Whether the model can follow the skill workflow. None = unknown, "
            "decided by the COPA_NO_SKILLS_MODELS setting. Skills are accessed "
            "through tool calls, so supports_tools=False also disables skills."
        ),
    )


class ScoreGroup(BaseModel):
    """One cluster of models that converged on the same predicted score."""

    score: str = Field(description='Predicted score, e.g. "2x1".')
    models: list[str] = Field(default_factory=list)
    percentage: float = Field(default=0.0, description="Share of models in this group (0-100).")
    arguments: list[str] = Field(default_factory=list)


class DebateReport(BaseModel):
    """Structured appendix the moderator is asked to emit as a fenced JSON block.

    Weak models may skip or mangle the block — the UI treats parsing failure
    as cosmetic and falls back to the raw markdown report.
    """

    groups: list[ScoreGroup] = Field(default_factory=list)
    final_score: str = Field(description="The winning prediction.")
    rationale: str = ""


class Participant(BaseModel):
    model_config = ConfigDict(extra="allow")

    participant_id: str = Field(description="Stable id chosen at `gambi participant join` time.")
    model: str = Field(description="Local model id (e.g. llama3.3:70b).")
    specs: ParticipantSpecs = Field(default_factory=ParticipantSpecs)
    endpoint: str | None = None

    @property
    def unique_id(self) -> str:
        return f"{self.participant_id}::{self.model}"
