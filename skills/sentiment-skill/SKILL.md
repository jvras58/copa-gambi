---
name: sentiment-skill
description: Sentimento popular sobre o jogo via notícias (DuckDuckGo News) e Reddit, com ranqueamento por engajamento, janela temporal e dedupe — sinal complementar (nunca único) na previsão do placar.
---

# sentiment-skill

Sentimento popular sobre o confronto, agregado de fontes gratuitas com ranqueamento por engajamento.

## Quando usar
- Como sinal complementar, nunca como única evidência.
- Quando há contexto de público (mando, torcida, polêmica recente, lesão de destaque).

## Como usar

```bash
python scripts/fetch_sentiment.py "Brasil x Argentina" --days 14
```

O script:
1. **Expande queries** — busca o confronto e cada seleção com apelidos comuns ("Seleção Brasileira", "Albiceleste"...).
2. **Aplica janela temporal** — só considera itens publicados dentro de `--days` (default 14).
3. **Ranqueia por engajamento** — no Reddit, upvotes e comentários pesam; tudo decai com a idade do item.
4. **Deduplica entre fontes** — a mesma história vinda de notícia e Reddit vira um item só, com engajamento somado.

Fontes: DuckDuckGo News (sempre ativa) e Reddit (só quando `COPA_REDDIT_CLIENT_ID`/`COPA_REDDIT_CLIENT_SECRET` estão no ambiente).

> O script é um wrapper fino sobre `copa_gambi.tools.sentiment` — a mesma lógica
> também está disponível como tool direta (`matchup_sentiment`). Prefira a tool
> quando ela estiver listada; use o script quando quiser controlar `--days` e
> `--max-per-query` manualmente.

## Como interpretar a saída
- `by_team.<time>.weighted_score`: -1.0 (clima negativo) a 1.0 (clima positivo). É uma **heurística por léxico** — trate como "tendência da torcida/mídia", não como fato.
- `by_team.geral`: itens sobre o confronto em si (não sobre uma seleção específica).
- `top_items`: as histórias com maior peso (engajamento × frescor) — cite-as ao justificar o sinal de sentimento.
- Poucos itens (`count` baixo) = sinal fraco; diga isso explicitamente na sua análise.
