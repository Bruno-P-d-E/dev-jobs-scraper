# Etapa 6 — normalização e remoção de stopwords

Ordem aplicada: converter tokens para minúsculas; remover pontuação, símbolos e demais caracteres não alfanuméricos, usando espaço como separador para não juntar palavras; remover stopwords em português e inglês. Letras acentuadas e números dentro de tokens são preservados. A entrada e a saída mantêm uma coluna (`tokens`) e uma linha por vaga.

- Vagas antes/depois: **1371 / 1371**
- Vagas com caixa ou caracteres especiais normalizados: **1303**
- Tokens em minúsculas: **0**
- Caracteres especiais removidos: **10772**
- Tokens de entrada: **493440**
- Tokens após normalização e antes de stopwords: **502918**
- Vagas com stopwords removidas: **1371**
- Stopwords removidas: **167030**
- Tokens finais: **335888**
- Vagas sem tokens finais: **0**
- Vocabulário antes/depois: **15452 / 13664**
- CSV resultante: `vagas_sem_stopwords.csv`

## 20 stopwords mais removidas

| Stopword | Ocorrências |
|---|---:|
| de | 35543 |
| e | 28930 |
| em | 11409 |
| com | 10824 |
| a | 9282 |
| para | 7978 |
| o | 4886 |
| ou | 3899 |
| que | 3751 |
| do | 3591 |
| da | 3363 |
| se | 2535 |
| na | 2491 |
| você | 2468 |
| no | 2463 |
| um | 2348 |
| como | 1768 |
| uma | 1707 |
| é | 1671 |
| das | 1608 |
