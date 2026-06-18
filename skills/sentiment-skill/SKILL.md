---
name: sentiment-skill
description: Sentimento popular sobre o jogo via posts do X, threads do Reddit e manchetes, usado como sinal complementar (nunca único) na previsão do placar.
---

# sentiment-skill

Sentimento popular sobre o jogo: posts do X, threads do Reddit, manchetes.

## Quando usar
- Como sinal complementar, nunca como única evidência.
- Quando há contexto de público (mando, torcida, polêmica recente).

## Scripts
- `scripts/fetch_sentiment.py` — coleta uma amostra de posts/manchetes e
  devolve um score de sentimento agregado por seleção.
