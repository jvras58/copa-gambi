from pydantic import BaseModel, ConfigDict, Field


class ParticipantSpecs(BaseModel):
    model_config = ConfigDict(extra="allow")

    gpu_vram_gb: float = Field(
        default=0.0,
        description="GPU VRAM (GB). Used to elect the moderator.",
    )
    cpu_cores: int | None = None
    ram_gb: float | None = None


class Participant(BaseModel):
    model_config = ConfigDict(extra="allow")

    participant_id: str = Field(description="Stable id chosen at `gambi participant join` time.")
    model: str = Field(description="Local model id (e.g. llama3.3:70b).")
    specs: ParticipantSpecs = Field(default_factory=ParticipantSpecs)
    endpoint: str | None = None

    @property
    def unique_id(self) -> str:
        return f"{self.participant_id}::{self.model}"
