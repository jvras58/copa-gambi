# ⚽ copa-gambi

CLI para um debate multi-modelo de previsão de jogos da Copa, com participantes
descobertos dinamicamente via [Gambi Hub](https://www.gambi.sh/reference/cli/) e
moderador eleito automaticamente pelo maior `gpu_vram_gb`.

> Como o sistema funciona por dentro está em [docs/architecture.md](docs/architecture.md).

---

## Pré-requisitos

- Python **3.12+**
- [uv](https://docs.astral.sh/uv/) (gerenciador de pacote/venv)
- [Gambi CLI](https://www.gambi.sh/reference/cli/) — para subir o Hub e conectar participantes

---

## Instalação

```bash
git clone <repo>
cd copa-gambi
uv sync
cp .env.example .env   # edite com seu HUB_URL e ROOM_CODE
```

`uv sync` cria `.venv/`, instala dependências e o pacote em modo editável.

---

## Configuração

Variáveis lidas via `pydantic-settings` (prefixo `COPA_`, arquivo `.env`):

| Variável             | Default                  | Descrição                                   |
|---|---|---|
| `COPA_HUB_URL`       | `http://localhost:3000`  | Base URL do Gambi Hub                       |
| `COPA_ROOM_CODE`     | `ABC123`                 | Código da room criado em `gambi room create`|
| `COPA_API_KEY`       | `gambi`                  | API key enviada ao endpoint OpenAI-compat   |
| `COPA_REQUEST_TIMEOUT` | `30`                   | Timeout HTTP (segundos)                     |

---

## Subindo a infra (Gambi)

```bash
# 1) Hub (qualquer máquina da rede, não precisa de GPU)
gambi hub serve --port 3000 --mdns

# 2) Criar a room
gambi room create --name "worldcup-debate"
# -> Room created! Code: ABC123

# 3) Cada participante conecta seu modelo local
gambi participant join --room ABC123 --participant-id joao-1 --model llama3.3:70b
gambi participant join --room ABC123 --participant-id maria-1 --model mistral --endpoint http://localhost:1234
gambi participant join --room ABC123 --participant-id pedro-1 --model deepseek-r1 --endpoint http://localhost:8000
```

---

## Uso

```bash
# Lista quem está na room e marca o moderador eleito
uv run copa-gambi participants

# Roda o debate em broadcast e imprime o relatório do moderador
uv run copa-gambi predict "Brasil x Argentina — Copa do Mundo 2026, Fase de Grupos"

# Sem streaming, sem reasoning detalhado
uv run copa-gambi predict "Brasil x Argentina" --no-stream --no-reasoning
```

Também dá pra rodar como módulo: `uv run python -m copa_gambi predict "..."`.

---

## Estrutura do projeto

```
copa-gambi/
├── pyproject.toml          # uv + hatchling + ruff
├── .env.example
├── docs/
│   └── architecture.md     # fluxo, princípios, output esperado
├── skills/                 # SKILL.md + scripts compartilhados pelos agentes
│   ├── stats-skill/
│   ├── tactical-skill/
│   └── sentiment-skill/
└── src/copa_gambi/         # namespace package (PEP 420, sem __init__.py)
    ├── __main__.py         # python -m copa_gambi
    ├── cli/
    │   └── main.py         # Typer: participants, predict
    ├── core/
    │   ├── config.py       # pydantic-settings (Settings)
    │   ├── schemas.py      # Participant, ParticipantSpecs (Pydantic)
    │   └── hub.py          # fetch_participants, elect_moderator
    └── agents/
        ├── instructions.py # SHARED_INSTRUCTIONS, MODERATOR_INSTRUCTIONS
        ├── factory.py      # make_agent, build_model
        └── team.py         # build_team, build_team_from_hub
```

---

## Dev

```bash
uv sync                 # instala + atualiza lockfile
uv run ruff check src   # lint
uv run ruff format src  # format
```

Para adicionar uma dependência: `uv add <pkg>` (ou `uv add --dev <pkg>` para grupo de dev).

---

## Como estender

| O que mudar | Onde mexer |
|---|---|
| Texto das instruções dos agentes ou do moderador | [src/copa_gambi/agents/instructions.py](src/copa_gambi/agents/instructions.py) |
| Regra de eleição do moderador (hoje: maior VRAM) | [src/copa_gambi/core/hub.py](src/copa_gambi/core/hub.py) — `elect_moderator` |
| Campos extras esperados do Gambi (CPU, RAM, etc.) | [src/copa_gambi/core/schemas.py](src/copa_gambi/core/schemas.py) |
| Tools/skills dos agentes (xG, sentimento etc.) | [src/copa_gambi/agents/factory.py](src/copa_gambi/agents/factory.py) + arquivos em `skills/` |
| Novo subcomando CLI | [src/copa_gambi/cli/main.py](src/copa_gambi/cli/main.py) |

Mais detalhes em:
- [docs/architecture.md](docs/architecture.md) — fluxo, princípios, output esperado
- [docs/roadmap.md](docs/roadmap.md) — próximos passos planejados (testes, CI, skills como tools)
