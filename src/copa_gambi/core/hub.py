import httpx

from copa_gambi.core.config import Settings, settings
from copa_gambi.core.schemas import Participant


class HubError(RuntimeError):
    """Raised when the Gambi Hub cannot be reached or returns invalid data."""


def fetch_participants(cfg: Settings = settings) -> list[Participant]:
    """Fetch participants currently connected to the configured room."""
    try:
        response = httpx.get(cfg.participants_url(), timeout=cfg.request_timeout)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HubError(f"failed to reach Gambi Hub at {cfg.participants_url()}: {exc}") from exc

    payload = response.json()
    if not isinstance(payload, list):
        raise HubError(f"unexpected payload from Hub (expected list, got {type(payload).__name__})")

    return [Participant.model_validate(item) for item in payload]


def elect_moderator(participants: list[Participant]) -> Participant:
    """Pick the participant with the highest GPU VRAM to act as moderator."""
    if not participants:
        raise HubError("room has no participants — start at least one `gambi participant join`.")
    return max(participants, key=lambda p: p.specs.gpu_vram_gb)
