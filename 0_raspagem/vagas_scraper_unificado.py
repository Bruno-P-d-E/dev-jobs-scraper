# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 [NOME DO AUTOR]. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
 VAGAS SCRAPER UNIFICADO — Gupy + InfoJobs + Catho + Empregos + LinkedIn
================================================================================

Um único script que substitui os arquivos soltos e divergentes do projeto
original (app.py, app_d.py, aprofundar_vagas_gupy.py,
completar_datas_e_relatorio.py) por um pipeline único, consistente e
extensível.

O QUE MUDOU EM RELAÇÃO AO PROJETO ANTERIOR
--------------------------------------------------------------------------
1. Antes cada etapa (descoberta de URLs, aprofundamento de descrição,
   completar datas, relatório) era um script Python separado, cada um com
   sua própria cópia de funções utilitárias (normalizar texto, extrair
   JSON-LD, detectar Brasil, detectar bloqueio anti-bot etc.), com
   pequenas divergências entre elas. Aqui existe UMA implementação de cada
   utilitário, reaproveitada por todas as plataformas.

2. O projeto cobria só a Gupy. Este script adiciona mais 4 plataformas que
   exigem raspagem de dados de fato (não têm uma API pública documentada
   como algumas ATS): InfoJobs, Catho, Empregos.com.br e LinkedIn.
   (Ficou de fora o Vagas.com.br, por decisão do usuário, já que no
   levantamento de referência ele não retornou resultados aproveitáveis.
   O Indeed também foi removido do pipeline: sua proteção anti-bot exigia
   um Chrome via Selenium dedicado só para ele, e o custo/fragilidade não
   compensava frente às demais plataformas.)

3. Todas as plataformas exportam para o MESMO schema (schema unificado),
   pedido explicitamente:

       platform, jobUrl, jobTitle, jobDescription, companyName,
       companyLocation, companyRating, companyUrl, date

4. A Gupy agora roda SEMPRE ao vivo (Selenium), do zero, a cada execução.
   O modo "legado" (importar CSVs antigos já coletados) continua existindo
   no código por compatibilidade, mas deixou de ser o padrão — para usá-lo
   é preciso pedir explicitamente com --gupy-modo legado ou --gupy-modo
   ambos.

5. [REVISÃO] A lógica de extração da Gupy foi conferida linha a linha
   contra os 4 scripts originais (app.py, app_d.py, aprofundar_vagas_gupy.py
   e completar_datas_e_relatorio.py) e os seguintes desvios foram
   corrigidos:

   a) `companyRating`/`companyUrl` faziam parte do schema unificado pedido
      (ver item 3 acima) mas não existiam no dataclass `VagaUnificada` nem
      em `COLUNAS_UNIFICADAS`. Isso fazia `carregar_gupy_legado` (usada
      por --gupy-modo legado/ambos) quebrar sempre com TypeError, e fazia
      `BaseScraper.rodar` referenciar atributos inexistentes quando
      --buscar-rating era usado. Os dois campos foram adicionados de volta
      ao schema, e a extração de `companyUrl`/`companyRating` a partir do
      JobPosting (JSON-LD) foi implementada de fato (antes era descartada
      de propósito em `_extrair_via_jsonld` e nunca preenchida na Gupy).

   b) `PALAVRAS_CHAVE_BUSCA` (a lista usada para pesquisar vagas no portal
      da Gupy, uma query por palavra) estava truncada para 11 termos
      genéricos. O app.py original (código 1) usa uma lista de 55 termos
      de busca — bem mais ampla — para cobrir variações de senioridade,
      stack e nomenclatura (ex.: "backend developer", "desenvolvedor
      android", "site reliability engineer" etc.). A lista completa foi
      restaurada, pois é parte central da lógica de descoberta de vagas da
      Gupy: usar só 11 termos reduzia bastante a cobertura da coleta em
      relação ao script original.

   c) A geração do "Relatório de Qualidade dos Dados" (completar_datas_e_
      relatorio.py, código 3) não tinha sido portada — só a parte de
      completar datas ausentes por texto foi migrada (já embutida na
      camada de aprofundamento da Gupy). A função `gerar_relatorio_
      qualidade` foi portada e adaptada às colunas do schema unificado, e
      pode ser gerada com `--relatorio-qualidade` (por padrão, roda sobre
      as vagas da Gupy, já que foi para essa plataforma que o relatório
      original foi desenhado; --relatorio-plataformas permite escolher
      outras/todas).

6. [REVISÃO 2] Corrigida a extração da InfoJobs, que estava devolvendo
   descrições incompletas/erradas. Duas causas raiz, ambas em
   InfoJobsScraper:

   a) `buscar_urls` aceitava qualquer href contendo "/vagas-de-" (plural),
      o que também casa com páginas de LISTAGEM/categoria da InfoJobs
      (ex.: ".../vagas-de-analista-desenvolvimento.aspx", sem ID de vaga
      nenhum), não só com anúncios individuais. Essas páginas de listagem
      eram tratadas como se fossem vagas de verdade. Agora só é aceito o
      padrão de anúncio individual, que sempre tem um ID numérico no final
      (".../vaga-de-...__12345678.aspx").

   b) Quando o JSON-LD não trazia (ou trazia incompleto) o corpo do
      anúncio, `extrair_vaga` caía num fallback genérico que pegava
      `soup.get_text()` da PÁGINA INTEIRA (menu, rodapé, vagas
      relacionadas, avisos de cookie etc.) cortado nos primeiros 5000
      caracteres — o que tanto misturava lixo quanto podia truncar a
      descrição real antes mesmo dela aparecer no texto. Foi adicionado um
      parser específico da estrutura de página da InfoJobs
      (`_extrair_estrutura_infojobs`), baseado num HTML de anúncio real,
      que pega o corpo do anúncio pelo seletor certo (o único <p> com
      classe "white-space-pre-line" dentro do painel da vaga), além de
      título, empresa, localização, salário e tipo de contrato. Esse
      parser agora roda sempre (mesmo quando o JSON-LD é encontrado) e o
      pipeline fica com a descrição mais completa entre as duas fontes.

7. [REVISÃO 3] Corrigida a extração da Catho:

   a) `employmentType` não estava sendo preenchido: a página de detalhe da
      Catho traz "Tipo de contrato" e "Horário de trabalho" como pares de
      `<p class="text-18 font-bold ...">Rótulo</p><p>Valor</p>` dentro da
      div `.text-16`, e isso nunca era lido — só a descrição principal
      (JSON-LD ou fallback de texto cru) era usada. Foi adicionado um
      parser específico da estrutura da Catho (`_extrair_estrutura_catho`)
      que lê esses pares de rótulo/valor e preenche `employmentType` a
      partir de "Tipo de contrato", além de anexar "Horário de trabalho" e
      "Benefícios" (lidos da caixa de Salário) ao final da descrição, para
      não perder essa informação (o schema unificado não tem colunas
      próprias para elas).

   b) `cidade` (e `companyLocation`) não eram detectados quando a página
      não tinha localização estruturada suficiente no JSON-LD: a Catho
      mostra a cidade num `<p>` com um ícone `i_job_location`, no formato
      "1 vaga - Brasilia" ou "1 vaga - Barueri, São Paulo". O parser novo
      extrai esse texto, separa "N vaga(s)" e localidade, e preenche
      `companyLocation`, `cidade` e `uf` (quando há vírgula separando
      cidade e estado).

   Assim como na InfoJobs, esse parser roda sempre (mesmo quando o
   JSON-LD é encontrado), preenchendo apenas o que ficou vazio na camada
   JSON-LD/fallback antigo — nunca sobrescrevendo um dado já obtido de
   fonte mais confiável.

8. [REVISÃO 5] O Indeed foi removido completamente do pipeline. Ele exigia
   um Chrome via Selenium dedicado só para ele (era o único, além da Gupy,
   que dependia disso), sofria bloqueios anti-bot mais agressivos que as
   outras plataformas e ainda assim caía com frequência em captcha visual.
   A classe `IndeedScraper` foi removida, junto com sua entrada em
   `PLATAFORMAS_DISPONIVEIS`/`PLATAFORMAS_SELENIUM` e no default de
   `--plataformas`. Nenhuma outra plataforma foi afetada.

9. [REVISÃO 6] Ajustes feitos após análise do relatório de qualidade dos
   dados (ver comentários "[REVISÃO 6]" espalhados pelo código):

   a) `classificar_vaga` era chamado no filtro de desenvolvimento dentro
      de `BaseScraper.rodar` só para descartar o resultado
      (`eh_dev, _ = classificar_vaga(...)`), fazendo `keywordsDetectadas`
      ficar sempre vazio para todas as plataformas exceto a Gupy (que
      calcula isso de novo, manualmente, dentro do seu próprio
      `extrair_vaga`). Corrigido para aproveitar o resultado já calculado.

   b) `dataColeta` e `keywordsBusca` só eram preenchidos pela Gupy. Agora
      `BaseScraper.rodar` preenche os dois de forma genérica para
      qualquer plataforma (usando a mesma ideia de "palavra-chave que
      encontrou a URL" que já existia só na Gupy), sem nunca sobrescrever
      um valor que a própria plataforma já tenha preenchido.

   c) `descriptionSource` também só era preenchido pela Gupy.
      `_extrair_via_jsonld` (usado por InfoJobs, Catho, Empregos,
      LinkedIn) agora marca "json-ld" quando a descrição vem de lá, e os
      parsers específicos da InfoJobs/Catho marcam "estrutura-pagina"
      (ou "json-ld+estrutura-pagina" quando complementam uma descrição
      que já veio do JSON-LD).

   d) `employmentType` extraído do `__NEXT_DATA__` da Gupy vinha com o
      código interno da Gupy (ex.: "vacancy_type_effective",
      "vacancy_legal_entity"), não um rótulo legível — diferente do que
      vem do JSON-LD ("FULL_TIME") ou dos parsers da Catho/InfoJobs
      (texto em português). Adicionado `GUPY_JOB_TYPE_LABELS` para
      traduzir os códigos conhecidos.

   e) `jobDescriptionHTML` só era preenchido pela Gupy.
      `_extrair_via_jsonld` agora também guarda o HTML bruto do
      `description` do JobPosting, quando existe.

   f) `cidade`/`uf` só eram derivados de `companyLocation` pela Catho
      (que já faz seu próprio parsing) e, parcialmente, pela Gupy.
      Adicionada `dividir_localizacao`, chamada de forma genérica em
      `BaseScraper.rodar`, que tenta separar "Cidade - UF" / "Cidade, UF"
      de `companyLocation` para as demais plataformas.

   g) `jobLocationType` (remoto/híbrido/presencial) só vinha preenchido
      pela Gupy (via JSON-LD/`__NEXT_DATA__`). Adicionada uma heurística
      simples baseada em palavras-chave no título/descrição/localização
      (`inferir_jobLocationType`), aplicada em `BaseScraper.rodar` só
      quando o campo ainda está vazio.

10. [REVISÃO 8 — REVERTIDA] Uma revisão anterior havia adicionado 7
    colunas novas ao schema unificado (`requisitosExigencias`,
    `requisitosValorizado`, `escolaridadeMinima`, `experienciaDesejada`,
    `bancoDados`, `habilidadesTecnicas`, `idiomas`) para guardar, de forma
    estruturada, o conteúdo das seções "Exigências"/"Valorizado" da
    InfoJobs. A pedido do usuário, essas colunas foram REMOVIDAS do
    schema unificado (`COLUNAS_UNIFICADAS`/`VagaUnificada`) para não
    divergir do schema pedido originalmente (item 3 acima) e para evitar
    duplicar a mesma informação em dois lugares ao mesmo tempo (colunas
    próprias + texto solto dentro de `jobDescription`). O parser da
    InfoJobs volta a só anexar o texto dessas seções ao final de
    `jobDescription` (comportamento da revisão 7), sem tentar quebrá-lo
    em colunas adicionais.

11. [REVISÃO 9] Removida a coluna `gupyJobId` do schema unificado
    (`COLUNAS_UNIFICADAS`/`VagaUnificada`). Era a única coluna do schema
    com nome de plataforma específica embutido, só era preenchida pela
    Gupy (ficando "ausente" para as outras 4 plataformas no relatório de
    qualidade, sem que isso indicasse nenhum problema real de coleta) e,
    além disso, era redundante: o ID numérico já vem embutido em
    `jobUrl` (".../job/<id>" ou ".../jobs/<id>"), que continua disponível
    para qualquer plataforma. Quem precisar do ID da vaga da Gupy pode
    extraí-lo de `jobUrl` com o mesmo regex que era usado aqui
    (r"/(?:job|jobs)/(\\d+)").

--------------------------------------------------------------------------
AVISOS IMPORTANTES (leia antes de rodar em produção)
--------------------------------------------------------------------------
* LinkedIn, Catho, InfoJobs e Empregos possuem proteção anti-bot
  bem mais agressiva do que a Gupy. Os seletores de HTML usados aqui foram
  escritos com base na estrutura pública conhecida dessas páginas, mas
  markup de site muda com frequência — é normal precisar ajustar os
  seletores (todos ficam concentrados no topo de cada classe, com
  comentário "AJUSTE AQUI SE O SITE MUDAR").
* Este ambiente de execução usado para gerar o script NÃO tem acesso de
  rede a linkedin.com, catho.com.br, infojobs.com.br,
  empregos.com.br ou portal.gupy.io — então o fluxo de rede completo não
  pôde ser testado ao vivo aqui. O que FOI testado: sintaxe do arquivo
  inteiro, o parser genérico de JSON-LD (JobPosting) contra HTML sintético,
  as funções de normalização/classificação/detecção de Brasil, a
  extração da Gupy (JSON-LD + __NEXT_DATA__ + fallback de texto + datas
  por extenso) contra fixtures que reproduzem a estrutura descrita nos 4
  scripts originais, o parser da InfoJobs (revisão 2) contra um HTML real
  de anúncio fornecido pelo usuário, e (na revisão 3) o novo parser da
  Catho contra um HTML real de anúncio fornecido pelo usuário. Rode
  primeiro com --max-por-plataforma 3 e --diagnostico para validar contra
  os sites reais antes de uma coleta grande.
* Respeite os Termos de Uso de cada site e o robots.txt. Os delays
  default são conservadores de propósito. LinkedIn em especial bloqueia
  agressivamente acesso não autenticado — trate o LinkedInScraper como
  best-effort / baixo volume, não como fonte principal.
* Raspagem de sites de terceiros pode violar os Termos de Serviço deles.
  Use por sua conta e risco, preferencialmente para fins de pesquisa
  pessoal/acadêmica, com volume baixo e respeitando eventuais bloqueios.
* A Gupy ao vivo precisa de Selenium + chromedriver instalados e
  acessíveis no PATH. Sem isso, a coleta da Gupy falha (ver mensagem de
  erro explicativa).
* [REVISÃO 5] O Indeed foi removido do pipeline (ver item 8 do changelog
  acima) — não há mais nenhuma etapa que dependa dele.
* [REVISÃO 6] Os enriquecimentos genéricos descritos no item 9 acima
  (cidade/uf, jobLocationType, keywordsBusca, dataColeta,
  descriptionSource) são heurísticas best-effort, não substituem parsers
  dedicados por plataforma quando a estrutura HTML permite algo mais
  preciso — por isso nunca sobrescrevem um valor já preenchido por um
  parser mais específico.

--------------------------------------------------------------------------
COMO USAR
--------------------------------------------------------------------------
    pip install pandas requests beautifulsoup4 lxml selenium

    # Coleta padrão: Gupy AO VIVO (do zero, sem depender de CSV) + as 4 novas
    python vagas_scraper_unificado.py

    # Só uma plataforma, teste rápido
    python vagas_scraper_unificado.py --plataformas infojobs --max-por-plataforma 5 --diagnostico

    # Se quiser (não é mais o padrão) reaproveitar CSVs antigos da Gupy
    python vagas_scraper_unificado.py --gupy-modo legado

    # Gerar o relatório de qualidade dos dados (código 3) para a Gupy
    python vagas_scraper_unificado.py --gupy-modo live --plataformas "" --relatorio-qualidade

    # Ver todas as opções
    python vagas_scraper_unificado.py --help

Saída: um único CSV (default: dados/bruto/vagas_unificado.csv) com o schema unificado,
e opcionalmente um relatório de qualidade em Markdown.
================================================================================
"""

from __future__ import annotations

import argparse
import html as html_lib
import json
import logging
import random
import re
import sys
import time
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

# Entradas/saídas da fase 0 (raspagem) ficam em dados/bruto/, na raiz do repositório.
DADOS_BRUTOS = Path(__file__).resolve().parent.parent / "dados" / "bruto"

# Selenium é opcional: só é necessário para a descoberta de vagas da Gupy
# ao vivo (--gupy-modo live/ambos, que agora é o padrão). Se não estiver
# instalado, o script avisa claramente e a coleta da Gupy falha, mas as
# outras plataformas continuam funcionando normalmente.
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_DISPONIVEL = True
except ImportError:
    SELENIUM_DISPONIVEL = False


# ================================================================================
# LOGGING
# ================================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)-12s | %(message)s",
    datefmt="%H:%M:%S",
)


def get_logger(nome: str) -> logging.Logger:
    return logging.getLogger(nome)


# ================================================================================
# SCHEMA UNIFICADO
# ================================================================================

COLUNAS_UNIFICADAS = [
    "platform",         # nome da plataforma de origem (gupy, infojobs, ...)
    "jobUrl",           # URL do anúncio
    "jobTitle",         # título da vaga
    "jobDescription",   # descrição da vaga (texto simples)
    "companyName",      # nome da empresa
    "companyLocation",  # localidade da vaga (cidade/UF/país ou "Remoto")
    "companyRating",    # avaliação da empresa (schema.org/aggregateRating), quando disponível
    "companyUrl",       # URL/site da empresa (schema.org/Organization.url ou sameAs)
    "date",             # data de publicação/cadastro do anúncio

    # Campos adicionais (extraídos principalmente da Gupy)
    "jobDescriptionHTML",
    "validThrough",
    "employmentType",
    "jobLocationType",
    "baseSalary",
    "descriptionSource",
    "datePostedSource",
    "validThroughSource",
    "possibleBotBlock",

    # Campos extras, no formato exato do app.py original.
    "cidade",
    "uf",
    "pais",
    "keywordsBusca",
    "keywordsDetectadas",
    "dataColeta",
]


@dataclass
class VagaUnificada:
    """Um registro no schema unificado pedido pelo usuário."""

    platform: str
    jobUrl: str
    jobTitle: Optional[str] = None
    jobDescription: Optional[str] = None
    companyName: Optional[str] = None
    companyLocation: Optional[str] = None
    companyRating: Optional[str] = None
    companyUrl: Optional[str] = None
    date: Optional[str] = None

    jobDescriptionHTML: Optional[str] = None
    validThrough: Optional[str] = None
    employmentType: Optional[str] = None
    jobLocationType: Optional[str] = None
    baseSalary: Optional[str] = None
    descriptionSource: Optional[str] = None
    datePostedSource: Optional[str] = None
    validThroughSource: Optional[str] = None
    possibleBotBlock: Optional[bool] = None

    # Campos extras no formato exato do app.py original.
    cidade: Optional[str] = None
    uf: Optional[str] = None
    pais: Optional[str] = None
    keywordsBusca: Optional[str] = None
    keywordsDetectadas: Optional[str] = None
    dataColeta: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ================================================================================
# CONFIGURAÇÕES GERAIS
# ================================================================================

# Palavras-chave de busca (idêntica à lista `KEYWORDS` do app.py / código 1
# original — 55 termos, cobrindo variações de senioridade, stack e
# nomenclatura pt/en). É usada tanto para montar as URLs de busca da Gupy
# (uma pesquisa por termo) quanto como default de --palavras-chave para as
# demais plataformas.
PALAVRAS_CHAVE_BUSCA = [
    "desenvolvedor",
    "desenvolvedora",
    "developer",
    "software developer",
    "software engineer",
    "engenheiro de software",
    "engenheira de software",
    "programador",
    "programadora",
    "backend",
    "back-end",
    "backend developer",
    "backend engineer",
    "frontend",
    "front-end",
    "frontend developer",
    "frontend engineer",
    "full stack",
    "fullstack",
    "full-stack",
    "full stack developer",
    "full stack engineer",
    "desenvolvedor mobile",
    "desenvolvedora mobile",
    "mobile developer",
    "mobile engineer",
    "desenvolvedor android",
    "desenvolvedora android",
    "android developer",
    "android engineer",
    "desenvolvedor ios",
    "desenvolvedora ios",
    "ios developer",
    "ios engineer",
    "desenvolvedor de sistemas",
    "desenvolvedora de sistemas",
    "analista de desenvolvimento",
    "analista de sistemas",
    "python developer",
    "java developer",
    ".net developer",
    "c# developer",
    "php developer",
    "ruby developer",
    "javascript developer",
    "typescript developer",
    "react developer",
    "node.js developer",
    "nodejs developer",
    "devops",
    "devops engineer",
    "devsecops",
    "sre",
    "site reliability engineer",
]

# Palavras-chave de CLASSIFICAÇÃO (usadas para decidir se uma vaga já
# extraída é ou não de desenvolvimento). Idêntica à lista `DEV_KEYWORDS`
# do app.py / código 1 original.
PALAVRAS_CHAVE_CLASSIFICACAO = [
    "desenvolvedor", "desenvolvedora", "developer", "software developer",
    "software engineer", "engenheiro de software", "engenheira de software",
    "programador", "programadora", "backend", "back-end", "frontend",
    "front-end", "full stack", "fullstack", "mobile developer",
    "mobile engineer", "android developer", "android engineer",
    "ios developer", "ios engineer", "desenvolvedor de sistemas",
    "desenvolvedora de sistemas", "desenvolvimento de software",
    "desenvolvimento de sistemas", "python developer", "java developer",
    ".net developer", "c# developer", "php developer", "ruby developer",
    "javascript developer", "typescript developer", "react developer",
    "node.js developer", "nodejs developer", "devops", "devops engineer",
    "devsecops", "site reliability engineer", "sre",
]

ESTADOS_BR = {
    "AC": "acre", "AL": "alagoas", "AP": "amapa", "AM": "amazonas",
    "BA": "bahia", "CE": "ceara", "DF": "distrito federal",
    "ES": "espirito santo", "GO": "goias", "MA": "maranhao",
    "MT": "mato grosso", "MS": "mato grosso do sul", "MG": "minas gerais",
    "PA": "para", "PB": "paraiba", "PR": "parana", "PE": "pernambuco",
    "PI": "piaui", "RJ": "rio de janeiro", "RN": "rio grande do norte",
    "RS": "rio grande do sul", "RO": "rondonia", "RR": "roraima",
    "SC": "santa catarina", "SP": "sao paulo", "SE": "sergipe",
    "TO": "tocantins",
}

# [REVISÃO 6] Tradução dos códigos internos de tipo de vaga da Gupy
# (vistos em __NEXT_DATA__.job.jobType e nos parâmetros de filtro
# jobTypes[]=... da busca) para rótulos legíveis, no mesmo estilo do que
# já vem pronto do JSON-LD (ex.: "FULL_TIME") ou dos parsers de
# Catho/InfoJobs (texto em português). Completar conforme aparecerem
# outros códigos em dumps de diagnóstico.
GUPY_JOB_TYPE_LABELS = {
    "vacancy_type_effective": "Efetivo (CLT)",
    "vacancy_type_apprentice": "Aprendiz",
    "vacancy_type_internship": "Estágio",
    "vacancy_type_temporary": "Temporário",
    "vacancy_type_cooperative_education": "Cooperado",
    "vacancy_legal_entity": "PJ",
    "vacancy_type_pj": "PJ",
}

# [REVISÃO 6] Heurística leve para inferir jobLocationType (remoto /
# híbrido / presencial) a partir de texto livre (título, descrição,
# localização), usada como fallback genérico em BaseScraper.rodar quando
# a plataforma não extraiu esse dado de forma estruturada. A ordem
# importa: se o texto mencionar "híbrido" E "remoto" ao mesmo tempo,
# tratamos como híbrido (mais específico) antes de cair em remoto.
PADROES_JOB_LOCATION_TYPE = [
    (re.compile(r"h[ií]brid[oa]|hybrid", re.IGNORECASE), "hybrid"),
    (re.compile(r"home\s*office|remot[oa]|remote|trabalho\s+remoto", re.IGNORECASE), "remote"),
    (re.compile(r"presencial|on-?site", re.IGNORECASE), "on-site"),
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36",
]


def cabecalhos_aleatorios() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
    }


# ================================================================================
# UTILITÁRIOS COMPARTILHADOS (antes duplicados em cada script)
# ================================================================================

def normalizar(texto) -> str:
    """Minúsculas, sem acento, espaços colapsados. Usado para comparação de texto."""
    if texto is None:
        return ""
    texto = str(texto).lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def eh_brasil(texto: str) -> bool:
    """Heurística simples para saber se um texto de localização é do Brasil."""
    texto_norm = normalizar(texto)
    if "brasil" in texto_norm or "brazil" in texto_norm:
        return True
    for sigla, estado in ESTADOS_BR.items():
        if re.search(rf"\b{sigla.lower()}\b", texto_norm):
            return True
        if estado in texto_norm:
            return True
    return False


def classificar_vaga(titulo: str, descricao: str) -> tuple[bool, list[str]]:
    """Retorna (é_vaga_de_dev, lista_de_palavras_chave_encontradas)."""
    texto = normalizar(f"{titulo or ''} {descricao or ''}")
    encontradas = [
        kw for kw in PALAVRAS_CHAVE_CLASSIFICACAO
        if normalizar(kw) in texto
    ]
    return (len(encontradas) > 0, encontradas)


def html_para_texto(texto_html: Optional[str]) -> str:
    """Converte um trecho HTML (ex.: descrição JSON-LD) em texto simples legível."""
    if not texto_html:
        return ""
    soup = BeautifulSoup(texto_html, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for tag in soup.find_all(["p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6"]):
        if tag.name == "li":
            tag.insert_before("\n")
        else:
            tag.insert_after("\n")
    texto = soup.get_text(separator="\n")
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    resultado, ultima = [], None
    for linha in linhas:
        if linha == ultima:
            continue
        resultado.append(linha)
        ultima = linha
    return "\n".join(resultado).strip()


PADROES_BLOQUEIO = [
    "captcha", "are you a human", "access denied", "acesso negado",
    "just a moment", "checking your browser", "cloudflare",
    "unusual traffic", "tráfego incomum", "robot check", "verifique que você não é um robô",
]


def parece_bloqueio(texto_pagina: str) -> bool:
    """Heurística para detectar páginas de captcha / bloqueio anti-bot."""
    texto_norm = normalizar(texto_pagina)[:5000]
    return any(padrao in texto_norm for padrao in PADROES_BLOQUEIO)


def parse_data(valor) -> Optional[str]:
    """Tenta converter qualquer formato de data em ISO 8601 (string). Retorna
    None se não conseguir — nunca lança exceção."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    valor = str(valor).strip()
    if not valor:
        return None
    try:
        return pd.to_datetime(valor, utc=True, errors="raise").isoformat()
    except Exception:
        return valor  # mantém o valor bruto em vez de perder a informação


# [REVISÃO 6] Padrão usado por `dividir_localizacao` para separar
# "Cidade - UF" ou "Cidade, UF" (formatos vistos em InfoJobs e Catho).
# Aceita tanto sigla de 2 letras (UF) quanto o nome do estado por
# extenso, já que nem toda plataforma normaliza para sigla.
_PADRAO_LOCALIZACAO_CIDADE_UF = re.compile(
    r"^\s*(?P<cidade>[A-Za-zÀ-ÿ' .]+?)\s*[-,]\s*(?P<uf>[A-Za-zÀ-ÿ ]{2,})\s*$"
)


def dividir_localizacao(texto: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """[REVISÃO 6] Tenta separar uma string livre de localização (ex.:
    "São Paulo - SP", "Barueri, São Paulo") em (cidade, uf). Usada como
    fallback genérico em BaseScraper.rodar para plataformas que só
    preenchem companyLocation como texto único (hoje: InfoJobs, Empregos,
    LinkedIn — Catho e Gupy já fazem esse split em parsers dedicados).
    Retorna (None, None) quando não reconhece o padrão."""
    if not texto:
        return None, None
    match = _PADRAO_LOCALIZACAO_CIDADE_UF.match(texto)
    if not match:
        return None, None
    cidade = match.group("cidade").strip()
    uf_bruta = match.group("uf").strip()
    if not cidade or not uf_bruta:
        return None, None
    # Se vier o nome do estado por extenso, tenta mapear para a sigla de
    # 2 letras, para manter consistência com o restante do dataset.
    if len(uf_bruta) > 2:
        uf_norm = normalizar(uf_bruta)
        sigla = next(
            (sigla for sigla, nome_estado in ESTADOS_BR.items() if nome_estado == uf_norm),
            None,
        )
        uf_bruta = sigla or uf_bruta
    return cidade, uf_bruta


def inferir_jobLocationType(
    titulo: Optional[str], descricao: Optional[str], localizacao: Optional[str]
) -> Optional[str]:
    """[REVISÃO 6] Heurística leve (título + início da descrição +
    localização) para preencher jobLocationType quando a plataforma não
    extraiu esse dado de forma estruturada. Best-effort: só é chamada em
    BaseScraper.rodar quando o campo ainda está vazio, e nunca sobrescreve
    um valor já obtido de fonte mais confiável (JSON-LD/__NEXT_DATA__)."""
    texto = " ".join(filter(None, [titulo, localizacao, (descricao or "")[:500]]))
    if not texto:
        return None
    for padrao, rotulo in PADROES_JOB_LOCATION_TYPE:
        if padrao.search(texto):
            return rotulo
    return None


def requisitar_com_retry(
    session: requests.Session,
    url: str,
    tentativas: int = 3,
    timeout: int = 25,
    espera_base: float = 2.0,
    logger: Optional[logging.Logger] = None,
) -> Optional[requests.Response]:
    """GET com retry + backoff exponencial. Retorna None em falha definitiva."""
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = session.get(url, timeout=timeout, headers=cabecalhos_aleatorios())
            if resposta.status_code == 200:
                return resposta
            if resposta.status_code in (403, 429, 503):
                espera = espera_base * (2 ** (tentativa - 1)) + random.uniform(0, 1)
                if logger:
                    logger.warning(
                        "HTTP %s em %s (tentativa %d/%d) — aguardando %.1fs",
                        resposta.status_code, url, tentativa, tentativas, espera,
                    )
                time.sleep(espera)
                continue
            if logger:
                logger.info("HTTP %s em %s — descartando", resposta.status_code, url)
            return None
        except requests.RequestException as erro:
            espera = espera_base * (2 ** (tentativa - 1))
            if logger:
                logger.warning(
                    "Erro de rede em %s (tentativa %d/%d): %s — aguardando %.1fs",
                    url, tentativa, tentativas, erro, espera,
                )
            time.sleep(espera)
    return None


def extrair_jobposting_ld(soup: BeautifulSoup) -> Optional[dict]:
    """Extrator genérico de dados estruturados schema.org/JobPosting.

    A maioria dos grandes portais de vagas (Catho, InfoJobs,
    Empregos, LinkedIn, Gupy) publica um bloco <script type="application/
    ld+json"> com @type = "JobPosting" para SEO / Google for Jobs. Sempre
    que esse bloco existe, é a fonte mais confiável e estruturada — muito
    mais estável do que depender de classes CSS, que mudam com frequência.
    """
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        conteudo = script.string or script.get_text()
        if not conteudo:
            continue
        # Alguns portais (a Gupy em especial) gravam o JSON-LD com
        # entidades HTML escapadas dentro do <script> (ex.: &quot;). O
        # html.parser não decodifica isso sozinho, e sem o unescape o
        # json.loads sempre falha silenciosamente — a vaga cairia (sem
        # aviso) no fallback de texto. unescape() é seguro mesmo quando
        # não há nada escapado (é idempotente).
        conteudo = html_lib.unescape(conteudo)
        try:
            objeto = json.loads(conteudo)
        except Exception:
            continue

        candidatos = []
        if isinstance(objeto, dict):
            candidatos.append(objeto)
            grafo = objeto.get("@graph")
            if isinstance(grafo, list):
                candidatos.extend(grafo)
        elif isinstance(objeto, list):
            candidatos.extend(objeto)

        for item in candidatos:
            if not isinstance(item, dict):
                continue
            tipo = item.get("@type")
            tipos = tipo if isinstance(tipo, list) else [tipo]
            if "JobPosting" in tipos:
                return item
    return None


def extrair_urls_de_itemlist_ld(soup: BeautifulSoup, base_url: str) -> set[str]:
    """Fallback genérico: muitas páginas de LISTAGEM de vagas (não só a
    página de detalhe) publicam um JSON-LD do tipo ItemList com um item por
    vaga, cada um apontando para a URL de detalhe. Quando existe, é muito
    mais confiável do que caçar padrões de href na marcação HTML (que muda
    o tempo todo). Retorna um conjunto de URLs absolutas."""
    urls: set[str] = set()
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        conteudo = script.string or script.get_text()
        if not conteudo:
            continue
        try:
            objeto = json.loads(conteudo)
        except Exception:
            continue

        candidatos = objeto if isinstance(objeto, list) else [objeto]
        for item in candidatos:
            if not isinstance(item, dict):
                continue
            tipo = item.get("@type")
            tipos = tipo if isinstance(tipo, list) else [tipo]

            if "ItemList" in tipos:
                elementos = item.get("itemListElement") or []
                for elemento in elementos:
                    if not isinstance(elemento, dict):
                        continue
                    url_item = elemento.get("url")
                    if not url_item and isinstance(elemento.get("item"), dict):
                        url_item = elemento["item"].get("url")
                    if url_item:
                        urls.add(urljoin(base_url, url_item))

            # Algumas páginas listam vários JobPosting soltos direto no
            # array, sem envelope ItemList.
            if "JobPosting" in tipos:
                url_item = item.get("url")
                if url_item:
                    urls.add(urljoin(base_url, url_item))

    return urls


def salvar_dump_diagnostico(nome_plataforma: str, palavra_chave: str, html: str) -> str:
    """Salva o HTML bruto de uma página de busca em disco, para permitir
    depuração quando 0 URLs são encontradas (por exemplo, para me enviar o
    arquivo e eu corrigir o seletor). Retorna o caminho salvo."""
    pasta = DADOS_BRUTOS / "diagnostico_html"
    pasta.mkdir(parents=True, exist_ok=True)
    nome_arquivo = f"{nome_plataforma}_{normalizar(palavra_chave).replace(' ', '-')}.html"
    caminho = pasta / nome_arquivo
    try:
        caminho.write_text(html, encoding="utf-8", errors="ignore")
    except Exception:
        pass
    return str(caminho)


def extrair_empresa_de_jobposting(job: dict) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """A partir de um dict JobPosting, extrai (nome_empresa, url_empresa, rating)."""
    nome = url = rating = None
    organizacao = job.get("hiringOrganization")
    if isinstance(organizacao, dict):
        nome = organizacao.get("name")
        url = organizacao.get("url") or organizacao.get("sameAs")
        avaliacao = organizacao.get("aggregateRating")
        if isinstance(avaliacao, dict):
            valor = avaliacao.get("ratingValue")
            contagem = avaliacao.get("ratingCount") or avaliacao.get("reviewCount")
            if valor is not None:
                rating = f"{valor}" + (f" ({contagem} avaliações)" if contagem else "")
    elif isinstance(organizacao, str):
        nome = organizacao
    return nome, url, rating


def extrair_localizacao_de_jobposting(job: dict) -> Optional[str]:
    """A partir de um dict JobPosting, monta uma string "Cidade, UF, País"."""
    local = job.get("jobLocation")
    if isinstance(local, list):
        local = local[0] if local else None
    if not isinstance(local, dict):
        tipo_local = job.get("jobLocationType")
        return "Remoto" if tipo_local else None
    endereco = local.get("address")
    partes = []
    if isinstance(endereco, dict):
        for chave in ("addressLocality", "addressRegion", "addressCountry"):
            valor = endereco.get(chave)
            if valor:
                partes.append(str(valor))
    elif isinstance(endereco, str):
        partes.append(endereco)
    return ", ".join(partes) if partes else None


def buscar_rating_empresa(session: requests.Session, url_empresa: str, logger=None) -> Optional[str]:
    """Fetch opcional da página da empresa para tentar achar aggregateRating
    (schema.org/Organization). Best-effort: qualquer falha retorna None."""
    if not url_empresa:
        return None
    resposta = requisitar_com_retry(session, url_empresa, tentativas=1, timeout=15, logger=logger)
    if resposta is None:
        return None
    try:
        soup = BeautifulSoup(resposta.text, "html.parser")
        for script in soup.find_all("script", type="application/ld+json"):
            conteudo = script.string or script.get_text()
            if not conteudo:
                continue
            try:
                objeto = json.loads(conteudo)
            except Exception:
                continue
            candidatos = objeto if isinstance(objeto, list) else [objeto]
            for item in candidatos:
                if not isinstance(item, dict):
                    continue
                avaliacao = item.get("aggregateRating")
                if isinstance(avaliacao, dict) and avaliacao.get("ratingValue"):
                    contagem = avaliacao.get("ratingCount") or avaliacao.get("reviewCount")
                    return f"{avaliacao['ratingValue']}" + (f" ({contagem} avaliações)" if contagem else "")
    except Exception:
        return None
    return None


# ================================================================================
# CLASSE BASE — toda plataforma nova implementa só 2 métodos
# ================================================================================

class BaseScraper(ABC):
    """Classe base com toda a lógica comum (sessão HTTP, rate limit, dedupe,
    filtro Brasil/dev, retry, conversão para o schema unificado).

    Uma plataforma nova só precisa implementar:
      - `buscar_urls(palavra_chave, max_paginas)`  -> descoberta de links
      - `extrair_vaga(url)`                        -> dict no schema unificado
    """

    platform: str = "base"
    delay_min: float = 1.5
    delay_max: float = 3.5

    def __init__(self, buscar_rating: bool = False, diagnostico: bool = False):
        self.session = requests.Session()
        self.logger = get_logger(self.platform)
        self.buscar_rating = buscar_rating
        self.diagnostico = diagnostico

    # ---- a implementar em cada subclasse -------------------------------

    @abstractmethod
    def buscar_urls(self, palavra_chave: str, max_paginas: int) -> set[str]:
        """Retorna um conjunto de URLs de anúncios de vaga para uma palavra-chave."""
        raise NotImplementedError

    @abstractmethod
    def extrair_vaga(self, url: str) -> Optional[VagaUnificada]:
        """Faz o fetch + parse de UM anúncio e retorna um VagaUnificada (ou
        None se não for possível extrair / vaga inválida)."""
        raise NotImplementedError

    # ---- orquestração comum ---------------------------------------------

    def _pausa(self):
        time.sleep(random.uniform(self.delay_min, self.delay_max))

    def rodar(
        self,
        palavras_chave: list[str],
        max_paginas_por_palavra: int = 3,
        max_vagas: Optional[int] = None,
        filtrar_brasil: bool = True,
        filtrar_dev: bool = True,
    ) -> pd.DataFrame:
        self.logger.info("=" * 60)
        self.logger.info("Iniciando coleta: %s", self.platform)
        self.logger.info("=" * 60)

        urls_encontradas: set[str] = set()
        # [REVISÃO 6] Rastreia qual(is) palavra(s)-chave de busca encontrou
        # cada URL — igual ao que só a Gupy fazia (self.keyword_por_url) —
        # para poder preencher keywordsBusca de forma genérica, para
        # qualquer plataforma, mais abaixo.
        url_keywords: dict[str, set[str]] = {}
        for numero, palavra in enumerate(palavras_chave, start=1):
            self.logger.info("[%d/%d] Descobrindo URLs para: %s", numero, len(palavras_chave), palavra)
            try:
                novas = self.buscar_urls(palavra, max_paginas_por_palavra)
                self.logger.info("  -> %d URLs encontradas (total único: %d)", len(novas), len(urls_encontradas | novas))
                urls_encontradas |= novas
                for url_nova in novas:
                    url_keywords.setdefault(url_nova, set()).add(palavra)
            except Exception as erro:
                self.logger.warning("  Falha na descoberta com '%s': %s", palavra, erro)
            self._pausa()
            if max_vagas and len(urls_encontradas) >= max_vagas:
                break

        if max_vagas:
            urls_encontradas = set(list(urls_encontradas)[:max_vagas])

        self.logger.info("Total de URLs únicas para processar: %d", len(urls_encontradas))

        registros = []
        for numero, url in enumerate(sorted(urls_encontradas), start=1):
            self.logger.info("[%d/%d] %s", numero, len(urls_encontradas), url)
            try:
                vaga = self.extrair_vaga(url)
            except Exception as erro:
                self.logger.warning("  Erro ao extrair %s: %s", url, erro)
                vaga = None

            if vaga is None:
                self._pausa()
                continue

            texto_localizacao = " ".join(filter(None, [vaga.companyLocation, vaga.jobDescription or ""]))
            if filtrar_brasil and not eh_brasil(texto_localizacao):
                self.logger.info("  -> descartada: não identificada como Brasil")
                self._pausa()
                continue

            if filtrar_dev:
                # [REVISÃO 6] Antes o resultado era descartado com
                # `_`, então keywordsDetectadas nunca era preenchido
                # (exceto na Gupy, que recalcula isso por conta própria).
                eh_dev, keywords_detectadas = classificar_vaga(vaga.jobTitle, vaga.jobDescription)
                if not eh_dev:
                    self.logger.info("  -> descartada: não classificada como desenvolvimento")
                    self._pausa()
                    continue
                if not vaga.keywordsDetectadas and keywords_detectadas:
                    vaga.keywordsDetectadas = "; ".join(keywords_detectadas)

            if self.buscar_rating and vaga.companyUrl and not vaga.companyRating:
                vaga.companyRating = buscar_rating_empresa(self.session, vaga.companyUrl, self.logger)

            # [REVISÃO 6] Enriquecimentos genéricos best-effort — todos só
            # atuam quando o campo ainda está vazio, então nunca
            # sobrescrevem um valor já obtido por um parser mais
            # específico da própria plataforma (ex.: Gupy e Catho já
            # preenchem cidade/uf e jobLocationType em seus próprios
            # parsers, então esses blocos praticamente não fazem nada
            # para elas).
            if not vaga.keywordsBusca:
                palavras_da_url = url_keywords.get(url)
                if palavras_da_url:
                    vaga.keywordsBusca = "; ".join(sorted(palavras_da_url))

            if vaga.companyLocation and not (vaga.cidade and vaga.uf):
                cidade_inferida, uf_inferida = dividir_localizacao(vaga.companyLocation)
                if not vaga.cidade and cidade_inferida:
                    vaga.cidade = cidade_inferida
                if not vaga.uf and uf_inferida:
                    vaga.uf = uf_inferida

            if not vaga.jobLocationType:
                tipo_inferido = inferir_jobLocationType(
                    vaga.jobTitle, vaga.jobDescription, vaga.companyLocation
                )
                if tipo_inferido:
                    vaga.jobLocationType = tipo_inferido

            if not vaga.dataColeta:
                vaga.dataColeta = datetime.now().isoformat()

            registros.append(vaga.to_dict())
            self._pausa()

        df = pd.DataFrame(registros, columns=COLUNAS_UNIFICADAS)
        if not df.empty:
            df = df.drop_duplicates(subset=["jobUrl"], keep="first")
        self.logger.info("Coleta finalizada para %s: %d vagas válidas", self.platform, len(df))
        return df

    # ---- helper comum para extração via JSON-LD --------------------------

    def _extrair_via_jsonld(self, url: str, soup: BeautifulSoup) -> Optional[VagaUnificada]:
        job = extrair_jobposting_ld(soup)
        if not job:
            return None
        titulo = job.get("title")
        descricao_html = job.get("description")
        descricao = html_para_texto(descricao_html) if descricao_html else None
        nome_empresa, url_empresa, rating_empresa = extrair_empresa_de_jobposting(job)
        localizacao = extrair_localizacao_de_jobposting(job)
        data = parse_data(job.get("datePosted"))
        return VagaUnificada(
            platform=self.platform,
            jobUrl=url,
            jobTitle=titulo,
            jobDescription=descricao,
            # [REVISÃO 6] Antes só a Gupy preenchia o HTML bruto da
            # descrição; o JobPosting genérico já tem esse dado disponível
            # (job["description"]) para qualquer plataforma que publique
            # JSON-LD, então passamos a guardá-lo aqui também.
            jobDescriptionHTML=str(descricao_html) if descricao_html else None,
            companyName=nome_empresa,
            companyLocation=localizacao,
            companyUrl=url_empresa,
            companyRating=rating_empresa,
            date=data,
            # [REVISÃO 6] Idem: antes só a Gupy registrava de onde veio a
            # descrição. Isso deixa a seção "Origem da descrição" do
            # relatório de qualidade representativa para todas as
            # plataformas, não só para a Gupy.
            descriptionSource="json-ld" if descricao else None,
        )


# ================================================================================
# GUPY — funções de "aprofundamento", portadas de aprofundar_vagas_gupy.py
# (JSON-LD + __NEXT_DATA__ + fallback de texto) e de
# completar_datas_e_relatorio.py (data por extenso em pt-BR). Usadas para
# enriquecer o que a extração básica (igual ao app.py) já trouxe, sempre
# só preenchendo o que ficou vazio — nunca sobrescrevendo dado já obtido
# de fonte mais confiável.
# ================================================================================

INDICIOS_BLOQUEIO_GUPY = [
    "captcha", "cloudflare", "just a moment", "attention required",
    "enable javascript", "habilite os scripts", "verificando", "access denied",
]

MARCADORES_INICIO_DESCRICAO_GUPY = [
    "descrição da vaga",
    "job description",
]

MARCADORES_FIM_DESCRICAO_GUPY = [
    "etapas do processo",
    "recruitment steps",
    "hiring process",
    "processo seletivo",
]

MESES_PT_GUPY = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5,
    "junho": 6, "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10,
    "novembro": 11, "dezembro": 12,
}

PADRAO_PUBLICADA_GUPY = re.compile(
    r"Publicad[ao]\s+em\s+(\d{1,2}\s+de\s+[A-Za-zçÇãÃéÉíÍóÓúÚâÂêÊôÔ]+\s+de\s+\d{4})",
    re.IGNORECASE,
)

PADRAO_VALIDADE_GUPY = re.compile(
    r"Inscri[cç][oõ]es\s+abertas\s+at[eé]\s+(\d{1,2}\s+de\s+[A-Za-zçÇãÃéÉíÍóÓúÚâÂêÊôÔ]+\s+de\s+\d{4})",
    re.IGNORECASE,
)


def _gupy_remover_acentos(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _gupy_parse_data_extenso(texto_data: str) -> Optional[datetime]:
    """Converte "18 de agosto de 2026" -> datetime(2026, 8, 18). None se
    não conseguir interpretar."""
    if not texto_data:
        return None
    texto_data = _gupy_remover_acentos(texto_data.strip().lower())
    match = re.match(r"(\d{1,2})\s+de\s+([a-z]+)\s+de\s+(\d{4})", texto_data)
    if not match:
        return None
    dia, mes_nome, ano = match.groups()
    mes = MESES_PT_GUPY.get(mes_nome)
    if mes is None:
        return None
    try:
        return datetime(int(ano), mes, int(dia))
    except ValueError:
        return None


def _gupy_extrair_data_publicada_do_texto(texto_pagina: str) -> Optional[datetime]:
    """Fallback (completar_datas_e_relatorio.py): procura "Publicada em
    18 de agosto de 2026" no texto renderizado da página."""
    if not texto_pagina:
        return None
    match = PADRAO_PUBLICADA_GUPY.search(texto_pagina)
    if not match:
        return None
    return _gupy_parse_data_extenso(match.group(1))


def _gupy_extrair_data_validade_do_texto(texto_pagina: str) -> Optional[datetime]:
    """Fallback (completar_datas_e_relatorio.py): procura "Inscrições
    abertas até 30 de setembro de 2026" no texto renderizado da página."""
    if not texto_pagina:
        return None
    match = PADRAO_VALIDADE_GUPY.search(texto_pagina)
    if not match:
        return None
    return _gupy_parse_data_extenso(match.group(1))


def _gupy_parece_bloqueio(texto_pagina: str) -> bool:
    """Indícios de bloqueio anti-bot específicos observados em páginas da
    Gupy — complementa (não substitui) a heurística genérica parece_bloqueio."""
    if not texto_pagina:
        return False
    texto_lower = texto_pagina.lower()
    return any(indicio in texto_lower for indicio in INDICIOS_BLOQUEIO_GUPY)


def _gupy_encontrar_next_data(soup: BeautifulSoup) -> Optional[dict]:
    """Extrai o objeto `job` de dentro do <script id="__NEXT_DATA__">
    (aplicação Next.js). IMPORTANTE: precisa ser chamada ANTES de remover
    as tags <script> do soup (o que _extrair_pagina_completa_gupy faz)."""
    script = soup.find("script", id="__NEXT_DATA__")
    if not script:
        return None
    conteudo = script.string or script.get_text()
    if not conteudo:
        return None
    conteudo = html_lib.unescape(conteudo)
    try:
        dados = json.loads(conteudo)
    except Exception:
        return None
    job = dados.get("props", {}).get("pageProps", {}).get("job", {})
    return job or None


def _gupy_extrair_de_next_data(job_next: Optional[dict]) -> dict:
    """Extrai campos detalhados a partir do objeto job do __NEXT_DATA__.
    Chaves alinhadas com os nomes usados em extrair_vaga (jobTitle,
    jobDescription, cidade, uf, pais etc.) para facilitar o merge."""
    dados = {
        "jobTitle": "",
        "jobDescription": "",
        "jobDescriptionHTML": "",
        "companyName": "",
        "cidade": "",
        "uf": "",
        "pais": "",
        "date": "",
        "validThrough": "",
        "employmentType": "",
        "jobLocationType": "",
    }
    if not job_next:
        return dados

    dados["jobTitle"] = job_next.get("name") or job_next.get("title") or ""

    # A Gupy costuma dividir a descrição em vários blocos separados
    # (description, responsibilities, prerequisites, relevantExperiences)
    # que o JSON-LD normalmente já concatena em um só campo "description".
    blocos_html = [
        job_next.get("description", ""),
        job_next.get("responsibilities", ""),
        job_next.get("prerequisites", ""),
        job_next.get("relevantExperiences", ""),
    ]
    html_completo = "".join(b for b in blocos_html if b)
    dados["jobDescriptionHTML"] = html_completo
    dados["jobDescription"] = html_para_texto(html_completo)

    career_page = job_next.get("careerPage") or {}
    dados["companyName"] = career_page.get("name", "")

    dados["cidade"] = job_next.get("addressCity", "")
    dados["uf"] = job_next.get("addressState", "")
    dados["pais"] = job_next.get("addressCountry", "")

    publicada = job_next.get("publishedAt", "")
    if publicada:
        dados["date"] = str(publicada)[:10]

    validade = job_next.get("registerEndDate") or job_next.get("expiresAt") or ""
    if validade:
        dados["validThrough"] = str(validade)[:10]

    # [REVISÃO 6] job_next["jobType"] vem com o código interno da Gupy
    # (ex.: "vacancy_type_effective"), não um rótulo legível. Traduzimos
    # pelos códigos conhecidos em GUPY_JOB_TYPE_LABELS; se o código for
    # novo/desconhecido, mantemos o valor bruto (melhor que perder a
    # informação, mas ainda vale adicionar o novo código ao dicionário).
    codigo_tipo = job_next.get("jobType", "")
    dados["employmentType"] = GUPY_JOB_TYPE_LABELS.get(codigo_tipo, codigo_tipo)
    dados["jobLocationType"] = job_next.get("workplaceType", "")

    return dados


def _gupy_mesclar_dados(dados_principal: dict, dados_next_data: dict) -> tuple[dict, str, str]:
    """Preenche, em dados_principal, só os campos que vieram vazios,
    usando dados_next_data como fallback. Nunca sobrescreve valor já
    obtido de fonte mais confiável (JSON-LD)."""
    origem_pub = ""
    origem_val = ""
    for chave, valor_fallback in dados_next_data.items():
        valor_atual = dados_principal.get(chave)
        if (not valor_atual) and valor_fallback:
            dados_principal[chave] = valor_fallback
            if chave == "date":
                origem_pub = "next_data"
            if chave == "validThrough":
                origem_val = "next_data"
    return dados_principal, origem_pub, origem_val


def _gupy_extrair_texto_vaga_da_pagina(pagina_completa_texto: str) -> str:
    """Fallback (aprofundar_vagas_gupy.py) para quando nem JSON-LD nem
    __NEXT_DATA__ trazem descrição: isola o bloco de texto entre os
    marcadores "Descrição da vaga" ... "Etapas do processo"."""
    if not pagina_completa_texto:
        return ""
    linhas = pagina_completa_texto.splitlines()
    linhas_lower = [linha.lower() for linha in linhas]
    idx_inicio = None
    idx_fim = None
    for i, linha in enumerate(linhas_lower):
        if idx_inicio is None:
            if any(marcador in linha for marcador in MARCADORES_INICIO_DESCRICAO_GUPY):
                idx_inicio = i
            continue
        if any(marcador in linha for marcador in MARCADORES_FIM_DESCRICAO_GUPY):
            idx_fim = i
            break
    if idx_inicio is None:
        return ""
    if idx_fim is None:
        idx_fim = min(idx_inicio + 400, len(linhas))
    return "\n".join(linhas[idx_inicio:idx_fim]).strip()


def _extrair_pagina_completa_gupy(soup: BeautifulSoup) -> str:
    """Texto completo da página (sem script/style/svg), usado como base
    tanto para o fallback de descrição quanto para o fallback de datas
    por extenso e para a checagem de bloqueio anti-bot. IMPORTANTE:
    remove as tags <script> do soup — por isso precisa ser chamada DEPOIS
    de _gupy_encontrar_next_data."""
    for tag in soup.find_all(["script", "style", "noscript", "svg"]):
        tag.decompose()
    texto = soup.get_text(separator="\n")
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    return "\n".join(linhas)


# ================================================================================
# GUPY — descoberta via Selenium (igual ao app.py) + extração de detalhe
# aprofundada (igual a aprofundar_vagas_gupy.py + completar_datas_e_relatorio.py)
# ================================================================================

class GupyScraper(BaseScraper):

    platform = "gupy"
    BASE_URL_BUSCA = "https://portal.gupy.io/job-search/term="
    TEMPO_SCROLL = 1.5
    MAX_SEM_MUDANCA = 4

    def __init__(self, buscar_rating: bool = False, headless: bool = True, diagnostico: bool = False):
        super().__init__(buscar_rating=buscar_rating, diagnostico=diagnostico)
        self.headless = headless
        self._driver = None
        # Igual ao `keyword_por_url` do app.py: para cada URL de vaga
        # descoberta, guarda a(s) palavra(s)-chave de busca que a
        # encontraram (uma URL pode aparecer em buscas por várias
        # palavras diferentes).
        self.keyword_por_url: dict[str, list[str]] = {}

    def _get_driver(self):
        if not SELENIUM_DISPONIVEL:
            raise RuntimeError(
                "Selenium não está instalado. Rode `pip install selenium` e "
                "garanta que o chromedriver está no PATH para usar a "
                "descoberta ao vivo da Gupy (que agora é o modo padrão, "
                "--gupy-modo live)."
            )
        if self._driver is None:
            options = ChromeOptions()
            if self.headless:
                options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--lang=pt-BR")
            self._driver = webdriver.Chrome(options=options)
        return self._driver

    def fechar(self):
        if self._driver is not None:
            self._driver.quit()
            self._driver = None

    def buscar_urls(self, palavra_chave: str, max_paginas: int) -> set[str]:
        # Para a Gupy, "max_paginas" não se aplica (é scroll infinito na
        # mesma página) — o parâmetro é ignorado aqui por consistência de
        # assinatura com as outras plataformas.
        driver = self._get_driver()
        wait = WebDriverWait(driver, 20)
        termo = quote(palavra_chave, safe="")
        url_busca = self.BASE_URL_BUSCA + termo

        try:
            driver.get(url_busca)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)
        except Exception as erro:
            self.logger.warning("Erro ao abrir busca Gupy: %s", erro)
            return set()

        urls = set()
        altura_anterior = 0
        sem_mudanca = 0

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.TEMPO_SCROLL)
            altura_atual = driver.execute_script("return document.body.scrollHeight")

            for elemento in driver.find_elements(By.TAG_NAME, "a"):
                try:
                    href = elemento.get_attribute("href")
                except Exception:
                    continue
                if href and ("/job/" in href or "/jobs/" in href):
                    href = href.split("?")[0]
                    urls.add(href)
                    # Registro do vínculo URL <-> palavra-chave (igual ao
                    # app.py), para preencher depois o Keywords_Busca.
                    self.keyword_por_url.setdefault(href, [])
                    self.keyword_por_url[href].append(palavra_chave)

            if altura_atual == altura_anterior:
                sem_mudanca += 1
            else:
                sem_mudanca = 0
            if sem_mudanca >= self.MAX_SEM_MUDANCA:
                break
            altura_anterior = altura_atual

        return urls

    def extrair_vaga(self, url: str) -> Optional[VagaUnificada]:
        """Extração em 2 camadas, replicando o pipeline original de 3
        scripts em uma única passada (sem precisar buscar a mesma URL
        duas vezes):

        1) CAMADA BÁSICA (igual ao app.py): JSON-LD (schema.org/JobPosting)
           + fallback de título via <h1>.
        2) CAMADA DE APROFUNDAMENTO (igual a aprofundar_vagas_gupy.py +
           completar_datas_e_relatorio.py): preenche com __NEXT_DATA__
           (mais confiável para datas) o que ficou vazio na camada 1;
           se a descrição continuar vazia, tenta isolar o bloco de texto
           da vaga na página; se as datas continuarem vazias, tenta o
           texto por extenso ("Publicada em ...", "Inscrições abertas
           até ..."); por fim, sinaliza possível bloqueio anti-bot.

        Cada campo guarda de onde veio (json-ld / next_data / fallback-
        página / texto-página), assim como nos scripts originais.
        """
        resposta = requisitar_com_retry(self.session, url, logger=self.logger)
        if resposta is None:
            return None
        soup = BeautifulSoup(resposta.text, "html.parser")

        # ============================================================
        # CAMADA BÁSICA — igual ao app.py (JSON-LD)
        # ============================================================
        job = extrair_jobposting_ld(soup)

        dados = {
            "jobTitle": None,
            "jobDescription": None,
            "jobDescriptionHTML": None,
            "companyName": None,
            "companyUrl": None,
            "companyRating": None,
            "cidade": None,
            "uf": None,
            "pais": None,
            "date": None,
            "validThrough": None,
            "employmentType": None,
            "jobLocationType": None,
            "baseSalary": None,
        }

        descricao_origem = None
        data_publicacao_origem = None
        data_validade_origem = None
        possivel_bloqueio = False

        if job:
            dados["jobTitle"] = job.get("title")

            descricao_html = job.get("description")
            descricao_html = str(descricao_html) if descricao_html else None
            dados["jobDescriptionHTML"] = descricao_html
            dados["jobDescription"] = html_para_texto(descricao_html) if descricao_html else None
            if dados["jobDescription"]:
                descricao_origem = "json-ld"

            dados["date"] = job.get("datePosted")
            dados["validThrough"] = job.get("validThrough")

            nome_empresa, url_empresa, rating_empresa = extrair_empresa_de_jobposting(job)
            dados["companyName"] = nome_empresa
            dados["companyUrl"] = url_empresa
            dados["companyRating"] = rating_empresa

            local = job.get("jobLocation")
            if isinstance(local, dict):
                endereco = local.get("address")
                if isinstance(endereco, dict):
                    dados["cidade"] = endereco.get("addressLocality")
                    dados["uf"] = endereco.get("addressRegion")
                    dados["pais"] = endereco.get("addressCountry")

            if job.get("jobLocationType"):
                dados["jobLocationType"] = job.get("jobLocationType")

            employment = job.get("employmentType")
            if isinstance(employment, list):
                employment = "; ".join(map(str, employment))
            dados["employmentType"] = employment

            salario = job.get("baseSalary")
            if salario:
                try:
                    dados["baseSalary"] = json.dumps(salario, ensure_ascii=False)
                except Exception:
                    dados["baseSalary"] = str(salario)

        # fallback de título direto da página (igual ao app.py)
        if not dados["jobTitle"]:
            h1 = soup.find("h1")
            if h1:
                dados["jobTitle"] = h1.get_text(" ", strip=True)

        # ============================================================
        # CAMADA DE APROFUNDAMENTO — igual a aprofundar_vagas_gupy.py
        # ============================================================

        # precisa vir ANTES de _extrair_pagina_completa_gupy, que remove
        # as tags <script> do soup
        job_next = _gupy_encontrar_next_data(soup)
        if job_next:
            dados_next = _gupy_extrair_de_next_data(job_next)
            descricao_antes_vazia = not dados["jobDescription"]

            dados, origem_pub, origem_val = _gupy_mesclar_dados(dados, dados_next)

            if origem_pub:
                data_publicacao_origem = origem_pub
            if origem_val:
                data_validade_origem = origem_val
            if descricao_antes_vazia and dados["jobDescription"]:
                descricao_origem = "next_data"

        pagina_completa = _extrair_pagina_completa_gupy(soup)

        # fallback de descrição por texto da página
        if not dados["jobDescription"]:
            texto_fallback = _gupy_extrair_texto_vaga_da_pagina(pagina_completa)
            if texto_fallback:
                dados["jobDescription"] = texto_fallback
                descricao_origem = "fallback-pagina"
            else:
                bloqueado = parece_bloqueio(pagina_completa[:3000]) or _gupy_parece_bloqueio(pagina_completa[:3000])
                possivel_bloqueio = bloqueado
                if bloqueado:
                    self.logger.warning("Possível bloqueio anti-bot em %s", url)

        # fallback de datas por texto por extenso (completar_datas_e_relatorio.py)
        if not dados["date"]:
            data_extenso = _gupy_extrair_data_publicada_do_texto(pagina_completa)
            if data_extenso:
                dados["date"] = data_extenso.isoformat()
                data_publicacao_origem = "texto-pagina"

        if not dados["validThrough"]:
            data_val_extenso = _gupy_extrair_data_validade_do_texto(pagina_completa)
            if data_val_extenso:
                dados["validThrough"] = data_val_extenso.isoformat()
                data_validade_origem = "texto-pagina"

        if not dados["jobTitle"] and not dados["jobDescription"]:
            return None

        # ============================================================
        # FILTROS (igual ao app.py) — Brasil + classificação de dev
        # ============================================================

        texto_localizacao = " ".join(
            filter(None, [
                str(dados["cidade"] or ""),
                str(dados["uf"] or ""),
                str(dados["pais"] or ""),
                pagina_completa,
            ])
        )
        if not eh_brasil(texto_localizacao):
            self.logger.info("  -> descartada: não identificada como Brasil")
            return None

        eh_dev, keywords_detectadas = classificar_vaga(dados["jobTitle"], dados["jobDescription"])
        if not eh_dev:
            self.logger.info("  -> descartada: não classificada como desenvolvimento")
            return None

        # ---- normaliza data de publicação para ISO, quando possível ----
        data_publicacao_iso = None
        if dados["date"]:
            try:
                data_publicacao_iso = pd.to_datetime(dados["date"], utc=True).isoformat()
            except Exception:
                data_publicacao_iso = dados["date"]

        keywords_busca = "; ".join(sorted(set(self.keyword_por_url.get(url, []))))

        if self.diagnostico and descricao_origem:
            self.logger.debug("Descrição obtida via '%s' em %s", descricao_origem, url)

        return VagaUnificada(
            platform=self.platform,
            jobUrl=url,
            jobTitle=dados["jobTitle"],
            jobDescription=dados["jobDescription"],
            jobDescriptionHTML=dados["jobDescriptionHTML"],
            companyName=dados["companyName"],
            companyLocation=", ".join(filter(None, [dados["cidade"], dados["uf"], dados["pais"]])) or None,
            companyUrl=dados["companyUrl"],
            companyRating=dados["companyRating"],
            date=data_publicacao_iso,
            validThrough=dados["validThrough"],
            employmentType=dados["employmentType"],
            jobLocationType=dados["jobLocationType"],
            baseSalary=dados["baseSalary"],
            descriptionSource=descricao_origem,
            datePostedSource=data_publicacao_origem,
            validThroughSource=data_validade_origem,
            possibleBotBlock=possivel_bloqueio,
            cidade=dados["cidade"],
            uf=dados["uf"],
            pais=dados["pais"],
            keywordsBusca=keywords_busca,
            keywordsDetectadas="; ".join(keywords_detectadas),
            dataColeta=datetime.now().isoformat(),
        )


# ================================================================================
# INFOJOBS
# ================================================================================

# [REVISÃO 7] A InfoJobs mostra a data de publicação do anúncio como texto
# relativo no cabeçalho (ex.: "Hoje", "Ontem", "Anteontem", "N dias atrás"),
# não como um atributo/JSON com data absoluta — por isso precisa de um
# parser dedicado, parecido em espírito com o fallback de data por extenso
# da Gupy (_gupy_extrair_data_publicada_do_texto), mas com um vocabulário
# de rótulos completamente diferente.
_PADRAO_DIAS_ATRAS_INFOJOBS = re.compile(r"(\d+)\s+dias?\s+atr[aá]s", re.IGNORECASE)


def _infojobs_parse_data_relativa(texto: str) -> Optional[str]:
    """Converte o rótulo de data relativa do cabeçalho de um anúncio da
    InfoJobs ("Hoje", "Ontem", "Anteontem", "N dias atrás") para uma data
    ISO (AAAA-MM-DD), usando a data local de execução do scraper como
    referência — é só uma aproximação (o próprio rótulo já é aproximado,
    não há como recuperar o horário exato a partir dele). Se o texto vier
    num formato de data absoluta (a InfoJobs usa isso para anúncios mais
    antigos, ex.: "05/09/2026"), tenta o parse direto via pandas antes de
    desistir. Retorna None se não reconhecer nada."""
    if not texto:
        return None
    texto_norm = normalizar(texto)
    hoje = datetime.now().date()
    if texto_norm == "hoje":
        data = hoje
    elif texto_norm == "ontem":
        data = hoje - timedelta(days=1)
    elif texto_norm == "anteontem":
        data = hoje - timedelta(days=2)
    else:
        match = _PADRAO_DIAS_ATRAS_INFOJOBS.search(texto)
        if match:
            data = hoje - timedelta(days=int(match.group(1)))
        else:
            try:
                data = pd.to_datetime(texto, dayfirst=True, errors="raise").date()
            except Exception:
                return None
    return data.isoformat()


class InfoJobsScraper(BaseScraper):

    platform = "infojobs"
    # AJUSTE AQUI SE O SITE MUDAR
    BASE_URL_BUSCA = "https://www.infojobs.com.br/empregos.aspx"

    # AJUSTE AQUI SE O SITE MUDAR: padrão de URL de um anúncio INDIVIDUAL
    # da InfoJobs. Sempre singular ("vaga-de-", não "vagas-de-") e sempre
    # termina com "__<ID numérico>.aspx" (ex.:
    # ".../vaga-de-analista-desenvolvimento-em-sao-paulo__11989398.aspx").
    # As páginas de LISTAGEM/categoria usam o plural "vagas-de-" e NÃO têm
    # esse ID no final (ex.: ".../vagas-de-analista-desenvolvimento.aspx")
    # — aceitar "vagas-de-" também (como a versão anterior fazia) coletava
    # essas páginas de listagem como se fossem vagas de verdade, o que é a
    # causa raiz de descrições vindas erradas/truncadas para a InfoJobs.
    PADRAO_URL_VAGA = re.compile(r"/vaga-de-[\w-]+__\d+\.aspx", re.IGNORECASE)

    # Localização (ex.: "São Paulo - SP") no formato "Cidade - UF".
    _PADRAO_LOCALIDADE = re.compile(r"^[A-Za-zÀ-ÿ' .-]+ - [A-Z]{2}$")

    # [REVISÃO 7] AJUSTE AQUI SE O SITE MUDAR: link para a página da
    # empresa no cabeçalho do anúncio, usado como fallback de nome/URL da
    # empresa para os casos (como o HTML de referência desta revisão) em
    # que não existe logo — a extração via `alt="Por dentro da empresa..."`
    # abaixo só funciona quando a empresa tem logo cadastrada.
    _PADRAO_LINK_EMPRESA = re.compile(r"/empresa-[\w-]+__\d+\.aspx", re.IGNORECASE)

    def buscar_urls(self, palavra_chave: str, max_paginas: int) -> set[str]:
        urls = set()
        for pagina in range(1, max_paginas + 1):
            params = {"palabra": palavra_chave, "page": pagina}
            resposta = self.session.get(
                self.BASE_URL_BUSCA, params=params, headers=cabecalhos_aleatorios(), timeout=25
            )
            if resposta.status_code != 200:
                break
            soup = BeautifulSoup(resposta.text, "html.parser")
            if parece_bloqueio(soup.get_text(" ", strip=True)[:3000]):
                self.logger.warning("Possível bloqueio anti-bot no InfoJobs (palavra=%s, pagina=%d)", palavra_chave, pagina)
                if self.diagnostico:
                    salvar_dump_diagnostico(self.platform, palavra_chave, resposta.text)
                break

            encontrados_via_ld = extrair_urls_de_itemlist_ld(soup, resposta.url)
            urls |= encontrados_via_ld
            encontrados = len(encontrados_via_ld)
            for link in soup.find_all("a", href=True):
                href = link["href"]
                # AJUSTE AQUI SE O SITE MUDAR: padrão de link de vaga do
                # InfoJobs — ver comentário em PADRAO_URL_VAGA acima sobre
                # por que só o padrão singular+ID é aceito.
                if self.PADRAO_URL_VAGA.search(href):
                    urls.add(urljoin("https://www.infojobs.com.br", href.split("?")[0]))
                    encontrados += 1

            if encontrados == 0:
                if self.diagnostico:
                    salvar_dump_diagnostico(self.platform, palavra_chave, resposta.text)
                break
            time.sleep(random.uniform(self.delay_min, self.delay_max))
        return urls

    def extrair_vaga(self, url: str) -> Optional[VagaUnificada]:
        resposta = requisitar_com_retry(self.session, url, logger=self.logger)
        if resposta is None:
            return None
        soup = BeautifulSoup(resposta.text, "html.parser")
        if parece_bloqueio(soup.get_text(" ", strip=True)[:3000]):
            self.logger.warning("Possível bloqueio anti-bot em %s", url)
            return None

        vaga = self._extrair_via_jsonld(url, soup)

        # O JSON-LD do InfoJobs, quando existe, costuma trazer só um
        # resumo curto do anúncio — não o corpo completo, que só existe
        # nesta estrutura de página. Por isso o parser específico abaixo
        # roda SEMPRE (mesmo quando o JSON-LD foi encontrado), e ficamos
        # com a descrição mais completa entre as duas fontes, em vez de
        # simplesmente usar a primeira que aparecer.
        dados_pagina = self._extrair_estrutura_infojobs(soup)

        if vaga is None:
            if not dados_pagina.get("jobTitle"):
                return None
            vaga = VagaUnificada(platform=self.platform, jobUrl=url)

        if dados_pagina.get("jobTitle"):
            vaga.jobTitle = dados_pagina["jobTitle"]

        descricao_pagina = dados_pagina.get("jobDescription")
        if descricao_pagina and (
            not vaga.jobDescription or len(descricao_pagina) > len(vaga.jobDescription)
        ):
            veio_so_do_json_ld = bool(vaga.jobDescription) and vaga.descriptionSource == "json-ld"
            vaga.jobDescription = descricao_pagina
            # [REVISÃO 6] Registra a origem real da descrição: se o corpo
            # completo veio deste parser específico (e não só o resumo do
            # JSON-LD), marcamos "estrutura-pagina"; se o JSON-LD já tinha
            # contribuído com algo (raramente é o caso, já que aqui a
            # versão da página é sempre mais longa quando difere), fica
            # registrado como combinação das duas fontes.
            vaga.descriptionSource = (
                "json-ld+estrutura-pagina" if veio_so_do_json_ld else "estrutura-pagina"
            )

        if dados_pagina.get("companyName") and not vaga.companyName:
            vaga.companyName = dados_pagina["companyName"]
        # [REVISÃO 7] companyUrl é uma coluna do schema unificado, mas
        # nada na InfoJobs a preenchia até agora — vem do link para a
        # página da empresa no cabeçalho do anúncio.
        if dados_pagina.get("companyUrl") and not vaga.companyUrl:
            vaga.companyUrl = dados_pagina["companyUrl"]
        if dados_pagina.get("companyLocation") and not vaga.companyLocation:
            vaga.companyLocation = dados_pagina["companyLocation"]
        if dados_pagina.get("employmentType") and not vaga.employmentType:
            vaga.employmentType = dados_pagina["employmentType"]
        if dados_pagina.get("baseSalary") and not vaga.baseSalary:
            vaga.baseSalary = dados_pagina["baseSalary"]
        # [REVISÃO 7] jobLocationType: a InfoJobs mostra a modalidade
        # (Presencial/Home Office/Híbrido) de forma estruturada no
        # cabeçalho — mais confiável do que a heurística de texto livre
        # (`inferir_jobLocationType`) que o BaseScraper.rodar só
        # aplicaria depois, e só se este campo continuasse vazio.
        if dados_pagina.get("jobLocationType") and not vaga.jobLocationType:
            vaga.jobLocationType = dados_pagina["jobLocationType"]
        # [REVISÃO 7] date: a InfoJobs não expõe data absoluta em nenhum
        # atributo/JSON acessível para todo anúncio — só o rótulo relativo
        # "Hoje"/"Ontem"/"N dias atrás" no cabeçalho. Só usamos esse valor
        # quando nada mais confiável (JSON-LD) já preencheu `date`.
        if dados_pagina.get("date") and not vaga.date:
            vaga.date = dados_pagina["date"]
            vaga.datePostedSource = dados_pagina.get("datePostedSource") or "texto-relativo-pagina"

        return vaga

    def _extrair_estrutura_infojobs(self, soup: BeautifulSoup) -> dict:
        """Extrai campos direto da estrutura HTML de detalhe de vaga do
        InfoJobs (div#vacancylistDetail), escrita a partir de um HTML de
        anúncio real.

        Substitui o fallback antigo, que pegava soup.get_text() da PÁGINA
        INTEIRA (menu, rodapé, vagas relacionadas etc.) cortado nos
        primeiros 5000 caracteres — o que tanto misturava lixo quanto
        podia truncar a descrição real antes mesmo dela aparecer.

        [REVERTIDO — REVISÃO 8] As seções "Exigências"/"Valorizado"
        voltam a ser apenas ANEXADAS ao final de `jobDescription` como
        texto (não geram mais colunas próprias no schema unificado), para
        não duplicar a mesma informação em dois lugares diferentes do
        dataset.
        """
        dados: dict = {}
        painel = soup.find(id="vacancylistDetail") or soup

        # ---- título ----
        # AJUSTE AQUI SE O SITE MUDAR: o título vem como <h2 class="...
        # js_vacancyHeaderTitle">, não <h1> — por isso o fallback antigo
        # (que só tentava <h1>) não encontrava título nenhum aqui.
        titulo_tag = (
            painel.select_one("h2.js_vacancyHeaderTitle")
            or painel.find("h1")
            or painel.find("h2")
        )
        if titulo_tag:
            dados["jobTitle"] = titulo_tag.get_text(" ", strip=True)

        # ---- descrição completa ----
        # AJUSTE AQUI SE O SITE MUDAR: o corpo do anúncio é o único <p>
        # com a classe "white-space-pre-line" dentro do painel da vaga;
        # os outros <p> do mesmo painel (Número de vagas, Tipo de
        # contrato, Área Profissional) não têm essa classe.
        partes_descricao = []
        texto_descricao_principal = None
        descricao_tag = painel.select_one("p.white-space-pre-line")
        if descricao_tag:
            # trabalha numa cópia isolada para poder trocar <br> por "\n"
            # sem mexer no soup original.
            descricao_copia = BeautifulSoup(str(descricao_tag), "html.parser").p
            for br in descricao_copia.find_all("br"):
                br.replace_with("\n")
            texto_descricao_principal = descricao_copia.get_text().strip()
            if texto_descricao_principal:
                partes_descricao.append(texto_descricao_principal)

        # Campos complementares no formato "<span class='font-weight-
        # bold'>Rótulo:</span> valor" (Número de vagas, Tipo de contrato
        # e Jornada, Área Profissional) — ficam de fora de qualquer
        # JSON-LD genérico, então são anexados ao final da descrição para
        # não perder a informação. "Tipo de contrato e Jornada" também
        # alimenta o campo employmentType do schema unificado.
        for p in painel.find_all("p"):
            rotulo_tag = p.find("span", class_="font-weight-bold")
            if not rotulo_tag:
                continue
            texto_p = p.get_text(" ", strip=True)
            if texto_descricao_principal and texto_p == texto_descricao_principal:
                continue
            partes_descricao.append(texto_p)
            if rotulo_tag.get_text(strip=True).lower().startswith("tipo de contrato"):
                dados["employmentType"] = texto_p.split(":", 1)[-1].strip()

        # Exigências e Valorizado (listas de requisitos), quando
        # presentes. AJUSTE AQUI SE O SITE MUDAR: as duas seções têm a
        # mesma estrutura na InfoJobs — um cabeçalho com o rótulo exato,
        # seguido da próxima <ul class="custom-list"> no documento. O
        # schema unificado não tem colunas próprias para essas seções
        # (ver item 10 do changelog no topo do arquivo), então elas só
        # são anexadas ao final de `jobDescription`, como texto, junto
        # com o resto do anúncio — evitando guardar a mesma informação em
        # dois lugares diferentes do dataset.
        for rotulo_secao in ("Exigências", "Valorizado"):
            bloco_secao = self._extrair_bloco_secao_infojobs(painel, rotulo_secao)
            if bloco_secao:
                partes_descricao.append(bloco_secao)

        if partes_descricao:
            dados["jobDescription"] = "\n\n".join(partes_descricao)

        # ---- data de publicação (rótulo relativo no cabeçalho) ----
        # [REVISÃO 7] AJUSTE AQUI SE O SITE MUDAR: o rótulo ("Hoje",
        # "Ontem", "Anteontem", "N dias atrás") fica num
        # <div class="caption ..."> no cabeçalho do anúncio, ao lado dos
        # botões de candidatar-se. É a única fonte de data de publicação
        # disponível para a InfoJobs (não há JSON-LD/atributo com data
        # absoluta para todo anúncio).
        data_tag = painel.select_one("div.caption")
        if data_tag:
            data_iso = _infojobs_parse_data_relativa(data_tag.get_text(" ", strip=True))
            if data_iso:
                dados["date"] = data_iso
                dados["datePostedSource"] = "texto-relativo-pagina"

        # ---- empresa ----
        # AJUSTE AQUI SE O SITE MUDAR: o nome da empresa aparece quebrado
        # em spans aninhados no cabeçalho ("Gi" + <span>Group</span>), o
        # que é frágil de reconstruir por texto. O atributo alt da logo
        # ("Por dentro da empresa {Nome} Logo") é uma fonte mais estável.
        logo_tag = soup.find("img", alt=re.compile(r"^Por dentro da empresa .+ Logo$"))
        if logo_tag:
            nome = re.sub(r"^Por dentro da empresa\s+", "", logo_tag.get("alt", ""))
            nome = re.sub(r"\s+Logo$", "", nome).strip()
            if nome:
                dados["companyName"] = nome

        # [REVISÃO 7] Fallback quando a empresa não tem logo cadastrada
        # (caso comum — o HTML de referência desta revisão é assim): o
        # nome e a URL da empresa vêm do link "<div class="h4"><a
        # href="/empresa-...__<id>.aspx">Nome</a></div>" no cabeçalho.
        # AJUSTE AQUI SE O SITE MUDAR.
        if "companyName" not in dados or "companyUrl" not in dados:
            link_empresa = painel.find("a", href=self._PADRAO_LINK_EMPRESA)
            if link_empresa:
                if "companyName" not in dados:
                    nome_via_link = link_empresa.get_text(" ", strip=True)
                    nome_via_link = re.sub(r"\s+", " ", nome_via_link).strip()
                    if nome_via_link:
                        dados["companyName"] = nome_via_link
                if "companyUrl" not in dados:
                    href_empresa = link_empresa.get("href")
                    if href_empresa:
                        dados["companyUrl"] = urljoin("https://www.infojobs.com.br", href_empresa)

        # ---- modalidade de trabalho (Presencial/Home Office/Híbrido) ----
        # [REVISÃO 7] AJUSTE AQUI SE O SITE MUDAR: fica num
        # <div class="text-medium small font-weight-bold ..."> com um
        # ícone (icon-buildings para presencial, outros para remoto/
        # híbrido) antes do texto. Mapeamos o texto para os mesmos
        # rótulos usados pela heurística genérica (`inferir_jobLocationType`)
        # para manter os valores consistentes entre plataformas.
        modalidade_tag = painel.select_one("div.text-medium.small.font-weight-bold")
        if modalidade_tag:
            texto_modalidade = modalidade_tag.get_text(" ", strip=True)
            if texto_modalidade:
                tipo_mapeado = inferir_jobLocationType(None, None, texto_modalidade)
                if tipo_mapeado:
                    dados["jobLocationType"] = tipo_mapeado

        # ---- localização e salário ----
        # Ambos vivem em divs genéricas class="text-medium", sem classe
        # própria que os diferencie — por isso identificamos pelo formato
        # do texto ("Cidade - UF" / menciona salário). Olhamos só o texto
        # direto de cada div (ignorando tags filhas), porque o InfoJobs
        # injeta um span oculto de telemetria de distância dentro do
        # mesmo div da cidade, o que bagunçaria um get_text() normal.
        for div in painel.find_all("div", class_="text-medium"):
            texto_direto = self._texto_direto_sem_filhos(div)
            if not texto_direto:
                continue
            if "companyLocation" not in dados and self._PADRAO_LOCALIDADE.match(texto_direto):
                dados["companyLocation"] = texto_direto
            # [REVISÃO 7] Antes só reconhecia salário com valor explícito
            # ("R$ ..."); "Salário a combinar" (sem R$ nenhum, visto no
            # HTML de referência) ficava sem ser capturado.
            elif "baseSalary" not in dados and (
                "R$" in texto_direto or "salario" in normalizar(texto_direto)
            ):
                dados["baseSalary"] = texto_direto

        return dados

    @staticmethod
    def _extrair_bloco_secao_infojobs(painel, rotulo: str) -> Optional[str]:
        """[REVISÃO 7 — comportamento restaurado] Extrai a lista de itens
        (um por <li>) de uma seção do tipo "Exigências" / "Valorizado" do
        painel de detalhe da InfoJobs: localiza o texto do rótulo (fica
        numa <div class="h4 font-weight-bold ...">) e pega a próxima
        <ul class="custom-list">. Retorna um bloco de texto pronto para
        ser anexado a `jobDescription` (ex.: "Exigências:\\n- Escolaridade
        Mínima: Ensino Superior\\n- ..."), ou None se a seção não existir
        na página."""
        padrao_rotulo = re.compile(rf"^\s*{re.escape(rotulo)}\s*$", re.IGNORECASE)
        marcador = painel.find(string=padrao_rotulo)
        if not marcador:
            return None
        container = marcador.find_parent()
        lista = container.find_next("ul") if container else None
        if not lista:
            return None
        itens = [
            li.get_text(" ", strip=True)
            for li in lista.find_all("li")
            if li.get_text(strip=True)
        ]
        if not itens:
            return None
        return f"{rotulo}:\n" + "\n".join(f"- {item}" for item in itens)

    @staticmethod
    def _texto_direto_sem_filhos(tag) -> str:
        """Texto dos nós de texto FILHOS DIRETOS de `tag`, ignorando o
        conteúdo de tags aninhadas (ex.: o span oculto de distância)."""
        partes = tag.find_all(string=True, recursive=False)
        texto = " ".join(p.strip() for p in partes if p.strip())
        return re.sub(r"\s+", " ", texto).strip()


# ================================================================================
# CATHO
# ================================================================================

class CathoScraper(BaseScraper):

    platform = "catho"
    # AJUSTE AQUI SE O SITE MUDAR
    BASE_URL_BUSCA = "https://www.catho.com.br/vagas/{termo}/"

    # Localização no formato "N vaga(s) - Cidade" ou "N vaga(s) - Cidade, UF"
    # (ex.: "1 vaga - Brasilia" / "1 vaga - Barueri, São Paulo"). O "N vaga(s)"
    # precisa ser removido antes de guardar em companyLocation/cidade/uf.
    _PADRAO_VAGAS_PREFIXO = re.compile(r"^\d+\s+vagas?\s*-\s*", re.IGNORECASE)

    def buscar_urls(self, palavra_chave: str, max_paginas: int) -> set[str]:
        urls = set()
        termo_slug = quote(normalizar(palavra_chave).replace(" ", "-"))
        for pagina in range(1, max_paginas + 1):
            url_pagina = self.BASE_URL_BUSCA.format(termo=termo_slug)
            if pagina > 1:
                url_pagina += f"?page={pagina}"
            resposta = self.session.get(url_pagina, headers=cabecalhos_aleatorios(), timeout=25)
            if resposta.status_code != 200:
                break
            soup = BeautifulSoup(resposta.text, "html.parser")
            if parece_bloqueio(soup.get_text(" ", strip=True)[:3000]):
                self.logger.warning("Possível bloqueio anti-bot na Catho (palavra=%s, pagina=%d)", palavra_chave, pagina)
                if self.diagnostico:
                    salvar_dump_diagnostico(self.platform, palavra_chave, resposta.text)
                break

            # 1) Tenta primeiro o JSON-LD ItemList da própria listagem —
            #    mais estável do que caçar padrão de href.
            encontrados_via_ld = extrair_urls_de_itemlist_ld(soup, resposta.url)
            urls |= encontrados_via_ld

            # 2) Fallback: padrão de href real da Catho, confirmado via dump
            # de diagnóstico: "/vagas/{slug-do-titulo}/{id-numerico}", ex.:
            # "/vagas/pessoa-desenvolvedora-servicenow-senior-home-office/37070137"
            # Importante excluir os links de CATEGORIA (sem id no final,
            # tipo "/vagas/desenvolvedor/" ou "/vagas/desenvolvedor/?page=2"),
            # que são busca, não vaga específica.
            # AJUSTE AQUI SE O SITE MUDAR: padrão de link de vaga da Catho.
            encontrados = len(encontrados_via_ld)
            for link in soup.find_all("a", href=True):
                href = link["href"]
                if re.search(r"^/vagas/[\w.-]+/\d{4,}(?:[/?]|$)", href):
                    urls.add(urljoin("https://www.catho.com.br", href.split("?")[0]))
                    encontrados += 1

            if encontrados == 0:
                if self.diagnostico:
                    caminho = salvar_dump_diagnostico(self.platform, palavra_chave, resposta.text)
                    self.logger.info(
                        "0 links encontrados (HTTP 200) — dump salvo em %s. "
                        "Abra esse arquivo, procure um link real de vaga e "
                        "me envie o padrão do href para eu corrigir o "
                        "regex.", caminho,
                    )
                break
            time.sleep(random.uniform(self.delay_min, self.delay_max))
        return urls

    def extrair_vaga(self, url: str) -> Optional[VagaUnificada]:
        resposta = requisitar_com_retry(self.session, url, logger=self.logger)
        if resposta is None:
            return None
        soup = BeautifulSoup(resposta.text, "html.parser")
        if parece_bloqueio(soup.get_text(" ", strip=True)[:3000]):
            self.logger.warning("Possível bloqueio anti-bot em %s", url)
            return None

        vaga = self._extrair_via_jsonld(url, soup)

        # [REVISÃO 3] Assim como na InfoJobs, este parser específico da
        # estrutura de página da Catho roda SEMPRE (mesmo quando o
        # JSON-LD foi encontrado). Ele cobre 3 coisas que o JSON-LD da
        # Catho normalmente NÃO traz: "Tipo de contrato" (employmentType),
        # "Horário de trabalho" e "Benefícios" (anexados à descrição, já
        # que o schema unificado não tem colunas próprias para eles), e a
        # localização em texto livre ("N vaga(s) - Cidade[, UF]"), usada
        # para preencher companyLocation/cidade/uf quando o JSON-LD não
        # tem endereço estruturado.
        dados_pagina = self._extrair_estrutura_catho(soup)

        veio_so_do_json_ld = vaga is not None

        if vaga is None:
            if not dados_pagina.get("jobTitle"):
                return None
            vaga = VagaUnificada(platform=self.platform, jobUrl=url)

        if dados_pagina.get("jobTitle") and not vaga.jobTitle:
            vaga.jobTitle = dados_pagina["jobTitle"]

        # Descrição: começa da "Sobre a vaga" (JSON-LD ou fallback), e
        # sempre ANEXA (não substitui) Tipo de contrato / Horário de
        # trabalho / Benefícios / Sobre a empresa lidos da página, que
        # normalmente não vêm no JSON-LD.
        descricao_pagina_principal = dados_pagina.get("jobDescriptionPrincipal")
        # [REVISÃO 6] Registra se o corpo da descrição veio deste parser
        # de página (quando o JSON-LD não tinha nada) — antes disso
        # descriptionSource nunca era preenchido para a Catho.
        veio_do_parser_pagina = not vaga.jobDescription and bool(descricao_pagina_principal)
        descricao_base = vaga.jobDescription or descricao_pagina_principal or ""
        complementos = dados_pagina.get("complementosDescricao") or []
        if complementos:
            texto_complementos = "\n\n".join(complementos)
            if texto_complementos not in descricao_base:
                descricao_base = (descricao_base + "\n\n" + texto_complementos).strip() if descricao_base else texto_complementos
        if descricao_base:
            vaga.jobDescription = descricao_base

        if veio_do_parser_pagina:
            vaga.descriptionSource = "estrutura-pagina"
        elif complementos and veio_so_do_json_ld:
            # A descrição principal já veio do JSON-LD, mas o corpo final
            # ficou maior por causa dos complementos (tipo de contrato,
            # horário, benefícios) lidos da página.
            vaga.descriptionSource = "json-ld+estrutura-pagina"

        if dados_pagina.get("companyName") and not vaga.companyName:
            vaga.companyName = dados_pagina["companyName"]

        if dados_pagina.get("companyLocation") and not vaga.companyLocation:
            vaga.companyLocation = dados_pagina["companyLocation"]
        if dados_pagina.get("cidade") and not vaga.cidade:
            vaga.cidade = dados_pagina["cidade"]
        if dados_pagina.get("uf") and not vaga.uf:
            vaga.uf = dados_pagina["uf"]

        # employmentType: "Tipo de contrato" da página é mais confiável
        # e específico do que o que (raramente) vem no JSON-LD da Catho —
        # por isso, ao contrário dos outros campos, sobrescreve mesmo que
        # vaga.employmentType já tenha algo vindo do JSON-LD.
        if dados_pagina.get("employmentType"):
            vaga.employmentType = dados_pagina["employmentType"]

        if dados_pagina.get("baseSalary") and not vaga.baseSalary:
            vaga.baseSalary = dados_pagina["baseSalary"]

        return vaga

    def _extrair_estrutura_catho(self, soup: BeautifulSoup) -> dict:
        """Extrai campos direto da estrutura HTML de detalhe de vaga da
        Catho, escrita a partir de um HTML de anúncio real.

        AJUSTE AQUI SE O SITE MUDAR: todos os seletores abaixo dependem
        das classes atuais do template de detalhe da Catho
        (`data-detail-offer`, `.box-company`, `.text-16`, `.sub_box`).
        """
        dados: dict = {}
        painel = soup.find(attrs={"data-detail-offer": True}) or soup

        # ---- título ----
        titulo_tag = painel.find("h1")
        if titulo_tag:
            dados["jobTitle"] = titulo_tag.get_text(" ", strip=True)

        # ---- empresa ----
        # A caixa "box-company" tem o <h1> do título e, logo depois, um
        # <p> só com o nome da empresa (classe "text-neutral").
        empresa_tag = painel.select_one("div.box-company p")
        if empresa_tag:
            nome_empresa = empresa_tag.get_text(" ", strip=True)
            if nome_empresa:
                dados["companyName"] = nome_empresa

        # ---- localização ----
        # O <p> com o ícone "i_job_location" traz "N vaga(s) - Cidade" ou
        # "N vaga(s) - Cidade, UF". Precisamos remover o prefixo "N
        # vaga(s) - " (o "vagas" aqui é quantidade de posições abertas,
        # não parte da localização) antes de usar o resto como local.
        local_p = None
        for p in painel.find_all("p"):
            if p.find("span", class_="i_job_location"):
                local_p = p
                break
        if local_p:
            texto_local = local_p.get_text(" ", strip=True)
            texto_local = self._PADRAO_VAGAS_PREFIXO.sub("", texto_local).strip()
            if texto_local:
                dados["companyLocation"] = texto_local
                if "," in texto_local:
                    cidade, resto = texto_local.split(",", 1)
                    dados["cidade"] = cidade.strip()
                    resto = resto.strip()
                    # A Catho normalmente escreve o nome do estado por
                    # extenso (ex.: "São Paulo"), não a sigla — tentamos
                    # mapear para a sigla de 2 letras quando bate com
                    # ESTADOS_BR; senão guardamos o texto como veio.
                    resto_norm = normalizar(resto)
                    sigla_encontrada = next(
                        (sigla for sigla, nome_estado in ESTADOS_BR.items() if nome_estado == resto_norm),
                        None,
                    )
                    dados["uf"] = sigla_encontrada or resto
                else:
                    dados["cidade"] = texto_local

        # ---- descrição principal ("Sobre a vaga") ----
        # Usada só como valor de retorno auxiliar (jobDescriptionPrincipal)
        # para o caso de o JSON-LD genérico não ter sido encontrado —
        # extrair_vaga já usa self._extrair_via_jsonld como fonte
        # preferencial quando disponível.
        descricao_tag = painel.select_one("div.text-16 p.whitespace-pre-line")
        if descricao_tag:
            descricao_copia = BeautifulSoup(str(descricao_tag), "html.parser").p
            for br in descricao_copia.find_all("br"):
                br.replace_with("\n")
            texto_descricao = descricao_copia.get_text().strip()
            if texto_descricao:
                dados["jobDescriptionPrincipal"] = texto_descricao

        # ---- "Tipo de contrato" / "Horário de trabalho" ----
        # Aparecem como pares <p class="... font-bold ...">Rótulo</p>
        # seguido de <p>Valor</p>, dentro da mesma div "text-16" da
        # descrição. Iteramos todos os rótulos em negrito e pegamos o
        # <p> imediatamente seguinte como valor.
        complementos = []
        info_div = painel.find("div", class_="text-16")
        if info_div:
            for label_p in info_div.find_all("p", class_=lambda c: c and "font-bold" in c):
                rotulo = label_p.get_text(" ", strip=True)
                valor_p = label_p.find_next_sibling("p")
                if not valor_p:
                    continue
                valor = valor_p.get_text(" ", strip=True)
                if not valor:
                    continue
                rotulo_norm = normalizar(rotulo)
                if rotulo_norm.startswith("tipo de contrato"):
                    dados["employmentType"] = valor
                    complementos.append(f"Tipo de contrato: {valor}")
                elif rotulo_norm.startswith("horario de trabalho"):
                    complementos.append(f"Horário de trabalho: {valor}")

        # ---- Salário + Benefícios ----
        # Vivem numa div "sub_box" separada, identificada pelo <h2> que
        # contém "Salário". O valor do salário é o primeiro <p
        # class="text-18 font-bold"> logo após o <h2>; os benefícios
        # ficam na <ul> após o rótulo "Benefícios".
        for div in painel.find_all("div", class_="sub_box"):
            h2 = div.find("h2")
            if not h2 or "salario" not in normalizar(h2.get_text()):
                continue

            valor_salario_tag = h2.find_next_sibling("p")
            if valor_salario_tag:
                valor_salario = valor_salario_tag.get_text(" ", strip=True)
                if valor_salario:
                    dados["baseSalary"] = valor_salario

            lista_beneficios = div.find("ul")
            if lista_beneficios:
                itens_beneficios = [
                    li.get_text(" ", strip=True)
                    for li in lista_beneficios.find_all("li")
                    if li.get_text(strip=True)
                ]
                if itens_beneficios:
                    complementos.append(
                        "Benefícios:\n" + "\n".join(f"- {item}" for item in itens_beneficios)
                    )
            break

        if complementos:
            dados["complementosDescricao"] = complementos

        return dados


# ================================================================================
# EMPREGOS.COM.BR
# ================================================================================

class EmpregosScraper(BaseScraper):

    platform = "empregos"
    # AJUSTE AQUI SE O SITE MUDAR
    BASE_URL_BUSCA = "https://www.empregos.com.br/vagas/{termo}"

    def buscar_urls(self, palavra_chave: str, max_paginas: int) -> set[str]:
        urls = set()
        termo_slug = quote(normalizar(palavra_chave).replace(" ", "-"))
        for pagina in range(1, max_paginas + 1):
            url_pagina = self.BASE_URL_BUSCA.format(termo=termo_slug)
            if pagina > 1:
                url_pagina += f"/pagina-{pagina}"
            resposta = self.session.get(url_pagina, headers=cabecalhos_aleatorios(), timeout=25)
            if resposta.status_code != 200:
                break
            soup = BeautifulSoup(resposta.text, "html.parser")
            if parece_bloqueio(soup.get_text(" ", strip=True)[:3000]):
                self.logger.warning("Possível bloqueio anti-bot no Empregos.com.br (palavra=%s, pagina=%d)", palavra_chave, pagina)
                if self.diagnostico:
                    salvar_dump_diagnostico(self.platform, palavra_chave, resposta.text)
                break

            encontrados_via_ld = extrair_urls_de_itemlist_ld(soup, resposta.url)
            urls |= encontrados_via_ld
            encontrados = len(encontrados_via_ld)
            for link in soup.find_all("a", href=True):
                href = link["href"]
                # AJUSTE AQUI SE O SITE MUDAR: padrão de link de vaga do Empregos.com.br.
                if "/vaga/" in href:
                    urls.add(urljoin("https://www.empregos.com.br", href.split("?")[0]))
                    encontrados += 1

            if encontrados == 0:
                if self.diagnostico:
                    salvar_dump_diagnostico(self.platform, palavra_chave, resposta.text)
                break
            time.sleep(random.uniform(self.delay_min, self.delay_max))
        return urls

    def extrair_vaga(self, url: str) -> Optional[VagaUnificada]:
        resposta = requisitar_com_retry(self.session, url, logger=self.logger)
        if resposta is None:
            return None
        soup = BeautifulSoup(resposta.text, "html.parser")
        if parece_bloqueio(soup.get_text(" ", strip=True)[:3000]):
            self.logger.warning("Possível bloqueio anti-bot em %s", url)
            return None
        vaga = self._extrair_via_jsonld(url, soup)
        if vaga is None:
            titulo_tag = soup.find("h1")
            if not titulo_tag:
                return None
            vaga = VagaUnificada(
                platform=self.platform,
                jobUrl=url,
                jobTitle=titulo_tag.get_text(" ", strip=True),
                jobDescription=soup.get_text(" ", strip=True)[:5000],
                descriptionSource="fallback-pagina",
            )
        return vaga


# ================================================================================
# LINKEDIN — best effort, sem login (baixo volume, bloqueio mais provável)
# ================================================================================

class LinkedInScraper(BaseScraper):
    """
    O LinkedIn é de longe o alvo mais hostil à raspagem sem autenticação:
    a busca "guest" (sem login) devolve poucos resultados por página, some
    com frequência e pode redirecionar para tela de login a qualquer
    momento. Este scraper é deliberadamente mais lento (delay maior) e
    tolerante a falhas — trate os resultados como um bônus, não como fonte
    principal de volume.
    """

    platform = "linkedin"
    delay_min = 4.0
    delay_max = 8.0
    # AJUSTE AQUI SE O SITE MUDAR
    BASE_URL_BUSCA = "https://www.linkedin.com/jobs/search"
    RESULTADOS_POR_PAGINA = 25

    def buscar_urls(self, palavra_chave: str, max_paginas: int) -> set[str]:
        urls = set()
        for pagina in range(max_paginas):
            params = {
                "keywords": palavra_chave,
                "location": "Brazil",
                "start": pagina * self.RESULTADOS_POR_PAGINA,
            }
            resposta = self.session.get(
                self.BASE_URL_BUSCA, params=params, headers=cabecalhos_aleatorios(), timeout=25
            )
            if resposta.status_code != 200:
                self.logger.info("HTTP %s — LinkedIn provavelmente exigiu login/bloqueou", resposta.status_code)
                break
            soup = BeautifulSoup(resposta.text, "html.parser")
            if parece_bloqueio(soup.get_text(" ", strip=True)[:3000]) or "authwall" in resposta.url:
                self.logger.warning("Bloqueio/authwall do LinkedIn detectado — interrompendo esta palavra-chave")
                break

            encontrados = 0
            for link in soup.find_all("a", href=True):
                href = link["href"]
                # AJUSTE AQUI SE O SITE MUDAR: padrão de link de vaga do LinkedIn.
                if "/jobs/view/" in href:
                    urls.add(href.split("?")[0])
                    encontrados += 1

            if encontrados == 0:
                break
            time.sleep(random.uniform(self.delay_min, self.delay_max))
        return urls

    def extrair_vaga(self, url: str) -> Optional[VagaUnificada]:
        resposta = requisitar_com_retry(self.session, url, tentativas=2, logger=self.logger)
        if resposta is None:
            return None
        if "authwall" in resposta.url:
            self.logger.info("Redirecionado para authwall — pulando %s", url)
            return None
        soup = BeautifulSoup(resposta.text, "html.parser")
        vaga = self._extrair_via_jsonld(url, soup)
        if vaga is None:
            titulo_tag = soup.find("h1")
            if not titulo_tag:
                return None
            vaga = VagaUnificada(
                platform=self.platform,
                jobUrl=url,
                jobDescription=soup.get_text(" ", strip=True)[:5000],
                jobTitle=titulo_tag.get_text(" ", strip=True),
                descriptionSource="fallback-pagina",
            )
        return vaga


PLATAFORMAS_DISPONIVEIS = {
    "gupy": GupyScraper,
    "infojobs": InfoJobsScraper,
    "catho": CathoScraper,
    "empregos": EmpregosScraper,
    "linkedin": LinkedInScraper,
}

# Plataformas cujo scraper usa Selenium (Chrome real) em vez de `requests`
# puro — hoje só a Gupy (o Indeed, que também usava, foi removido do
# pipeline). Usado por `rodar_coleta` para saber quais scrapers aceitam o
# parâmetro `headless` e precisam de `fechar()` chamado no final (para não
# deixar processos de Chrome pendurados).
PLATAFORMAS_SELENIUM = {"gupy"}


# ================================================================================
# ADAPTADOR DOS CSVs "BONS" DA GUPY JÁ COLETADOS (opcional, não é mais o padrão)
# ================================================================================

def carregar_gupy_legado(caminhos: list[str]) -> pd.DataFrame:
    """Lê um ou mais CSVs já coletados no formato antigo da Gupy
    (gupy_vagas_dev_brasil_detalhadas.csv / _completo.csv) e converte para
    o schema unificado. Não faz nenhuma requisição de rede — só remapeia
    colunas já existentes.

    Este caminho deixou de ser o padrão: por decisão explícita, a Gupy
    agora roda sempre ao vivo, do zero. Esta função só é chamada se o
    usuário pedir explicitamente com --gupy-modo legado ou --gupy-modo
    ambos."""

    logger = get_logger("gupy-legado")
    dfs = []

    for caminho in caminhos:
        caminho_path = Path(caminho)
        if not caminho_path.exists():
            logger.warning("Arquivo não encontrado, pulando: %s", caminho)
            continue

        bruto = pd.read_csv(caminho_path, encoding="utf-8-sig")
        logger.info("Lido %s (%d linhas)", caminho_path.name, len(bruto))

        def pega(col, linha):
            valor = linha.get(col)
            if pd.isna(valor):
                return None
            valor = str(valor).strip()
            return valor if valor else None

        registros = []
        for _, linha in bruto.iterrows():
            url = pega("Link", linha) or pega("URL_Final", linha)
            if not url:
                continue

            titulo = pega("Vaga", linha)

            # Preferir descrição em texto simples já processada; cair para
            # a versão bruta (Descricao) só se necessário.
            descricao = (
                pega("Descricao_Texto", linha)
                or pega("Pagina_Completa_Texto", linha)
                or html_para_texto(pega("Descricao", linha))
                or None
            )

            empresa = pega("Empresa_Detalhada", linha) or pega("Empresa", linha)

            cidade = pega("Cidade_Detalhada", linha) or pega("Cidade", linha)
            uf = pega("UF_Detalhada", linha) or pega("UF", linha)
            pais = pega("Pais_Detalhado", linha) or pega("Pais", linha)
            localizacao = ", ".join(filter(None, [cidade, uf, pais])) or pega("Localizacao_Tipo", linha)

            data = (
                parse_data(pega("Data_Publicacao_Detalhada", linha))
                or parse_data(pega("Data_Publicacao", linha))
                or parse_data(pega("Data_Publicacao_Origem", linha))
            )

            registros.append(VagaUnificada(
                platform="gupy",
                jobUrl=url,
                jobTitle=titulo,
                jobDescription=descricao,
                companyName=empresa,
                companyLocation=localizacao,
                companyRating=None,   # a Gupy não expõe avaliação de empresa no JobPosting
                companyUrl=None,      # não coletado no formato antigo
                date=data,
                validThrough=parse_data(pega("Data_Validade", linha)),
                employmentType=pega("Tipo_Vaga", linha),
                jobLocationType=pega("Localizacao_Tipo", linha),
                baseSalary=pega("Salario", linha),
                descriptionSource=pega("Descricao_Origem", linha),
                datePostedSource=pega("Data_Publicacao_Origem", linha),
                validThroughSource=pega("Data_Validade_Origem", linha),
                possibleBotBlock=(str(pega("Possivel_Bloqueio", linha)).lower() == "true")
                    if pega("Possivel_Bloqueio", linha) is not None else None,
                cidade=cidade,
                uf=uf,
                pais=pais,
                keywordsBusca=pega("Keywords_Busca", linha),
                keywordsDetectadas=pega("Keywords_Detectadas", linha),
                dataColeta=pega("Data_Aprofundamento", linha) or pega("Data_Coleta", linha),
            ).to_dict())

        dfs.append(pd.DataFrame(registros, columns=COLUNAS_UNIFICADAS))

    if not dfs:
        return pd.DataFrame(columns=COLUNAS_UNIFICADAS)

    df_final = pd.concat(dfs, ignore_index=True)
    df_final = df_final.drop_duplicates(subset=["jobUrl"], keep="first")
    logger.info("Total após deduplicar legado da Gupy: %d vagas", len(df_final))
    return df_final


# ================================================================================
# RELATÓRIO DE QUALIDADE DOS DADOS (código 3 — completar_datas_e_relatorio.py)
# ================================================================================
#
# Porte da Parte 2 de completar_datas_e_relatorio.py, adaptado às colunas
# do schema unificado (jobDescription, date, validThrough, companyName,
# employmentType, jobLocationType, uf, pais, possibleBotBlock, ...) em vez
# das colunas específicas do CSV antigo da Gupy (Descricao_Texto,
# Data_Publicacao_Detalhada, Empresa_Detalhada, Tipo_Vaga, ...). A "Parte 1"
# (completar datas ausentes a partir do texto por extenso) não precisa de
# um passo separado aqui: já acontece dentro de GupyScraper.extrair_vaga,
# vaga por vaga, no momento da coleta.
# ================================================================================

def gerar_relatorio_qualidade(
    df: pd.DataFrame,
    plataforma_rotulo: str = "dados coletados",
    max_por_plataforma: Optional[int] = None,
) -> str:

    linhas_relatorio: list[str] = []

    def add(texto: str = ""):
        linhas_relatorio.append(texto)

    total = len(df)

    add("# Relatório de Qualidade dos Dados")
    add()
    add(f"Fonte: **{plataforma_rotulo}**")
    add(f"Total de registros: **{total}**")
    add(f"Gerado em: {datetime.now().isoformat(timespec='seconds')}")
    # [REVISÃO 6] Deixa explícito quando a coleta foi limitada por
    # --max-por-plataforma (comum em testes/diagnóstico), para quem lê o
    # relatório não interpretar uma amostra pequena de propósito como se
    # fosse o volume real disponível nas plataformas.
    if max_por_plataforma:
        add(
            f"⚠️ Coleta limitada por `--max-por-plataforma {max_por_plataforma}`: "
            "os números abaixo refletem uma amostra de teste, não o volume "
            "real de vagas disponíveis nas plataformas coletadas."
        )
    add()

    if total == 0:
        add("Nenhum registro para analisar.")
        return "\n".join(linhas_relatorio)

    # ------------------------------------------------------------------
    # 1. DADOS AUSENTES
    # ------------------------------------------------------------------

    add("## 1. Dados ausentes por coluna")
    add()

    for coluna in df.columns:
        vazios = (
            df[coluna].isna()
            | (df[coluna].astype(str).str.strip().isin(["", "None", "nan", "<NA>"]))
        ).sum()
        if vazios > 0:
            percentual = 100 * vazios / total
            add(f"- `{coluna}`: **{vazios}** ausentes ({percentual:.1f}%)")

    add()

    # ------------------------------------------------------------------
    # 2. ORIGEM DOS DADOS (JSON-LD / __NEXT_DATA__ / fallback de texto)
    # ------------------------------------------------------------------

    if "descriptionSource" in df.columns:
        add("## 2. Origem da descrição")
        add()
        contagem = df["descriptionSource"].fillna("(vazio)").replace("", "(vazio)").value_counts()
        for origem, qtd in contagem.items():
            add(f"- {origem}: {qtd}")
        add()

    # ------------------------------------------------------------------
    # 3. INCONSISTÊNCIAS ESTRUTURAIS
    # ------------------------------------------------------------------

    add("## 3. Inconsistências")
    add()

    inconsistencias_encontradas = False

    if "date" in df.columns and "validThrough" in df.columns:
        publicacao = pd.to_datetime(df["date"], errors="coerce", utc=True)
        validade = pd.to_datetime(df["validThrough"], errors="coerce", utc=True)
        invertidas = (validade < publicacao).sum()
        if invertidas > 0:
            inconsistencias_encontradas = True
        add(f"- Vagas com `validThrough` **anterior** a `date`: **{invertidas}**")

    if "companyName" in df.columns:
        sem_empresa = (
            df["companyName"].isna()
            | (df["companyName"].astype(str).str.strip() == "")
        ).sum()
        if sem_empresa > 0:
            inconsistencias_encontradas = True
        add(f"- Vagas sem `companyName` (possível falha de parsing ou bloqueio silencioso): **{sem_empresa}**")

    if "possibleBotBlock" in df.columns:
        bloqueios = df["possibleBotBlock"].fillna(False).astype(bool).sum()
        if bloqueios > 0:
            inconsistencias_encontradas = True
        add(f"- Linhas sinalizadas como possível bloqueio anti-bot: **{bloqueios}**")

    if not inconsistencias_encontradas:
        add("- Nenhuma inconsistência estrutural detectada pelas checagens acima.")

    add()

    # ------------------------------------------------------------------
    # 4. VALORES EXTREMOS
    # ------------------------------------------------------------------

    add("## 4. Valores extremos")
    add()

    if "jobDescription" in df.columns:
        tamanhos = df["jobDescription"].fillna("").astype(str).str.len()
        tamanhos_validos = tamanhos[tamanhos > 0]
        if len(tamanhos_validos) > 0:
            q1 = tamanhos_validos.quantile(0.25)
            q3 = tamanhos_validos.quantile(0.75)
            iqr = q3 - q1
            limite_baixo = q1 - 1.5 * iqr
            limite_alto = q3 + 1.5 * iqr
            muito_curtas = (tamanhos_validos < max(limite_baixo, 50)).sum()
            muito_longas = (tamanhos_validos > limite_alto).sum()
            add(f"- Descrições muito curtas (< {max(int(limite_baixo), 50)} caracteres): **{muito_curtas}**")
            add(f"- Descrições muito longas (outlier, > {int(limite_alto)} caracteres): **{muito_longas}**")
            add(f"- Tamanho mediano da descrição: **{int(tamanhos_validos.median())} caracteres**")

    if "date" in df.columns:
        pub = pd.to_datetime(df["date"], errors="coerce", utc=True)
        pub_valida = pub.dropna()
        if len(pub_valida) > 0:
            agora = pd.Timestamp.now(tz="UTC")
            futuras = (pub_valida > agora).sum()
            muito_antigas = (pub_valida < (agora - pd.Timedelta(days=365))).sum()
            add(f"- Vagas com data de publicação **no futuro** (provável erro de parsing): **{futuras}**")
            add(f"- Vagas com data de publicação com mais de 1 ano: **{muito_antigas}**")

    add()

    # ------------------------------------------------------------------
    # 5. CATEGORIAS POUCO REPRESENTADAS
    # ------------------------------------------------------------------

    add("## 5. Categorias pouco representadas")
    add()

    colunas_categoricas = [
        c for c in ["employmentType", "jobLocationType", "uf", "pais"]
        if c in df.columns
    ]

    for coluna in colunas_categoricas:
        contagem = (
            df[coluna].fillna("(vazio)").astype(str).str.strip().replace("", "(vazio)").value_counts()
        )
        limite = max(1, int(total * 0.01))
        raras = contagem[contagem <= limite]
        if len(raras) == 0:
            continue
        add(f"**{coluna}** — categorias com ≤ {limite} ocorrências (≤ 1% do total):")
        add()
        for categoria, qtd in raras.items():
            add(f"- {categoria}: {qtd}")
        add()

    if "companyName" in df.columns:
        empresas = df["companyName"].fillna("").astype(str).str.strip().replace("", pd.NA).dropna()
        empresas_unicas = empresas.nunique()
        empresas_uma_vaga = empresas.value_counts().eq(1).sum()
        add(
            f"- Empresas distintas no dataset: **{empresas_unicas}**, das quais "
            f"**{empresas_uma_vaga}** aparecem com apenas 1 vaga (cauda longa)."
        )

    add()

    # ------------------------------------------------------------------
    # 6. POSSÍVEIS LIMITAÇÕES DOS DADOS
    # ------------------------------------------------------------------

    add("## 6. Possíveis limitações dos dados")
    add()

    limitacoes = [
        "Coleta feita em um único momento no tempo (snapshot): vagas podem "
        "ser pausadas, encerradas ou reabertas pela empresa a qualquer "
        "momento sem que a coleta reflita isso.",

        "Extração de datas por texto (`fallback-pagina`/`texto-pagina`) é "
        "menos confiável que o JSON estruturado (`__NEXT_DATA__` ou "
        "JSON-LD): variações de layout, idioma da página (pt/en/es) ou "
        "mudanças futuras no site podem quebrar o regex silenciosamente.",

        "Possível viés de bloqueio anti-bot: se uma fração das vagas foi "
        "bloqueada (ver coluna `possibleBotBlock`), essas vagas ficam "
        "sub-representadas nas colunas de descrição/salário, o que pode "
        "distorcer análises de conteúdo.",

        "Campo `baseSalary` raramente preenchido: a maioria das empresas no "
        "Brasil não divulga faixa salarial publicamente, então qualquer "
        "análise salarial terá amostra pequena e não aleatória.",

        # [REVISÃO 6] Antes só citava a ausência do dado; agora deixa
        # claro que companyRating depende de --buscar-rating e de o
        # schema.org/Organization da empresa expor aggregateRating (algo
        # raro no mercado brasileiro), para não parecer um bug de coleta.
        "Campo `companyRating` quase sempre ausente: só é preenchido "
        "quando a execução usa `--buscar-rating` E a página institucional "
        "da empresa publica `aggregateRating` em schema.org/Organization "
        "— algo incomum no mercado brasileiro.",

        "Descrição/requisitos em texto livre: normalizar tecnologias, "
        "senioridade, modelo de trabalho ou requisitos específicos "
        "(escolaridade, idiomas, banco de dados etc.) a partir do texto "
        "de `jobDescription` exige regras adicionais além do que este "
        "relatório cobre — o schema unificado não tem colunas próprias "
        "para esses sub-campos, para não duplicar a mesma informação em "
        "dois lugares do dataset.",

        # [REVISÃO 6] cidade/uf, jobLocationType, keywordsBusca,
        # dataColeta e descriptionSource passaram a ser preenchidos por
        # heurísticas genéricas (regex/palavras-chave) para plataformas
        # que não têm parser dedicado desses campos — não têm a mesma
        # confiabilidade dos campos extraídos de dados estruturados
        # (JSON-LD/__NEXT_DATA__).
        "Alguns campos (`cidade`/`uf` fora da Catho/Gupy, `jobLocationType` "
        "fora da Gupy) são preenchidos por heurísticas genéricas de texto "
        "quando a plataforma não expõe o dado de forma estruturada — "
        "menos confiáveis do que os campos extraídos de JSON-LD/"
        "__NEXT_DATA__.",

        # [REVISÃO 9] Nota geral: colunas que só uma plataforma consegue
        # preencher de forma estruturada (ex.: datas relativas só a
        # InfoJobs expõe; "descriptionSource"/"jobLocationType" dependem
        # do que cada site publica) vão aparecer com percentuais altos de
        # ausência na seção 1 quando o dataset mistura várias plataformas
        # — isso não é, por si só, sinal de falha de coleta, e sim de que
        # aquele dado simplesmente não existe de forma estruturada nas
        # demais plataformas. Ao interpretar a seção 1, vale cruzar com a
        # coluna `platform` antes de concluir que há um problema.
        "Algumas colunas do schema unificado só podem ser preenchidas de "
        "forma estruturada por um subconjunto das plataformas (o dado "
        "simplesmente não existe, de forma acessível, nas demais) — isso "
        "aparece como percentual alto de ausência na seção 1 mesmo sem "
        "indicar falha de coleta. Vale sempre cruzar a ausência com a "
        "coluna `platform` antes de tratá-la como um problema.",
    ]

    if plataforma_rotulo == "gupy":
        limitacoes.insert(
            0,
            "Fonte única (Gupy): não representa vagas publicadas em outras "
            "plataformas, então o dataset reflete o viés de quais empresas "
            "usam a Gupy.",
        )

    for item in limitacoes:
        add(f"- {item}")

    add()

    return "\n".join(linhas_relatorio)


# ================================================================================
# ORQUESTRAÇÃO
# ================================================================================

def rodar_coleta(
    plataformas_novas: list[str],
    palavras_chave: list[str],
    max_paginas_por_palavra: int,
    max_vagas_por_plataforma: Optional[int],
    gupy_modo: str,
    caminhos_gupy_legado: list[str],
    buscar_rating: bool,
    gupy_headless: bool,
    diagnostico: bool = False,
) -> pd.DataFrame:

    logger = get_logger("orquestrador")
    partes: list[pd.DataFrame] = []

    # ---- Gupy: ao vivo por padrão; legado/ambos só se pedido explicitamente
    if gupy_modo in ("legado", "ambos"):
        partes.append(carregar_gupy_legado(caminhos_gupy_legado))

    if gupy_modo in ("live", "ambos"):
        scraper_gupy = GupyScraper(buscar_rating=buscar_rating, headless=gupy_headless, diagnostico=diagnostico)
        try:
            partes.append(
                scraper_gupy.rodar(palavras_chave, max_paginas_por_palavra, max_vagas_por_plataforma)
            )
        finally:
            scraper_gupy.fechar()

    # ---- demais plataformas ----------------------------------------------
    for nome_plataforma in plataformas_novas:
        if nome_plataforma == "gupy":
            continue  # já tratado acima
        classe_scraper = PLATAFORMAS_DISPONIVEIS.get(nome_plataforma)
        if classe_scraper is None:
            logger.warning("Plataforma desconhecida, ignorando: %s", nome_plataforma)
            continue

        kwargs_scraper = {"buscar_rating": buscar_rating, "diagnostico": diagnostico}
        usa_selenium = nome_plataforma in PLATAFORMAS_SELENIUM
        if usa_selenium:
            # Mesma flag que já controlava o headless da Gupy
            # (--sem-selenium-headless); serve para qualquer outra
            # plataforma que futuramente venha a usar Selenium.
            kwargs_scraper["headless"] = gupy_headless

        scraper = classe_scraper(**kwargs_scraper)
        try:
            partes.append(
                scraper.rodar(palavras_chave, max_paginas_por_palavra, max_vagas_por_plataforma)
            )
        except Exception as erro:
            logger.error("Falha geral na plataforma %s: %s", nome_plataforma, erro)
        finally:
            if usa_selenium:
                scraper.fechar()

    if not partes:
        return pd.DataFrame(columns=COLUNAS_UNIFICADAS)

    df = pd.concat(partes, ignore_index=True)
    df = df.drop_duplicates(subset=["jobUrl"], keep="first")

    # Ordena pela data mais recente quando possível.
    df["_data_ordenacao"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
    df = df.sort_values(by="_data_ordenacao", ascending=False, na_position="last")
    df = df.drop(columns=["_data_ordenacao"])

    return df


def imprimir_resumo(df: pd.DataFrame):
    logger = get_logger("resumo")
    logger.info("=" * 60)
    logger.info("RESUMO FINAL")
    logger.info("=" * 60)
    logger.info("Total de vagas no CSV unificado: %d", len(df))
    if df.empty:
        return
    logger.info("Vagas por plataforma:")
    for plataforma, quantidade in df["platform"].value_counts().items():
        logger.info("  %-10s %d", plataforma, quantidade)


# ================================================================================
# CLI
# ================================================================================

def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Coleta unificada de vagas de desenvolvimento (Gupy + 4 outras plataformas).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--plataformas",
        default="infojobs,catho,empregos,linkedin",
        help="Lista separada por vírgula das plataformas a RASPAR ao vivo "
             "(a Gupy é tratada à parte via --gupy-modo). Passe uma string "
             "vazia (\"\") para rodar somente a Gupy. "
             f"Opções: {', '.join(k for k in PLATAFORMAS_DISPONIVEIS if k != 'gupy')}",
    )
    parser.add_argument(
        "--gupy-modo",
        choices=["legado", "live", "ambos", "nenhum"],
        default="live",
        help="'live' (PADRÃO) raspa a Gupy do zero, ao vivo, via Selenium — "
             "não depende de nenhum CSV antigo; 'legado' importa CSVs já "
             "coletados anteriormente (uso opcional, ex.: reprocessar dados "
             "antigos); 'ambos' faz as duas coisas; 'nenhum' ignora a Gupy.",
    )
    parser.add_argument(
        "--gupy-legado",
        default=",".join(str(DADOS_BRUTOS / n) for n in (
            "gupy_vagas_dev_brasil_detalhadas_completo.csv",
            "gupy_vagas_dev_brasil_detalhadas.csv",
        )),
        help="Caminhos (separados por vírgula) dos CSVs antigos da Gupy a "
             "importar. Só é usado se --gupy-modo for 'legado' ou 'ambos'.",
    )
    parser.add_argument(
        "--palavras-chave",
        default=",".join(PALAVRAS_CHAVE_BUSCA),
        help="Lista separada por vírgula de termos de busca (default: os "
             "mesmos 55 termos do app.py original).",
    )
    parser.add_argument("--max-paginas", type=int, default=3, help="Máximo de páginas de resultado por palavra-chave.")
    parser.add_argument("--max-por-plataforma", type=int, default=None, help="Limite de vagas por plataforma (bom para testes).")
    parser.add_argument("--saida", default=str(DADOS_BRUTOS / "vagas_unificado.csv"), help="Caminho do CSV final.")
    parser.add_argument("--buscar-rating", action="store_true", help="Tenta buscar a avaliação da empresa (faz 1 requisição extra por vaga).")
    parser.add_argument("--sem-selenium-headless", action="store_true", help="Abre o Chrome com interface gráfica (útil para depurar a Gupy).")
    parser.add_argument("--diagnostico", action="store_true", help="Log em nível DEBUG, mais verboso, e salva HTML de páginas com 0 resultados em dados/bruto/diagnostico_html/.")
    parser.add_argument(
        "--acumular",
        action="store_true",
        help="Se o arquivo de --saida já existir, soma o resultado novo a "
             "ele (deduplicando por jobUrl) em vez de sobrescrever. Útil "
             "quando você testa uma plataforma de cada vez, em comandos "
             "separados, e quer ir juntando tudo no mesmo CSV.",
    )
    parser.add_argument(
        "--relatorio-qualidade",
        action="store_true",
        help="Gera também um relatório de qualidade dos dados em Markdown "
             "(porte de completar_datas_e_relatorio.py), por padrão sobre "
             "as vagas da Gupy. Use --relatorio-plataformas para escolher "
             "outra(s) plataforma(s) ou 'todas'.",
    )
    parser.add_argument(
        "--relatorio-plataformas",
        default="gupy",
        help="Plataforma (ou lista separada por vírgula, ou 'todas') sobre "
             "a qual gerar o --relatorio-qualidade.",
    )
    parser.add_argument(
        "--relatorio-saida",
        default=str(DADOS_BRUTOS / "relatorio_qualidade_dados.md"),
        help="Caminho do relatório de qualidade em Markdown, quando "
             "--relatorio-qualidade é usado.",
    )
    return parser


def main(argv=None):
    parser = construir_parser()
    args = parser.parse_args(argv)

    if args.diagnostico:
        logging.getLogger().setLevel(logging.DEBUG)

    plataformas_novas = [p.strip() for p in args.plataformas.split(",") if p.strip()]
    palavras_chave = [p.strip() for p in args.palavras_chave.split(",") if p.strip()]
    caminhos_gupy_legado = [c.strip() for c in args.gupy_legado.split(",") if c.strip()]

    df = rodar_coleta(
        plataformas_novas=plataformas_novas,
        palavras_chave=palavras_chave,
        max_paginas_por_palavra=args.max_paginas,
        max_vagas_por_plataforma=args.max_por_plataforma,
        gupy_modo=args.gupy_modo,
        caminhos_gupy_legado=caminhos_gupy_legado,
        buscar_rating=args.buscar_rating,
        gupy_headless=not args.sem_selenium_headless,
        diagnostico=args.diagnostico,
    )

    if args.acumular and Path(args.saida).exists():
        logger_main = get_logger("main")
        try:
            df_existente = pd.read_csv(args.saida, encoding="utf-8-sig")
            df = pd.concat([df_existente, df], ignore_index=True)
            df = df.drop_duplicates(subset=["jobUrl"], keep="first")
            logger_main.info("Acumulado com %s: total agora %d vagas", args.saida, len(df))
        except Exception as erro:
            logger_main.warning("Não consegui acumular com o CSV existente (%s) — vou sobrescrever.", erro)

    Path(args.saida).resolve().parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.saida, index=False, encoding="utf-8-sig")
    imprimir_resumo(df)
    get_logger("main").info("CSV salvo em: %s", Path(args.saida).resolve())

    if args.relatorio_qualidade:
        rotulo = args.relatorio_plataformas.strip().lower()
        if rotulo == "todas":
            df_relatorio = df
            rotulo_exibicao = "todas as plataformas"
        else:
            plataformas_relatorio = [p.strip() for p in rotulo.split(",") if p.strip()]
            df_relatorio = df[df["platform"].isin(plataformas_relatorio)]
            rotulo_exibicao = ", ".join(plataformas_relatorio) if len(plataformas_relatorio) > 1 else (plataformas_relatorio[0] if plataformas_relatorio else "dados coletados")

        relatorio = gerar_relatorio_qualidade(
            df_relatorio,
            plataforma_rotulo=rotulo_exibicao,
            max_por_plataforma=args.max_por_plataforma,
        )
        Path(args.relatorio_saida).write_text(relatorio, encoding="utf-8")
        get_logger("main").info("Relatório de qualidade salvo em: %s", Path(args.relatorio_saida).resolve())

if __name__ == "__main__":
    main()