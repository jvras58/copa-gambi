# stats-skill

Estatísticas avançadas do jogo: xG, posse de bola, gols, defesa, confrontos diretos.

## Quando usar
- O analista precisa de números concretos (não opinião) para sustentar a previsão.
- Antes de declarar o placar final.

## Scripts
- `scripts/fetch_stats.py` — consulta uma API esportiva (ex.: football-data.org)
  e devolve um JSON com xG, gols marcados/sofridos por jogo, posse média e
  histórico de confrontos.
