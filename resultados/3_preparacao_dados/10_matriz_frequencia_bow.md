# Etapa 10 — matriz de frequência e Bag of Words

A representação Bag of Words conta ocorrências de cada termo lematizado em cada vaga. Cada linha da matriz corresponde a um documento (`documento_id`, na ordem do CSV da etapa 7); cada coluna seguinte corresponde a um termo do vocabulário. Os valores são contagens inteiras brutas, sem ponderação TF-IDF e sem considerar a ordem das palavras.

- Documentos: **1371**
- Vocabulário: **11876** termos distintos
- Ocorrências totais: **335897**
- Soma de frequências documento-termo: **233947**
- Matriz CSV: `matriz_frequencia_bow.csv`
- Frequências agregadas: `frequencia_termos_bow.csv`

## 20 termos mais frequentes

| Termo | Ocorrências | Documentos com o termo |
|---|---:|---:|
| experiência | 4966 | 1197 |
| desenvolvimento | 3859 | 1162 |
| conhecimento | 3399 | 1118 |
| desenvolvedor | 3036 | 1038 |
| sistema | 2437 | 944 |
| solução | 2335 | 931 |
| técnico | 2201 | 915 |
| software | 1959 | 718 |
| aplicação | 1873 | 807 |
| tecnologia | 1778 | 811 |
| brasil | 1743 | 784 |
| desenvolver | 1741 | 940 |
| integração | 1730 | 797 |
| bom | 1717 | 868 |
| dar | 1621 | 818 |
| apis | 1546 | 817 |
| time | 1448 | 672 |
| teste | 1354 | 772 |
| código | 1340 | 769 |
| atuar | 1323 | 753 |
