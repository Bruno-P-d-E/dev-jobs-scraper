# Fase 0 — Raspagem (Vagas Scraper Unificado)

Um único arquivo (`vagas_scraper_unificado.py`) substituindo `app.py`,
`app_d.py`, `aprofundar_vagas_gupy.py` e `completar_datas_e_relatorio.py`.

## Plataformas

- **Gupy** — importa por padrão os dois CSVs que você indicou como os
  melhores resultados (`gupy_vagas_dev_brasil_detalhadas_completo.csv` e
  `gupy_vagas_dev_brasil_detalhadas.csv`), sem refazer a raspagem. Se
  quiser raspar de novo ao vivo, use `--gupy-modo live` (precisa de
  Selenium + chromedriver) ou `--gupy-modo ambos`.
- **Novas (exigem raspagem de fato):** Indeed, InfoJobs, Catho,
  Empregos.com.br, LinkedIn — a combinação que você escolheu, excluindo
  Vagas.com.br do fluxograma de referência.

Tudo cai no mesmo schema, como pedido:
`platform, jobUrl, jobTitle, jobDescription, companyName, companyLocation,
companyRating, companyUrl, date`.

## Instalação

No PowerShell, a partir da raiz do repositório:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements/requirements.txt
```

Para usar `--gupy-modo live` ou `ambos`, instale também `selenium`:

```powershell
python -m pip install -r requirements/requirements-selenium.txt
```

O ambiente virtual `.venv` é local a esta pasta e está excluído do Git. O pipeline CRISP-DM (fases 2 a 5) usa apenas a biblioteca padrão do Python.

## Uso básico

```bash
# Padrão: importa os 2 CSVs da Gupy + raspa as 5 plataformas novas
python 0_raspagem/vagas_scraper_unificado.py

# Teste rápido de uma plataforma só, com log detalhado
python 0_raspagem/vagas_scraper_unificado.py --plataformas indeed --max-por-plataforma 5 --diagnostico

# Rodar a Gupy ao vivo também
python 0_raspagem/vagas_scraper_unificado.py --gupy-modo ambos

# Todas as opções
python 0_raspagem/vagas_scraper_unificado.py --help
```

Saída: um único CSV (default `dados/bruto/vagas_unificado.csv`). Os CSVs legados da Gupy são lidos de `dados/bruto/`, e os HTMLs de diagnóstico ficam em `dados/bruto/diagnostico_html/`.

## O que foi testado aqui e o que não foi

Testado neste ambiente (sem acesso de rede a sites de vagas):
- Sintaxe do arquivo inteiro (`py_compile`).
- Funções utilitárias (`normalizar`, `eh_brasil`, `classificar_vaga`).
- O extrator genérico de JSON-LD (schema.org `JobPosting`) contra HTML
  sintético — é a peça central reaproveitada por todas as plataformas.
- A leitura real dos seus dois CSVs da Gupy: 207 vagas carregadas e
  deduplicadas corretamente para o schema novo.
- O CLI de ponta a ponta em `--gupy-modo legado` (sem tocar rede).

**Não testado ao vivo** (este ambiente não tem saída de rede para
indeed.com, linkedin.com, catho.com.br, infojobs.com.br,
empregos.com.br): a descoberta de links e o parsing real de cada um
desses 5 sites. Os seletores de HTML foram escritos com base na estrutura
pública conhecida dessas páginas, mas markup de site muda — cada método
`buscar_urls` tem um comentário `# AJUSTE AQUI SE O SITE MUDAR` marcando
exatamente onde mexer se algo parar de funcionar. Recomendo rodar primeiro
com `--max-por-plataforma 3 --diagnostico` em cada plataforma antes de uma
coleta grande.

LinkedIn merece atenção especial: sem login, o acesso "guest" é limitado e
pode redirecionar para tela de login (`authwall`) a qualquer momento — o
scraper já detecta isso e pula, mas trate os resultados como bônus, não
como fonte principal de volume.

## Principais decisões tomadas

- Excluí o Vagas.com.br (conforme sua escolha) e mantive o LinkedIn.
- O CSV final é único (não gera um arquivo por plataforma), conforme
  pedido.
- Por padrão a Gupy usa os CSVs já coletados em vez de raspar de novo,
  porque você indicou que eles têm os melhores resultados — mas a opção
  de raspar ao vivo continua disponível.
- `companyRating` fica vazio por padrão (a maioria dos sites não expõe
  isso na página da vaga); com `--buscar-rating` o script tenta uma
  segunda requisição na página da empresa em busca de `aggregateRating`
  no JSON-LD — desligado por padrão para não multiplicar requisições.

## Scripts auxiliares desta fase

- `inspecionar.py`: inspeciona um HTML salvo em `dados/bruto/diagnostico_html/` (título, links, JSON-LD) para ajustar seletores.
- `limpeza.py`: reduz `dados/bruto/vagas_unificado.csv` a um conjunto fixo de colunas e grava `dados/bruto/anuncio_vagas.csv`.
