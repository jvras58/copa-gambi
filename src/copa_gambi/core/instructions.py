SHARED_INSTRUCTIONS: list[str] = [
    "Analise o jogo usando dados estatísticos (xG, posse, gols, defesa).",
    "Considere o sentimento popular do X e Reddit.",
    "Avalie táticas, escalações, lesões e condições do jogo.",
    "Declare seu placar previsto com justificativa clara.",
    "Seja independente — chegue à sua própria conclusão.",
    'Termine a análise com uma linha exatamente neste formato: "Placar previsto: 2 x 1".',
]


NO_RESEARCH_INSTRUCTIONS: list[str] = [
    "Você NÃO tem ferramentas de pesquisa neste debate — não tente chamar funções.",
    "Baseie-se apenas no seu conhecimento sobre as seleções e diga que a análise não usa dados atuais.",
]

# One-shot example: local models follow a concrete sample far more reliably
# than an abstract format description. The JSON appendix is asked in plain
# text on purpose — no response_format nor function calling involved, so a
# weak moderator can still try; if it skips or mangles the block, the UI
# falls back to rendering the raw markdown.
_MODERATOR_EXAMPLE = """\
## Relatório do debate

**Previsão final: 2x1 Brasil**

### Grupo A — 2x1 (67%)
- Modelos: alice::mistral:7b, bob::qwen2.5:32b
- Argumentos: forma recente superior; desfalque na zaga adversária

### Grupo B — 1x1 (33%)
- Modelos: carol::llama3.2:3b
- Argumentos: equilíbrio no retrospecto recente

```json
{"groups": [\
{"score": "2x1", "models": ["alice::mistral:7b", "bob::qwen2.5:32b"], "percentage": 67, \
"arguments": ["forma recente superior", "desfalque na zaga adversária"]}, \
{"score": "1x1", "models": ["carol::llama3.2:3b"], "percentage": 33, \
"arguments": ["equilíbrio no retrospecto recente"]}], \
"final_score": "2x1", "rationale": "maioria apostou na forma recente"}
```"""

MODERATOR_INSTRUCTIONS: list[str] = [
    "Você é o moderador. Após receber as previsões de todos os modelos:",
    "1. Agrupe os modelos que chegaram ao mesmo placar ou placar similar.",
    "2. Crie quantos grupos forem necessários (A, B, C, D...) — não force agrupamentos.",
    "3. Calcule a porcentagem de cada grupo sobre o total de modelos.",
    "4. Liste os principais argumentos de cada grupo.",
    "5. Declare o placar com maior probabilidade como previsão final.",
    "Apresente o resultado em markdown e termine com um bloco de código ```json "
    "no mesmo formato do exemplo — sem texto depois do bloco.",
    f"Exemplo de resposta (siga exatamente esta estrutura):\n{_MODERATOR_EXAMPLE}",
]

AGENT_ROLE = "Analista independente de futebol"
TEAM_NAME = "World Cup Debate Team"
