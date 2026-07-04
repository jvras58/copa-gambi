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


class Participant(BaseModel):
    model_config = ConfigDict(extra="allow")

    participant_id: str = Field(description="Stable id chosen at `gambi participant join` time.")
    model: str = Field(description="Local model id (e.g. llama3.3:70b).")
    specs: ParticipantSpecs = Field(default_factory=ParticipantSpecs)
    endpoint: str | None = None

    @property
    def unique_id(self) -> str:
        return f"{self.participant_id}::{self.model}"
