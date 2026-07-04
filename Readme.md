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
| `COPA_SKILLS_DIR`    | `skills`                 | Diretório das skills compartilhadas (Agno)  |
| `COPA_REDDIT_CLIENT_ID` | _vazio_               | OAuth Reddit (sentiment). Vazio = `RedditTools` desligado |
| `COPA_REDDIT_CLIENT_SECRET` | _vazio_           | OAuth Reddit (sentiment)                    |
| `COPA_REDDIT_USER_AGENT` | `copa-gambi/0.1 (sentiment)` | User-Agent exigido pela API Reddit |
| `COPA_FOOTBALL_DATA_TOKEN` | _vazio_             | Token football-data.org (stats). Vazio = tool desligada |
| `COPA_EXA_API_KEY`   | _vazio_                  | API key do [Exa](https://exa.ai) (busca semântica, últimos 30 dias). Vazio = `ExaTools` desligada |
| `COPA_NO_TOOLS_MODELS` | _vazio_                | Substrings de ids de modelos sem function calling (ex.: `llama3.2:1b,tinyllama`). Debatem sem tools e sem skills |
| `COPA_NO_SKILLS_MODELS` | _vazio_               | Substrings de ids de modelos que usam tools mas não dão conta do fluxo de skills. Mantêm tools, perdem skills |
| `COPA_PREFLIGHT_PROBE` | `true`                 | Testa cada participante não declarado com 1 requisição mínima antes do debate; servidor que rejeitar tools entra degradado em vez de quebrar |

> Tools opcionais (`RedditTools`, `FootballDataTools`, `ExaTools`) são ignoradas com log INFO quando a credencial estiver vazia. `DuckDuckGoTools` está sempre ativa (não exige auth).

### Modelos menos capazes

Todo participante debate, mesmo que o modelo não saiba usar tool nem skill. A capacidade de tools é resolvida por participante, nesta ordem: flags explícitas `supports_tools`/`supports_skills` nas specs (se o Hub enviar) → padrões `COPA_NO_TOOLS_MODELS`/`COPA_NO_SKILLS_MODELS` → preflight probe (1 requisição de 1 token com uma tool de teste no endpoint do participante; rejeição explícita de tools desliga, resposta inconclusiva mantém capaz) → default capaz. Skills não têm probe (seguir o fluxo é comportamental) e dependem de function calling, então modelo sem tools perde as skills junto. Agentes sem pesquisa recebem instruções para argumentar só com o próprio conhecimento, sem inventar chamadas de função — e se o moderador cair nessa categoria, ele também dispensa as `ReasoningTools`.

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
        ├── skills.py       # load_shared_skills (Agno LocalSkills loader)
        ├── tools/
        │   ├── stats.py    # FootballDataTools (football-data.org)
        │   └── registry.py # load_default_tools: DDG + Reddit + stats
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
| Skills compartilhadas (lista carregada) | [src/copa_gambi/agents/skills.py](src/copa_gambi/agents/skills.py) — `SKILL_DIRS` |
| Conteúdo de uma skill (instruções + scripts) | [skills/<nome>/SKILL.md](skills/) + `scripts/` ao lado |
| Lista default de tools dos agentes | [src/copa_gambi/agents/tools/registry.py](src/copa_gambi/agents/tools/registry.py) — `load_default_tools` |
| Tool nova / API esportiva extra | adicionar arquivo em [src/copa_gambi/agents/tools/](src/copa_gambi/agents/tools/) e plugar no `registry.py` |
| Novo subcomando CLI | [src/copa_gambi/cli/main.py](src/copa_gambi/cli/main.py) |

Mais detalhes em:
- [docs/architecture.md](docs/architecture.md) — fluxo, princípios, output esperado
- [docs/roadmap.md](docs/roadmap.md) — próximos passos planejados (testes, CI, skills como tools)
