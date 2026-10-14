# Etapa 7 — lematização

Os tokens da etapa 6 foram processados com o modelo `pt_core_news_sm` do spaCy. Cada vaga continua em uma linha e a saída possui somente a coluna `tokens`. A lematização usa o contexto linguístico do modelo. Um vocabulário técnico configurado, nomes próprios e substantivos singulares são preservados para reduzir alterações ambíguas em termos de TI.

- Vagas antes/depois: **1371 / 1371**
- Tokens antes: **335888**
- Tokens depois: **335897**
- Tokens com lema diferente da forma original: **110179**
- Termos técnicos ou formas ambíguas preservadas: **25882**
- Vocabulário antes/depois: **13664 / 11876**
- Vagas sem tokens após lematização: **0**
- CSV resultante: `vagas_lematizadas.csv`
