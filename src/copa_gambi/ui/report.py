"""Tolerant extraction of the structured appendix from the moderator report.

The moderator is instructed to end the markdown report with a fenced ```json
block matching `DebateReport`. Parsing must never be load-bearing: broken JSON
goes through json-repair first, and when nothing validates the caller renders
the raw markdown instead.
"""

import json
import re

import json_repair
from pydantic import ValidationError

from copa_gambi.core.schemas import DebateReport

_FENCED_BLOCK = re.compile(r"```[\w-]*[ \t]*\n(.*?)```", re.DOTALL)


def _validate(raw: str) -> DebateReport | None:
    """Strict json first; then json-repair for the usual small-model damage
    (single quotes, trailing commas, missing closing brace)."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = json_repair.loads(raw)
    if not isinstance(data, dict):
        return None
    try:
        return DebateReport.model_validate(data)
    except ValidationError:
        return None


def parse_report(text: str) -> DebateReport | None:
    """Return the report from the last candidate that validates, else None.

    Candidates: fenced code blocks (last first), then — for moderators that
    skip the fence entirely — the outermost brace-delimited slice of the text.
    """
    text = text or ""
    for block in reversed(_FENCED_BLOCK.findall(text)):
        report = _validate(block)
        if report is not None:
            return report

    start, end = text.find("{"), text.rfind("}")
    if 0 <= start < end:
        return _validate(text[start : end + 1])
    return None


def strip_report_blocks(text: str) -> str:
    """Remove fenced blocks that validate as `DebateReport` from the markdown.

    Keeps other fenced blocks intact — only the structured appendix is
    redundant once the UI renders it as panels.
    """

    def _replace(match: re.Match[str]) -> str:
        return match.group(0) if _validate(match.group(1)) is None else ""

    return _FENCED_BLOCK.sub(_replace, text or "").strip()


_SCORE = re.compile(r"\b(\d{1,2})\s*[x×:-]\s*(\d{1,2})\b")  # noqa: RUF001


def guess_score(text: str) -> str | None:
    """Best-effort score badge for a debater's free-form response."""
    match = _SCORE.search(text or "")
    return f"{match.group(1)} x {match.group(2)}" if match else None
