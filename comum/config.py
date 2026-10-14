# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 [NOME DO AUTOR]. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Configuração compartilhada do projeto (CRISP-DM). A base bruta fica somente para leitura.

Layout: uma pasta de código por fase (0_raspagem ... 6_implantacao) e uma
subpasta de saídas por fase em resultados/.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS_BRUTOS = RAIZ / "dados" / "bruto"
ARQUIVO_BRUTO = DADOS_BRUTOS / "vagas_unificado.csv"   # saída da fase 0_raspagem
FIGURAS = RAIZ / "figuras"

SAIDA = RAIZ / "resultados"
SAIDA_ENTENDIMENTO = SAIDA / "2_entendimento_dados"
SAIDA_PREPARACAO = SAIDA / "3_preparacao_dados"
SAIDA_MODELAGEM = SAIDA / "4_modelagem"
SAIDA_AVALIACAO = SAIDA / "5_avaliacao"
PASTAS_SAIDA = (SAIDA_ENTENDIMENTO, SAIDA_PREPARACAO, SAIDA_MODELAGEM, SAIDA_AVALIACAO)
ARQUIVO_HIGIENIZADO = SAIDA_PREPARACAO / "vagas_higienizadas.csv"
ARQUIVO_PREPARADO = SAIDA_PREPARACAO / "vagas_preparadas.csv"
ARQUIVO_TOKENIZADO = SAIDA_PREPARACAO / "vagas_tokenizadas.csv"
ARQUIVO_SEM_STOPWORDS = SAIDA_PREPARACAO / "vagas_sem_stopwords.csv"
ARQUIVO_LEMATIZADO = SAIDA_PREPARACAO / "vagas_lematizadas.csv"
ARQUIVO_MATRIZ_FREQUENCIA = SAIDA_PREPARACAO / "matriz_frequencia_bow.csv"
ARQUIVO_FREQUENCIA_TERMOS = SAIDA_PREPARACAO / "frequencia_termos_bow.csv"
ARQUIVO_TF_IDF = SAIDA_PREPARACAO / "matriz_tfidf_esparsa.csv"
ARQUIVO_EMBEDDINGS = SAIDA_PREPARACAO / "embeddings_sbert.csv"
ARQUIVO_SIMILARIDADES = SAIDA_PREPARACAO / "vizinhos_semanticos_sbert.csv"
ARQUIVO_NGRAMAS = SAIDA_MODELAGEM / "frequencia_ngramas.csv"
ARQUIVO_LEXICO = SAIDA_MODELAGEM / "ocorrencias_lexico_dominio.csv"
ARQUIVO_LEXICO_RESUMO = SAIDA_MODELAGEM / "resumo_lexico_dominio.csv"
ARQUIVO_REGEX = SAIDA_MODELAGEM / "extracoes_regex.csv"
ARQUIVO_TOPICOS = SAIDA_MODELAGEM / "topicos_lda.csv"
ARQUIVO_ROTULOS_TOPICOS = SAIDA_MODELAGEM / "documentos_topicos_lda.csv"
ARQUIVO_CLUSTERS = SAIDA_MODELAGEM / "documentos_clusters_kmeans.csv"
ARQUIVO_RESUMO_CLUSTERS = SAIDA_MODELAGEM / "resumo_clusters_kmeans.csv"
ARQUIVO_METRICAS_VALIDACAO = SAIDA_AVALIACAO / "metricas_modelos.csv"
ARQUIVO_AMOSTRA_REVISAO = SAIDA_AVALIACAO / "amostra_revisao_humana.csv"
ARQUIVO_MODALIDADE_CLASSIFICADA = SAIDA_MODELAGEM / "modalidade_classificada.csv"
RELATORIO_MODALIDADE = SAIDA_MODELAGEM / "16_modalidade_trabalho.md"
ARQUIVO_EXCLUIDOS = SAIDA_PREPARACAO / "vagas_excluidas_com_motivo.csv"
ARQUIVO_EXCLUIDOS_IDIOMA = SAIDA_PREPARACAO / "vagas_excluidas_filtro_idioma.csv"
ARQUIVO_TITULOS_SEM_TERMO = SAIDA_PREPARACAO / "titulos_sem_termo_profissao.csv"
ARQUIVO_DISTRIBUICAO_IDIOMA = SAIDA_PREPARACAO / "distribuicao_idioma.csv"
LOG_HIGIENIZACAO_CSV = SAIDA_PREPARACAO / "log_higienizacao.csv"
RELATORIO_ENTENDIMENTO = SAIDA_ENTENDIMENTO / "01_entendimento_dados.md"
RELATORIO_EXPLORACAO = SAIDA_ENTENDIMENTO / "02_exploracao_dados.md"
RELATORIO_HIGIENIZACAO = SAIDA_PREPARACAO / "03_higienizacao.md"
RELATORIO_PREPARACAO = SAIDA_PREPARACAO / "04_preparacao_dados.md"
RELATORIO_TOKENIZACAO = SAIDA_PREPARACAO / "05_tokenizacao.md"
RELATORIO_STOPWORDS = SAIDA_PREPARACAO / "06_remocao_stopwords.md"
RELATORIO_LEMATIZACAO = SAIDA_PREPARACAO / "07_lematizacao.md"
RELATORIO_BOW = SAIDA_PREPARACAO / "10_matriz_frequencia_bow.md"
RELATORIO_TF_IDF = SAIDA_PREPARACAO / "11_tfidf.md"
RELATORIO_EMBEDDINGS = SAIDA_PREPARACAO / "12_embeddings_sbert.md"
RELATORIO_MODELAGEM = SAIDA_MODELAGEM / "14_modelagem_topicos_clusters.md"
RELATORIO_ANALISE_TEXTUAL = SAIDA_MODELAGEM / "13_ngramas_lexico_regex.md"
RELATORIO_VALIDACAO = SAIDA_AVALIACAO / "15_avaliacao_validacao.md"
PLANO_MODELAGEM = SAIDA_MODELAGEM / "08_modelagem_pendente.md"
PLANO_AVALIACAO = SAIDA_AVALIACAO / "09_avaliacao_pendente.md"

COLUNA_TEXTO = "jobDescription"
COLUNA_TITULO = "jobTitle"
COLUNA_URL = "jobUrl"
COLUNAS_TEXTO_VAGA = (
    "jobTitle", "companyName", "companyLocation", "cidade", "uf", "pais",
    "employmentType", "jobLocationType", "jobDescription_limpa",
)
ENCODING = "utf-8-sig"

# Termos configuráveis para delimitar a profissão-alvo nos títulos.
TERMOS_PROFISSAO_TITULO = (
    "desenvolvedor", "desenvolvedora", "desenvolvedores", "desenvolvedoras",
    "developer", "developers", "dev",
    "programador", "programadora", "programadores", "programadoras",
    "programmer", "programmers",
    "engenheiro de software", "engenheira de software", "engenheiros de software",
    "engenheiras de software", "engenheiro(a) de software", "software engineer",
    "software engineers",
)

# Vocabulários usados pela detecção local e reproduzível do idioma principal.
# O método e os resultados por idioma são registrados pelo script de higienização.
MARCADORES_IDIOMA = {
    "português": {
        "voce", "seu", "sua", "seus", "suas", "estamos", "estao", "temos",
        "nossa", "nosso", "nossas", "nossos", "empresa", "equipe", "vaga",
        "vagas", "experiencia", "requisitos", "responsabilidades", "desejavel",
        "necessario", "necessaria", "formacao", "conhecimentos", "trabalhar",
        "oportunidade", "atuacao", "candidatura", "beneficios", "contratacao",
        "desenvolvimento", "projetos", "nao", "pela", "pelo", "nossa", "nosso",
        "precisamos", "conheca", "inscreva", "requisitos", "habilidades",
        "remuneracao", "beneficio", "brasileiro", "brasileira", "portugues",
    },
    "inglês": {
        "the", "and", "you", "your", "our", "we", "are", "will", "this",
        "they", "from", "experience", "requirements", "responsibilities", "role",
        "position", "skills", "preferred", "must", "should", "opportunity",
        "company", "apply", "working", "team", "with", "for", "have", "has",
        "who", "what", "their", "about", "join", "work", "years", "ability",
        "responsible", "responsibility", "benefits", "location", "employment",
    },
    "espanhol": {
        "esta", "estan", "buscamos", "experiencia", "requisitos", "responsabilidades",
        "trabajo", "empresa", "conocimientos", "deseable", "posicion", "postulacion",
        "habilidades", "oportunidad", "equipo", "busqueda", "postular", "requisitos",
        "seran", "tendra", "funciones", "desarrollar", "ofrecemos", "remuneracion",
    },
    "francês": {
        "vous", "nous", "notre", "votre", "avec", "poste", "experience", "equipe", "entreprise", "missions", "competences",
        "responsabilites", "recherche", "souhaite", "seront", "candidature",
    },
}


# Cria as pastas de saída de cada fase na primeira importação.
for _pasta in PASTAS_SAIDA:
    _pasta.mkdir(parents=True, exist_ok=True)
