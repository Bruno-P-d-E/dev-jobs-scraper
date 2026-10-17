# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Bruno Proença de Souza. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Etapa 15: coerência de tópicos, métricas disponíveis e planilha de validação humana."""
import csv
import math
from collections import Counter, defaultdict

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import (
    ARQUIVO_TOPICOS, ARQUIVO_LEMATIZADO, ARQUIVO_PREPARADO,
    ARQUIVO_ROTULOS_TOPICOS, ARQUIVO_CLUSTERS, ARQUIVO_LEXICO,
    ARQUIVO_METRICAS_VALIDACAO, ARQUIVO_AMOSTRA_REVISAO, RELATORIO_VALIDACAO,
)
from comum.io_utils import ler_csv


def ler_opcional(caminho):
    return ler_csv(caminho)[1] if caminho.exists() else []


def executar():
    _, linhas = ler_csv(ARQUIVO_LEMATIZADO)
    _, vagas = ler_csv(ARQUIVO_PREPARADO)
    if len(linhas) != len(vagas):
        raise ValueError("A base lematizada e a base preparada não têm o mesmo número de documentos.")
    documentos = [set((linha.get("tokens") or "").split()) for linha in linhas]
    # Conjunto de unigrams/bigrams observados para computar UMass também nos termos compostos do LDA.
    doc_termos = []
    for linha in linhas:
        toks = (linha.get("tokens") or "").split()
        doc_termos.append(set(toks) | {f"{a} {b}" for a, b in zip(toks, toks[1:])})
    df = Counter(term for termos in doc_termos for term in termos)

    topicos = ler_opcional(ARQUIVO_TOPICOS)
    por_topico = defaultdict(list)
    for linha in topicos:
        por_topico[linha["topico"]].append(linha["termo"])
    metricas = []
    coerencias = []
    for topico, termos in sorted(por_topico.items(), key=lambda x: int(x[0])):
        termos = termos[:10]
        pares = []
        for i in range(1, len(termos)):
            for j in range(i):
                denominador = df[termos[j]]
                if denominador:
                    coocorrencia = sum(termos[i] in d and termos[j] in d for d in doc_termos)
                    pares.append(math.log((coocorrencia + 1) / denominador))
        score = sum(pares) / len(pares) if pares else None
        coerencias.append(score) if score is not None else None
        metricas.append([f"umass_topico_{topico}", f"{score:.8f}" if score is not None else "", "média UMass dos 10 termos principais; maior (menos negativo) indica maior coocorrência"])
    if coerencias:
        metricas.append(["umass_media", f"{sum(coerencias)/len(coerencias):.8f}", "média dos tópicos; compare configurações com mesmos dados e pré-processamento"])

    for linha in ler_opcional(ARQUIVO_METRICAS_VALIDACAO):
        if linha.get("metrica") and not linha["metrica"].startswith(("precisao_lexico", "status_")):
            metricas.append([linha["metrica"], linha.get("valor", ""), linha.get("escopo", "")])

    # Amostra intencionalmente representativa: documentos mais próximos do perfil dominante.
    # A planilha nunca é sobrescrita após existir, para preservar anotações humanas.
    amostra = []
    usados = set()
    def adicionar(doc_id, fonte, grupo, confianca="", candidato=""):
        chave_amostra = (doc_id, fonte, grupo, candidato)
        if chave_amostra in usados or not (1 <= doc_id <= len(vagas)):
            return
        usados.add(chave_amostra)
        vaga = vagas[doc_id - 1]
        amostra.append([
            len(amostra) + 1, fonte, doc_id, grupo, confianca,
            vaga.get("platform", ""), vaga.get("jobTitle", ""),
            vaga.get("jobDescription_limpa", ""), candidato,
            "", "", "", "", "", "", "",
        ])

    distr = defaultdict(list)
    for linha in ler_opcional(ARQUIVO_ROTULOS_TOPICOS):
        distr[linha["topico_dominante"]].append((int(linha["documento_id"]), float(linha["probabilidade"])))
    for grupo, docs in distr.items():
        for doc_id, prob in sorted(docs, key=lambda x: (-x[1], x[0]))[:5]:
            adicionar(doc_id, "representante_topico", grupo, f"{prob:.5f}")

    clusters = defaultdict(list)
    for linha in ler_opcional(ARQUIVO_CLUSTERS):
        clusters[linha["cluster"]].append((int(linha["documento_id"]), float(linha.get("distancia_centroide") or "inf")))
    for grupo, docs in clusters.items():
        for doc_id, dist in sorted(docs, key=lambda x: (x[1], x[0]))[:5]:
            adicionar(doc_id, "representante_cluster", grupo, f"dist={dist:.5f}")

    # Revisão de precisão do léxico: amostra determinística de ocorrências detectadas.
    ocorrencias = ler_opcional(ARQUIVO_LEXICO)
    categorias = defaultdict(list)
    for linha in ocorrencias:
        categorias[linha["categoria"]].append(linha)
    for categoria, registros in categorias.items():
        vistos_categoria = set()
        for registro in registros:
            doc_id = int(registro["documento_id"])
            chave = (doc_id, registro["termo"])
            if chave not in vistos_categoria:
                adicionar(doc_id, f"auditoria_lexico_{categoria}", categoria, candidato=registro["termo"])
                vistos_categoria.add(chave)
            if len(vistos_categoria) >= 5:
                break

    # Amostra de documentos sem correspondência no léxico para procurar falsos negativos.
    docs_com_lexico = {int(linha["documento_id"]) for linha in ocorrencias}
    sem_lexico = [i for i in range(1, len(vagas) + 1) if i not in docs_com_lexico]
    for doc_id in sem_lexico[:10]:
        adicionar(doc_id, "auditoria_negativos_lexico", "sem_match_automatico")

    colunas_revisao = [
        "amostra_id", "estrato", "documento_id", "topico_ou_cluster", "score",
        "platform", "jobTitle", "texto_anuncio", "termo_candidato",
        "revisor_1_decisao_correto_incorreto", "revisor_1_codigo_aberto",
        "revisor_2_decisao_correto_incorreto", "revisor_2_codigo_aberto",
        "adjudicacao", "categoria_axial", "memo_revisor",
    ]
    if ARQUIVO_AMOSTRA_REVISAO.exists():
        colunas_existentes, anotacoes = ler_csv(ARQUIVO_AMOSTRA_REVISAO)
        aliases = {
            "decisao_revisor_correto_incorreto": "revisor_1_decisao_correto_incorreto",
            "codigo_aberto": "revisor_1_codigo_aberto",
        }
        colunas_saida = list(dict.fromkeys([
            *[c for c in colunas_existentes if c not in aliases], *colunas_revisao,
        ]))
        for anotacao in anotacoes:
            for antiga, nova in aliases.items():
                if anotacao.get(antiga) and not anotacao.get(nova):
                    anotacao[nova] = anotacao[antiga]
        chaves_existentes = {
            (r.get("estrato", ""), r.get("documento_id", ""), r.get("topico_ou_cluster", ""), r.get("termo_candidato", ""))
            for r in anotacoes
        }
        novas_linhas = []
        for valores in amostra:
            novo = dict(zip(colunas_revisao, valores))
            chave = (novo["estrato"], str(novo["documento_id"]), novo["topico_ou_cluster"], novo["termo_candidato"])
            if chave not in chaves_existentes:
                novo["amostra_id"] = str(len(anotacoes) + len(novas_linhas) + 1)
                novas_linhas.append(novo)
                chaves_existentes.add(chave)
        if any(coluna not in colunas_existentes for coluna in colunas_revisao) or any(a in colunas_existentes for a in aliases) or novas_linhas:
            # Evolui esquema/amostra mantendo valores que já foram anotados.
            with ARQUIVO_AMOSTRA_REVISAO.open("w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=colunas_saida, extrasaction="ignore")
                w.writeheader(); w.writerows([*anotacoes, *novas_linhas])
    else:
        with ARQUIVO_AMOSTRA_REVISAO.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(colunas_revisao)
            w.writerows(amostra)

    revisoes = ler_opcional(ARQUIVO_AMOSTRA_REVISAO)
    rotulos_validos = {"correto", "correta", "incorreto", "incorreta", "sim", "não", "nao"}
    adjudicados = []
    for registro in revisoes:
        if not registro.get("estrato", "").startswith("auditoria_lexico_"):
            continue
        decisao = (registro.get("adjudicacao") or "").strip().casefold()
        d1 = (registro.get("revisor_1_decisao_correto_incorreto") or "").strip().casefold()
        d2 = (registro.get("revisor_2_decisao_correto_incorreto") or "").strip().casefold()
        if not decisao and d1 == d2 and d1 in rotulos_validos:
            decisao = d1
        if decisao in rotulos_validos:
            adjudicados.append(decisao in {"correto", "correta", "sim"})
    if adjudicados:
        precisao = sum(adjudicados) / len(adjudicados)
        metricas.append(["precisao_lexico_amostra_revisada", f"{precisao:.8f}", f"{sum(adjudicados)} corretos em {len(adjudicados)} decisões; revisão independente ou adjudicação"])
    else:
        metricas.append(["status_precisao_lexico", "pendente", "preencha decisões de revisores/adjudicação na amostra humana"])
    if not topicos:
        metricas.append(["status_umass", "pendente", "execute a etapa 14 com --modelagem"])
    if not ARQUIVO_CLUSTERS.exists():
        metricas.append(["status_silhueta_kmeans", "pendente", "execute a etapa 14 com --modelagem"])

    with ARQUIVO_METRICAS_VALIDACAO.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["metrica", "valor", "escopo"]); w.writerows(metricas)

    status = []
    status.append(f"- Coerência UMass calculada para **{len(coerencias)} tópicos**." if coerencias else "- Coerência LDA: **pendente** (execute a etapa 14 com `--modelagem` para gerar os tópicos).")
    status.append(f"- Métricas e estados registrados: **{len(metricas)}** linhas em `{ARQUIVO_METRICAS_VALIDACAO.name}`.")
    status.append(f"- Planilha para revisão humana: `{ARQUIVO_AMOSTRA_REVISAO.name}` (**{len(amostra)}** registros na seleção desta execução; anotações existentes são preservadas).")
    RELATORIO_VALIDACAO.write_text(
        "# Etapa 15 — avaliação e validação\n\n"
        "## Métricas automatizadas\n\n"
        + "\n".join(status) + "\n\n"
        "UMass estima a coocorrência dos termos de maior peso no corpus; é uma medida interna e não determina sozinha o número ótimo de tópicos. Para selecioná-lo, compare uma grade de valores de K, coerência, estabilidade entre sementes e inspeção humana. Precisão/recall do léxico requerem decisões humanas em amostras de positivos e negativos; recall não pode ser estimado apenas revisando hits. Não há rótulos de referência para tópicos ou clusters, portanto não se reporta precisão/recall desses métodos.\n\n"
        "## Protocolo Human-in-the-Loop\n\n"
        "1. Dois avaliadores com conhecimento do domínio codificam independentemente a amostra estratificada da planilha. Para léxico, marcam o termo candidato como correto/incorreto e registram competências ausentes nos controles negativos. Para tópicos/clusters, descrevem o tema do anúncio e sua aderência ao grupo sugerido.\n"
        "2. Compare as decisões, registre divergências e resolva-as por discussão ou terceiro avaliador. Calcule precisão do léxico como acertos/(acertos+falsos positivos); reporte denominador e protocolo. Estime recall somente com uma amostra de negativos revisada de modo exaustivo e denominador documentado.\n"
        "3. Use codificação aberta e comparação constante para criar códigos, depois agrupe relações em categorias (codificação axial) e integre categorias centrais em memo. Revise categorias contra casos discrepantes e mantenha trilha de decisões. Só denomine o estudo Grounded Theory se a pergunta e o desenho realmente adotarem amostragem teórica, comparação constante e desenvolvimento de teoria; a revisão da amostra por si só não constitui Grounded Theory.\n"
        "4. Anote mudanças na planilha de revisão; execuções futuras preservam respostas e acrescentam apenas novos exemplos. Documente avaliadores, treinamento, divergências, códigos, amostra e saturação/limites.\n\n"
        "A seleção automatizada é intencional e voltada a exemplos representativos, não uma amostra probabilística para estimar prevalência. Não generalize frequências de anotação sem desenho amostral apropriado.\n",
        encoding="utf-8",
    )
    print(f"Validação preparada: {len(coerencias)} tópicos avaliados; amostra humana com {len(amostra)} documentos novos")


if __name__ == "__main__":
    executar()
