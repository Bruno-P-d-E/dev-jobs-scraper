# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Bruno Proença de Souza. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Etapa 14 opcional: LDA em contagens e K-Means em TF-IDF."""
import csv
import math

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import (
    ARQUIVO_LEMATIZADO, ARQUIVO_PREPARADO, ARQUIVO_TOPICOS,
    ARQUIVO_ROTULOS_TOPICOS, ARQUIVO_CLUSTERS, ARQUIVO_RESUMO_CLUSTERS,
    ARQUIVO_METRICAS_VALIDACAO, RELATORIO_MODELAGEM, SAIDA,
)
from comum.io_utils import ler_csv

N_TOPICOS = 8
GRADE_TOPICOS = (4, 6, 8, 10, 12)
N_CLUSTERS = 8
SEMENTE = 42


def executar():
    try:
        from sklearn.cluster import KMeans
        from sklearn.decomposition import LatentDirichletAllocation
        from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
        from sklearn.metrics import silhouette_score
    except ImportError as erro:
        raise RuntimeError("Instale as dependências opcionais: python -m pip install -r requirements-modelagem.txt") from erro

    _, linhas = ler_csv(ARQUIVO_LEMATIZADO)
    _, vagas = ler_csv(ARQUIVO_PREPARADO)
    if len(linhas) != len(vagas):
        raise ValueError("As etapas 4 e 7 têm números diferentes de documentos.")
    textos = [linha.get("tokens") or "" for linha in linhas]
    if len(textos) < max(N_TOPICOS, N_CLUSTERS):
        raise ValueError("Há documentos insuficientes para o número configurado de tópicos/grupos.")
    SAIDA.mkdir(parents=True, exist_ok=True)

    # LDA é ajustado sobre contagens (não sobre TF-IDF).
    contagens = CountVectorizer(ngram_range=(1, 2), min_df=5, max_df=0.95)
    matriz_contagens = contagens.fit_transform(textos)
    nomes = contagens.get_feature_names_out()
    doc_sets = []
    for texto in textos:
        toks = texto.split()
        doc_sets.append(set(toks) | {f"{a} {b}" for a, b in zip(toks, toks[1:])})
    doc_freq = {}
    for doc_set in doc_sets:
        for termo in doc_set:
            doc_freq[termo] = doc_freq.get(termo, 0) + 1

    def umass(top_terms):
        scores = []
        for i in range(1, len(top_terms)):
            for j in range(i):
                denominador = doc_freq.get(top_terms[j], 0)
                if denominador:
                    cooc = sum(top_terms[i] in d and top_terms[j] in d for d in doc_sets)
                    scores.append(math.log((cooc + 1) / denominador))
        return sum(scores) / len(scores) if scores else 0.0

    lda = None
    dist = None
    scores_coerencia = []
    for k in GRADE_TOPICOS:
        modelo_k = LatentDirichletAllocation(n_components=k, random_state=SEMENTE, learning_method="batch", max_iter=20)
        modelo_k.fit(matriz_contagens)
        scores_k = [umass([nomes[i] for i in pesos.argsort()[-10:][::-1]]) for pesos in modelo_k.components_]
        score_medio = sum(scores_k) / len(scores_k)
        scores_coerencia.append((k, score_medio))
        if k == N_TOPICOS:
            lda = modelo_k
            dist = lda.transform(matriz_contagens)

    with ARQUIVO_METRICAS_VALIDACAO.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["metrica", "valor", "escopo"])
        for k, score in scores_coerencia:
            w.writerow([f"umass_media_k_{k}", f"{score:.8f}", "média por tópico dos 10 termos principais; maior/menos negativo indica mais coocorrência"])
    with ARQUIVO_TOPICOS.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["topico", "termo", "peso"])
        for t, pesos in enumerate(lda.components_, 1):
            for idx in pesos.argsort()[-15:][::-1]:
                w.writerow([t, nomes[idx], f"{pesos[idx]:.8f}"])
    with ARQUIVO_ROTULOS_TOPICOS.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["documento_id", "topico_dominante", "probabilidade"])
        for doc_id, distribuicao in enumerate(dist, 1):
            topico = int(distribuicao.argmax())
            w.writerow([doc_id, topico + 1, f"{distribuicao[topico]:.8f}"])

    # K-Means é um algoritmo de clustering; kNN é busca de vizinhos, não clustering.
    vetorizador = TfidfVectorizer(ngram_range=(1, 2), min_df=5, max_df=0.95, sublinear_tf=True)
    matriz_tfidf = vetorizador.fit_transform(textos)
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=SEMENTE, n_init=10)
    rotulos = kmeans.fit_predict(matriz_tfidf)
    silhueta = silhouette_score(
        matriz_tfidf, rotulos,
        sample_size=min(1000, len(textos)), random_state=SEMENTE, metric="cosine",
    )
    distancias = kmeans.transform(matriz_tfidf)
    termos = vetorizador.get_feature_names_out()
    tamanhos = [0] * N_CLUSTERS
    for rotulo in rotulos:
        tamanhos[int(rotulo)] += 1
    with ARQUIVO_CLUSTERS.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["documento_id", "platform", "jobTitle", "cluster", "distancia_centroide"])
        for i, (vaga, rotulo) in enumerate(zip(vagas, rotulos), 1):
            w.writerow([i, vaga.get("platform", ""), vaga.get("jobTitle", ""), int(rotulo) + 1, f"{distancias[i-1, int(rotulo)]:.8f}"])
    with ARQUIVO_RESUMO_CLUSTERS.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["cluster", "documentos", "termos_caracteristicos"])
        for c in range(N_CLUSTERS):
            pesos = kmeans.cluster_centers_[c]
            top = [termos[i] for i in pesos.argsort()[-12:][::-1]]
            w.writerow([c + 1, tamanhos[c], ", ".join(top)])

    with ARQUIVO_METRICAS_VALIDACAO.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["metrica", "valor", "escopo"])
        w.writerow(["silhueta_kmeans_cosseno", f"{silhueta:.8f}", f"amostra determinística de {min(1000, len(textos))} documentos" if len(textos) > 1000 else "corpus completo"])

    RELATORIO_MODELAGEM.write_text(
        "# Etapa 14 — modelagem exploratória: LDA e K-Means\n\n"
        f"Foram ajustados {N_TOPICOS} tópicos LDA sobre contagens de unigramas/bigramas (min_df=5, max_df=0,95) "
        f"e {N_CLUSTERS} grupos K-Means sobre TF-IDF (mesmos limites de frequência; sublinear_tf=True). "
        f"Semente aleatória: {SEMENTE}. Cada tópico tem 15 termos de maior peso; cada vaga recebe tópico dominante. "
        f"A coerência UMass foi comparada para K={', '.join(map(str, GRADE_TOPICOS))}; resultados em `{ARQUIVO_METRICAS_VALIDACAO.name}`. "
        "Os nomes dos tópicos/grupos são interpretações posteriores, não rótulos comprovados. O número de tópicos/grupos "
        "K=8 é a configuração exportada para inspeção; não é selecionada automaticamente. Compare coerência, "
        "estabilidade e inspeção humana. kNN não foi tratado como clustering: vizinhos semânticos estão na etapa SBERT opcional.\n\n"
        f"- LDA e distribuições por vaga: `{ARQUIVO_TOPICOS.name}`, `{ARQUIVO_ROTULOS_TOPICOS.name}`\n"
        f"- K-Means e resumo: `{ARQUIVO_CLUSTERS.name}`, `{ARQUIVO_RESUMO_CLUSTERS.name}`\n"
        f"- Silhueta K-Means (cosseno): **{silhueta:.4f}**; valor maior sugere grupos mais separados, mas não confirma utilidade substantiva.\n"
        f"- Vocabulários LDA/K-Means: {matriz_contagens.shape[1]} / {matriz_tfidf.shape[1]} atributos\n",
        encoding="utf-8",
    )
    print(f"LDA e K-Means concluídos: {len(textos)} documentos, {N_TOPICOS} tópicos, {N_CLUSTERS} clusters")


if __name__ == "__main__":
    executar()
