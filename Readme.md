
# ⚽ World Cup Score Predictor — Distributed Multi-Model Debate

Sistema distribuído onde múltiplas pessoas conectam seus modelos locais via **Gambi Hub**,
cada um analisa o mesmo jogo de forma independente com as mesmas skills, e o modelo
com mais poder de processamento (eleito automaticamente pelos specs do Gambi) atua como
**moderador** — agrupando os resultados dinamicamente e calculando a probabilidade de cada previsão.

---

## Arquitetura

```mermaid
flowchart TD
    A["Input: Jogo da Copa<br/>ex: Brasil x Argentina"] --> B0

    subgraph BM["BROADCAST MODE"]
        direction TB

        B0["Participantes descobertos dinamicamente via Gambi Hub<br/>Todos recebem o mesmo input e as mesmas skills<br/>Cada modelo decide livremente"]

        B1["joao-1::llama3.3:70b<br/>previsão independente"]
        B2["maria-1::mistral<br/>previsão independente"]
        B3["pedro-1::deepseek-r1<br/>previsão independente"]
        B4["joao-2::llama3.3:70b<br/>previsão independente"]
        B5["ana-1::qwen2.5:72b<br/>previsão independente"]

        B0 --> B1
        B0 --> B2
        B0 --> B3
        B0 --> B4
        B0 --> B5
    end

    B1 --> C1
    B2 --> C1
    B3 --> C1
    B4 --> C1
    B5 --> C1

    subgraph MODR["⭐ MODERADOR — maior gpu_vram_gb (ReasoningTools)"]
        direction TB

        C1["1. Lê todas as previsões"]
        C2["2. Agrupa as similares dinamicamente<br/>(A, B, C, D...)"]
        C3["3. Calcula a probabilidade de cada grupo"]
        C4["4. Declara o placar com maior probabilidade"]

        C1 --> C2 --> C3 --> C4
    end

    C4 --> D["Output: Relatório Final"]
```

---

## Output Esperado

O moderador cria os grupos dinamicamente — podem ser 2, 3 ou mais:

```
📊 PREVISÃO: Brasil x Argentina — Copa do Mundo 2026

GRUPO A — 60% de probabilidade
  Placar: Brasil 2 x 1 Argentina
  Modelos: joao-1::llama3.3:70b, maria-1::mistral, pedro-1::deepseek-r1
  Argumentos:
    - Brasil com melhor xG nos últimos 5 jogos
    - Sentimento popular 72% favorável ao Brasil no X
    - Argentina sem Messi em forma plena

GRUPO B — 20% de probabilidade
  Placar: Empate 1 x 1
  Modelos: joao-2::llama3.3:70b
  Argumentos:
    - Histórico de empates em fases de grupos
    - Defesa argentina sólida nos últimos 3 jogos

GRUPO C — 20% de probabilidade
  Placar: Argentina 1 x 0 Brasil
  Modelos: ana-1::qwen2.5:72b
  Argumentos:
    - Argentina venceu os últimos 2 confrontos diretos

🎯 Previsão Final: Brasil 2 x 1 Argentina (60% de confiança)
```

---

## Setup com Gambi

### 1. Subir o Hub
Escolha uma máquina na rede (não precisa de GPU):

```bash
# Interativo:
gambi hub serve

# Ou com flags:
gambi hub serve --port 3000 --mdns
```

### 2. Criar a Room

```bash
gambi room create --name "worldcup-debate"
# Output: Room created! Code: ABC123
```

### 3. Cada participante conecta seu modelo

```bash
# Ollama (padrão — localhost:11434)
gambi participant join \
  --room ABC123 \
  --participant-id joao-1 \
  --model llama3.3:70b

# Outro João com o mesmo modelo — participant-id diferente garante unicidade
gambi participant join \
  --room ABC123 \
  --participant-id joao-2 \
  --model llama3.3:70b

# LM Studio
gambi participant join \
  --room ABC123 \
  --participant-id maria-1 \
  --model mistral \
  --endpoint http://localhost:1234

# vLLM
gambi participant join \
  --room ABC123 \
  --participant-id pedro-1 \
  --model deepseek-r1 \
  --endpoint http://localhost:8000
```

> ⭐ O moderador é eleito **automaticamente** pelo Agno — o participante com maior `gpu_vram_gb`
> nos specs que o Gambi compartilha ao conectar. Não é necessário designar manualmente.

---

## Skills dos Agentes

Todos os agentes recebem as **mesmas skills** — a diferença está apenas no modelo local de cada participante.

```
skills/
├── stats-skill/
│   ├── SKILL.md              # xG, posse, gols, defesa, confrontos diretos
│   └── scripts/
│       └── fetch_stats.py    # APIs esportivas (ex: football-data.org)
│
├── tactical-skill/
│   ├── SKILL.md              # Formações, escalações, lesões, clima
│   └── references/
│       └── formations.md
│
└── sentiment-skill/
    ├── SKILL.md              # Opinião popular do X, Reddit, sites
    └── scripts/
        └── fetch_sentiment.py
```

---

## Código Base

```python
import httpx
from agno.agent import Agent
from agno.team import Team
from agno.team.mode import TeamMode
from agno.tools.reasoning import ReasoningTools
from agno.models.openai.like import OpenAILike

HUB_URL = "http://hub-ip:3000"
ROOM_CODE = "ABC123"

SHARED_INSTRUCTIONS = [
    "Analise o jogo usando dados estatísticos (xG, posse, gols, defesa).",
    "Considere o sentimento popular do X e Reddit.",
    "Avalie táticas, escalações, lesões e condições do jogo.",
    "Declare seu placar previsto com justificativa clara.",
    "Seja independente — chegue à sua própria conclusão.",
]

def fetch_participants():
    """Busca participantes ativos do room via Gambi Hub"""
    response = httpx.get(f"{HUB_URL}/rooms/{ROOM_CODE}/participants")
    response.raise_for_status()
    return response.json()

def make_agent(participant):
    unique_id = f"{participant['participant_id']}::{participant['model']}"
    return Agent(
        name=unique_id,  # ex: "joao-1::llama3.3:70b" — único mesmo com dois Joãos
        model=OpenAILike(
            id=participant["model"],
            base_url=f"{HUB_URL}/v1",
            api_key="gambi",
        ),
        role="Analista independente de futebol",
        instructions=SHARED_INSTRUCTIONS,
    )

# Descobre participantes dinamicamente
participants = fetch_participants()

# Elege moderador automaticamente pelo maior poder de GPU
moderator_participant = max(participants, key=lambda p: p["specs"]["gpu_vram_gb"])

# Demais participantes viram agentes do debate
agents = [
    make_agent(p)
    for p in participants
    if p["participant_id"] != moderator_participant["participant_id"]
]

moderator = Team(
    name="World Cup Debate Team",
    mode=TeamMode.broadcast,
    model=OpenAILike(
        id=moderator_participant["model"],
        base_url=f"{HUB_URL}/v1",
        api_key="gambi",
    ),
    members=agents,
    tools=[ReasoningTools(add_instructions=True)],
    instructions=[
        "Você é o moderador. Após receber as previsões de todos os modelos:",
        "1. Agrupe os modelos que chegaram ao mesmo placar ou placar similar.",
        "2. Crie quantos grupos forem necessários (A, B, C, D...) — não force agrupamentos.",
        "3. Calcule a porcentagem de cada grupo sobre o total de modelos.",
        "4. Liste os principais argumentos de cada grupo.",
        "5. Declare o placar com maior probabilidade como previsão final.",
        "Apresente o resultado em formato de relatório claro com markdown.",
    ],
    show_members_responses=True,
    markdown=True,
)

if __name__ == "__main__":
    moderator.print_response(
        "Jogo: Brasil x Argentina — Copa do Mundo 2026, Fase de Grupos",
        stream=True,
        show_full_reasoning=True,
    )
```

---

## Stack & Referências

| Componente | Descrição | Link |
|---|---|---|
| Gambi Hub | Conecta modelos locais distribuídos em rede | [gambi.sh/reference/cli](https://www.gambi.sh/reference/cli/) |
| OpenAILike | Aponta qualquer endpoint OpenAI-compatible | [docs.agno.com/models/providers/openai-like](https://docs.agno.com/models/providers/openai-like) |
| Broadcast Mode | Todos os agentes recebem o mesmo input em paralelo | [docs.agno.com/examples/teams/modes/broadcast/debate](https://docs.agno.com/examples/teams/modes/broadcast/debate) |
| ReasoningTools | Raciocínio estruturado no moderador | [docs.agno.com/reasoning/usage/tools/reasoning-tool-team](https://docs.agno.com/reasoning/usage/tools/reasoning-tool-team) |
| Teams Overview | Como times funcionam no Agno | [docs.agno.com/teams/overview](https://docs.agno.com/teams/overview) |

---

As duas mudanças principais refletidas:
- **ID único**: `participant_id::model` garante distinção mesmo entre dois Joãos com o mesmo modelo
- **Descoberta dinâmica**: `fetch_participants()` busca quem está no room em tempo real — ninguém precisa editar código para entrar no debate
