# Etapa 5 — tokenização

Uma linha por vaga. O conteúdo é a junção dos campos textuais configurados em `config.py`, gravada em uma única coluna (`tokens`). URLs/e-mails e números isolados foram removidos; stopwords são mantidas nesta etapa e removidas na etapa 6; tokens ficam em minúsculas, com acentos preservados. Expressões técnicas como C++, C#, .NET e CI/CD são preservadas. Não foi aplicado stemming ou lematização.

- Documentos tokenizados: **1371**
- Total de tokens: **493440**
- Vocabulário (tokens únicos): **15452**
- Média de tokens por vaga: **359.91**
- Vagas sem tokens: **0**
- CSV tokenizado: `vagas_tokenizadas.csv`
