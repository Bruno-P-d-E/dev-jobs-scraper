# Dev Jobs Scraper — raspagem e análise de vagas (CRISP-DM)

Repositório organizado conforme o CRISP-DM. O fluxo começa pela **raspagem** (`0_raspagem`) e segue pelas fases na ordem do CRISP-DM; dentro de cada fase, os scripts mantêm a numeração original (`01_…` a `16_…`).

## Estrutura

| Pasta | Fase CRISP-DM | Scripts |
| --- | --- | --- |
| `0_raspagem/` | Coleta dos dados (início do fluxo) | `vagas_scraper_unificado.py`, `inspecionar.py`, `limpeza.py` |
| `1_entendimento_negocio/` | Entendimento do negócio | documentação (pergunta de pesquisa ainda em aberto) |
| `2_entendimento_dados/` | Entendimento dos dados | `01_entendimento_dados.py`, `02_exploracao.py` |
| `3_preparacao_dados/` | Preparação dos dados | `03_higienizacao.py`, `04_preparacao.py`, `05_tokenizacao.py`, `06_remocao_stopwords.py`, `07_lematizacao.py`, `10_matriz_frequencia_bow.py`, `11_tfidf.py`, `12_embeddings_sbert.py` (opcional) |
| `4_modelagem/` | Modelagem | `08_modelagem.py`, `13_ngramas_lexico_regex.py`, `14_modelagem_topicos_clusters.py` (opcional), `16_classificar_modalidade.py` |
| `5_avaliacao/` | Avaliação | `09_avaliacao.py`, `15_avaliacao_validacao.py` |
| `6_implantacao/` | Implantação / comunicação dos resultados | `gerar_graficos.py`, `gerar_nuvem_palavras.py` |

Apoio:

- `comum/` — `config.py` (todos os caminhos) e `io_utils.py`, compartilhados pelas fases 2 a 6.
- `dados/bruto/` (criada pela raspagem ou por você) — saída da raspagem (`vagas_unificado.csv`) e CSVs legados da Gupy. Somente leitura para o pipeline.
- `resultados/<fase>/` — relatórios `.md` e CSVs gerados por cada fase. `resultados/_legado/` guarda relatórios de uma numeração antiga que nenhum script atual gera.
- `figuras/` (criada pela fase 6) — gráficos gerados.
- `requirements/` — dependências por uso (scraper, Selenium, NLP, embeddings, modelagem, lock).
- `docs/metodologia_pipeline.md` — documentação metodológica detalhada do pipeline.
- `executar_pipeline.py` — roda as fases 2 a 5 em ordem.

## Como executar

Na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/requirements.txt

# Fase 0 — raspagem (gera dados/bruto/vagas_unificado.csv)
python 0_raspagem/vagas_scraper_unificado.py

# Fases 2 a 5 — pipeline (a lematização exige requirements/requirements-nlp.txt)
python -m pip install -r requirements/requirements-nlp.txt
python executar_pipeline.py                 # opcionais: --embeddings  --modelagem

# Fase 6 — figuras
python 6_implantacao/gerar_graficos.py
```

Qualquer script também roda isolado, por exemplo `python 3_preparacao_dados/03_higienizacao.py`.

Dependências opcionais: `requirements/requirements-selenium.txt` (Gupy ao vivo), `requirements-embeddings.txt` (etapa 12), `requirements-modelagem.txt` (etapa 14); `gerar_nuvem_palavras.py` usa `matplotlib` e `wordcloud`.

## Ordem de execução

`executar_pipeline.py` segue as fases; por isso as etapas 10, 11 (e 12) rodam na preparação, antes do roteiro `08_modelagem.py` e das etapas 13, 14 e 16 da modelagem. A etapa 15 roda por último, pois lê as saídas de 13, 14 e 16.

## Licença, autoria e citação

- **Licença:** Apache-2.0 (`LICENSE`). Ela permite uso e adaptação, mas **exige** manter o aviso de copyright e o arquivo `NOTICE` em qualquer redistribuição ou obra derivada, e indicar as alterações feitas.
- **Citação obrigatória:** trabalhos acadêmicos, artigos, relatórios ou produtos que usem este código, a metodologia ou os resultados devem citar a obra conforme `CITATION.cff` (o GitHub gera o formato "Cite this repository" a partir dele).
- **Autoria comprovável:** `PROVENANCE.md` traz o hash SHA-256 de cada arquivo. O histórico de commits e uma versão publicada (release/DOI) completam a prova de anterioridade.
- **Dados:** os anúncios raspados pertencem às plataformas e empresas que os publicaram. A licença deste repositório cobre o código e a documentação, não esses textos. Por isso `dados/bruto/*.csv` está no `.gitignore` e não deve ser publicado.
