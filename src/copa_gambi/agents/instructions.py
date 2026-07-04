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
]

AGENT_ROLE = "Analista independente de futebol"
TEAM_NAME = "World Cup Debate Team"
