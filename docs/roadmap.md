# Roadmap — copa-gambi

Checkpoint de evolução. Cada item tem **objetivo**, **onde mexer** e um **DoD** ("done when").
A ordem é uma sugestão de prioridade, não obrigatória.

---

## 1. Testes (pytest + httpx mock + agno mock)

**Objetivo.** Cobrir o que dá pra testar sem subir Hub real nem chamar LLM:
schemas, eleição do moderador, parse de payload do Hub, comportamento do CLI.

**Onde mexer.**
- Adicionar dev deps no [pyproject.toml](../pyproject.toml):
  - `pytest`, `pytest-cov`, `respx` (mock para `httpx`), `typer[all]` já cobre o CliRunner.
- Criar `tests/` (sem `__init__.py`, pytest descobre via `pyproject.toml`):
  ```
  tests/
  ├── conftest.py             # fixture: settings com hub_url fake
  ├── test_schemas.py         # Participant.unique_id, defaults, extra="allow"
  ├── test_hub.py             # respx mockando /rooms/{code}/participants
  │                           # casos: lista vazia → HubError; payload inválido; ok
  ├── test_election.py        # elect_moderator com VRAMs diferentes / empate
  └── test_cli.py             # typer.testing.CliRunner em `participants`
  ```
- Configurar pytest no `pyproject.toml`:
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  addopts = "-ra --strict-markers"
  ```

**Done when.**
- `uv run pytest` passa local.
- Cobertura ≥ 80% em `core/` e `agents/factory.py`.
- Nenhum teste depende de Hub real ou de chamada a LLM.

**Notas.**
- `agents/team.py` que toca o Agno fica fora — testar via integração só faz sentido com Hub de verdade.
- Para o CLI use `CliRunner(mix_stderr=False)` para separar stdout/stderr.

---

## 2. Workflow CI (GitHub Actions)

**Objetivo.** Em todo push/PR: lint + testes em uma matriz Python razoável.

**Onde mexer.** Criar `.github/workflows/ci.yml`:

```yaml
name: ci
on:
  push:
    branches: [main]
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true
      - run: uv python install ${{ matrix.python }}
      - run: uv sync --frozen
      - run: uv run ruff check src tests
      - run: uv run ruff format --check src tests
      - run: uv run pytest
```

**Done when.**
- Workflow verde em PR de teste.
- Badge no [README.md](../README.md).
- `uv.lock` commitado (já está) — `--frozen` garante reprodutibilidade.

**Notas.**
- Adicionar `concurrency: { group: ci-${{ github.ref }}, cancel-in-progress: true }` para não enfileirar builds em rebase.
- Se rodar custo extra: cobertura no Codecov só no merge em `main`, não em todo PR.

---

## 3. Skills como tools dos agentes (Agno)

**Objetivo.** Hoje os scripts em `skills/*/scripts/` existem mas os agentes não conseguem chamá-los.
Plugar como tools do Agno para que cada agente decida quando buscar stats / sentimento / formação.

**Onde mexer.**
- Criar `src/copa_gambi/agents/tools/` com funções/classes plugáveis:
  - `stats.py` — wrapper sobre [skills/stats-skill/scripts/fetch_stats.py](../skills/stats-skill/scripts/fetch_stats.py)
  - `sentiment.py` — wrapper sobre [skills/sentiment-skill/scripts/fetch_sentiment.py](../skills/sentiment-skill/scripts/fetch_sentiment.py)
  - `tactical.py` — lookup em [skills/tactical-skill/references/formations.md](../skills/tactical-skill/references/formations.md)
- Em [agents/factory.py](../src/copa_gambi/agents/factory.py), passar `tools=[...]` ao `Agent(...)`.
- Esquema sugerido (Agno aceita callables ou `Toolkit`):
  ```python
  Agent(
      ...,
      tools=[get_match_stats, get_public_sentiment, lookup_formation],
      show_tool_calls=True,
  )
  ```
- Cada tool deve devolver **um dict pequeno e tipado** — Pydantic ajuda a manter o contrato estável.

**Done when.**
- Pelo menos uma tool real chamada por um agente em um run de exemplo.
- Tools mockáveis em teste (não dependem de credencial em CI).
- README atualizado com "como adicionar uma skill" em uma seção.

**Notas.**
- Credenciais de APIs externas (football-data.org, X) vêm via `Settings` (novos campos em `core/config.py`), nunca hardcoded.
- Considere cache em disco (`functools.cache` + arquivo) para não estourar rate limit em desenvolvimento.

---

## 4. Quality-of-life menores

Quando der vontade:

- **Logging estruturado.** Trocar `typer.echo` para `logging` + um handler `rich` opcional. Hub error vira `logger.error("...", extra={...})`.
- **`copa-gambi doctor`.** Subcomando que faz health-check: pinga Hub, lista participantes, verifica `.env`, mostra versão do agno instalada.
- **Modo offline.** Flag `--fixture path/to/participants.json` na CLI para rodar `predict` sem Hub — útil em demo / debug.
- **Pre-commit.** Hooks `ruff check`, `ruff format`, `pytest -x` (opcional).
- **Versão dinâmica.** `__version__` via `importlib.metadata.version("copa-gambi")` em vez de hardcode, caso volte a precisar.

---

## Como atualizar este arquivo

- Ao concluir um item, **não apague** — risque com `~~...~~` e adicione data + link do PR.
- Quando aparecer ideia nova, encaixe na seção 4 antes de criar uma seção própria.
- Mantenha cada item com os 3 blocos: **objetivo**, **onde mexer**, **done when**. Sem isso vira lista de desejos.
