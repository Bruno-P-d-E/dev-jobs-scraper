# Etapa 11 — TF-IDF

A matriz usa TF como contagem bruta do termo no documento e IDF suavizado `log((1 + N) / (1 + df)) + 1`, em que `N` é o número de vagas e `df` é o número de vagas que contêm o termo. O peso é `TF × IDF`; termos presentes em quase todas as vagas recebem menor peso relativo. O arquivo é esparso: registra apenas pares documento-termo observados. Os pesos não foram normalizados por comprimento do documento.

- Documentos: **1371**
- Vocabulário: **11876** termos
- Células não nulas gravadas: **233947**
- Arquivo: `matriz_tfidf_esparsa.csv`
