"""Tolerant extraction of the structured appendix from the moderator report.

The moderator is instructed to end the markdown report with a fenced ```json
block matching `DebateReport`. Parsing must never be load-bearing: when the
block is missing or broken the caller renders the raw markdown instead.
"""

import json
import re

from pydantic import ValidationError

from copa_gambi.core.schemas import DebateReport

# Accepts any language tag: matching only ```json would desync the fence
# pairing when other fenced blocks precede it — Pydantic validation is what
# decides whether a block is the structured appendix.
_FENCED_BLOCK = re.compile(r"```[\w-]*[ \t]*\n(.*?)```", re.DOTALL)


def parse_report(text: str) -> DebateReport | None:
    """Return the report from the last fenced block that validates, else None."""
    for block in reversed(_FENCED_BLOCK.findall(text or "")):
        try:
            return DebateReport.model_validate(json.loads(block))
        except (json.JSONDecodeError, ValidationError):
            continue
    return None


def strip_report_blocks(text: str) -> str:
    """Remove fenced blocks that validate as `DebateReport` from the markdown.

    Keeps other fenced blocks intact — only the structured appendix is
    redundant once the UI renders it as panels.
    """

    def _replace(match: re.Match[str]) -> str:
        try:
            DebateReport.model_validate(json.loads(match.group(1)))
        except (json.JSONDecodeError, ValidationError):
            return match.group(0)
        return ""

    return _FENCED_BLOCK.sub(_replace, text or "").strip()


# The multiplication sign in the class is deliberate: models write the score
# both with the letter x and with the unicode times sign.
_SCORE = re.compile(r"\b(\d{1,2})\s*[x×:-]\s*(\d{1,2})\b")  # noqa: RUF001


def guess_score(text: str) -> str | None:
    """Best-effort score badge for a debater's free-form response."""
    match = _SCORE.search(text or "")
    return f"{match.group(1)} x {match.group(2)}" if match else None
