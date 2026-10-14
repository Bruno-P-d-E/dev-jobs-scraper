# Etapa 13 — n-gramas, léxico de domínio e regex

N-gramas são contados separadamente em títulos e descrições para n=1, 2 e 3. Foram analisadas 1371 vagas.

## Dez combinações mais frequentes por tamanho

Unigramas comuns de função (stopwords) foram omitidos apenas deste resumo; o CSV completo mantém todas as contagens.

| Campo | n | N-grama | Ocorrências | Documentos |
|---|---:|---|---:|---:|
| descricao | 1 | experiencia | 4978 | 1203 |
| descricao | 1 | desenvolvimento | 3810 | 1153 |
| descricao | 1 | conhecimento | 2901 | 1038 |
| descricao | 1 | voce | 2464 | 734 |
| descricao | 1 | solucoes | 2168 | 896 |
| descricao | 1 | sistemas | 2094 | 875 |
| descricao | 1 | desenvolvedor | 1823 | 597 |
| descricao | 1 | dados | 1784 | 852 |
| descricao | 1 | aplicacoes | 1668 | 774 |
| descricao | 1 | software | 1641 | 656 |
| descricao | 2 | experiencia com | 2489 | 874 |
| descricao | 2 | conhecimento em | 1705 | 756 |
| descricao | 2 | de dados | 1503 | 810 |
| descricao | 2 | desenvolvimento de | 1282 | 758 |
| descricao | 2 | de software | 1191 | 591 |
| descricao | 2 | de desenvolvimento | 1107 | 645 |
| descricao | 2 | praticas de | 859 | 563 |
| descricao | 2 | de trabalho | 825 | 609 |
| descricao | 2 | boas praticas | 780 | 541 |
| descricao | 2 | de codigo | 711 | 521 |
| descricao | 3 | boas praticas de | 602 | 441 |
| descricao | 3 | bancos de dados | 527 | 409 |
| descricao | 3 | tipo de contrato | 438 | 437 |
| descricao | 3 | limpar texto limpar | 400 | 100 |
| descricao | 3 | texto limpar texto | 400 | 100 |
| descricao | 3 | seguro de vida | 380 | 375 |
| descricao | 3 | banco de dados | 362 | 278 |
| descricao | 3 | horario de trabalho | 340 | 335 |
| descricao | 3 | praticas de desenvolvimento | 325 | 280 |
| descricao | 3 | desenvolver e manter | 323 | 287 |

O léxico-semente identificou 11874 combinações vaga-termo em 80 termos/categorias; as regex registraram 1986 ocorrências. Saídas: `frequencia_ngramas.csv`, `ocorrencias_lexico_dominio.csv`, `resumo_lexico_dominio.csv` e `extracoes_regex.csv`.

O léxico é inicial, configurável no script e requer revisão/validação manual antes de inferir competências. As regex indicam apenas correspondências textuais e não garantem que o requisito foi corretamente interpretado.
