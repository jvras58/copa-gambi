import typer

from copa_gambi.agents.team import build_team
from copa_gambi.core.config import settings
from copa_gambi.core.hub import HubError, elect_moderator, fetch_participants

app = typer.Typer(
    name="copa-gambi",
    help="Distributed multi-model World Cup score debate via Gambi Hub.",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def participants() -> None:
    """List participants currently connected to the room."""
    try:
        people = fetch_participants(settings)
    except HubError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    moderator = elect_moderator(people)
    typer.echo(f"Room {settings.room_code} — {len(people)} participant(s):")
    for p in people:
        mark = " (moderator)" if p.participant_id == moderator.participant_id else ""
        typer.echo(f"  - {p.unique_id} — gpu_vram_gb={p.specs.gpu_vram_gb}{mark}")


@app.command()
def predict(
    matchup: str = typer.Argument(..., help='e.g. "Brasil x Argentina — Copa do Mundo 2026, Fase de Grupos"'),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Stream tokens as they arrive."),
    reasoning: bool = typer.Option(True, "--reasoning/--no-reasoning", help="Show full moderator reasoning."),
) -> None:
    """Run the broadcast debate for a matchup and print the moderator report."""
    try:
        people = fetch_participants(settings)
        team = build_team(people, settings)
    except HubError as exc:
        typer.echo(f"error: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    team.print_response(matchup, stream=stream, show_full_reasoning=reasoning)
