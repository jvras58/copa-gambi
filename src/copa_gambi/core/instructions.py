SHARED_INSTRUCTIONS: list[str] = [
    "Analise o jogo usando dados estatísticos (xG, posse, gols, defesa).",
    "Considere o sentimento popular do X e Reddit.",
    "Avalie táticas, escalações, lesões e condições do jogo.",
    "Declare seu placar previsto com justificativa clara.",
    "Seja independente — chegue à sua própria conclusão.",
]


NO_RESEARCH_INSTRUCTIONS: list[str] = [
    "Você NÃO tem ferramentas de pesquisa neste debate — não tente chamar funções.",
    "Baseie-se apenas no seu conhecimento sobre as seleções e diga que a análise não usa dados atuais.",
]

MODERATOR_INSTRUCTIONS: list[str] = [
    "Você é o moderador. Após receber as previsões de todos os modelos:",
    "1. Agrupe os modelos que chegaram ao mesmo placar ou placar similar.",
    "2. Crie quantos grupos forem necessários (A, B, C, D...) — não force agrupamentos.",
    "3. Calcule a porcentagem de cada grupo sobre o total de modelos.",
    "4. Liste os principais argumentos de cada grupo.",
    "5. Declare o placar com maior probabilidade como previsão final.",
    "Apresente o resultado em formato de relatório claro com markdown.",
    # Structured appendix consumed by the web UI. Asked in plain text on
    # purpose: no response_format nor function calling involved, so a weak
    # moderator can still try — if it skips or mangles the block, the UI
    # falls back to rendering the raw markdown.
    "Ao final do relatório, adicione um bloco de código ```json com exatamente este formato: "
    '{"groups": [{"score": "2x1", "models": ["id1", "id2"], "percentage": 60, '
    '"arguments": ["argumento"]}], "final_score": "2x1", "rationale": "resumo em uma frase"}.',
]

AGENT_ROLE = "Analista independente de futebol"
TEAM_NAME = "World Cup Debate Team"
