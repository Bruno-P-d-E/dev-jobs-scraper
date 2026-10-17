# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Bruno Proença de Souza. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Etapa 10: matriz documento-termo com contagens brutas (Bag of Words)."""
import csv
from collections import Counter

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import (
    ARQUIVO_FREQUENCIA_TERMOS,
    ARQUIVO_LEMATIZADO,
    ARQUIVO_MATRIZ_FREQUENCIA,
    RELATORIO_BOW,
)
from comum.io_utils import ler_csv


def executar():
    _, linhas = ler_csv(ARQUIVO_LEMATIZADO)
    documentos = [(linha.get("tokens") or "").split() for linha in linhas]
    frequencia_global = Counter(token for tokens in documentos for token in tokens)
    frequencia_documentos = Counter(
        termo for tokens in documentos for termo in set(tokens)
    )
    vocabulario = sorted(frequencia_global)

    ARQUIVO_MATRIZ_FREQUENCIA.parent.mkdir(parents=True, exist_ok=True)
    with ARQUIVO_MATRIZ_FREQUENCIA.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["documento_id", *vocabulario])
        for indice, tokens in enumerate(documentos, start=1):
            contagens = Counter(tokens)
            escritor.writerow([indice, *(contagens[termo] for termo in vocabulario)])

    ARQUIVO_FREQUENCIA_TERMOS.parent.mkdir(parents=True, exist_ok=True)
    with ARQUIVO_FREQUENCIA_TERMOS.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["termo", "frequencia_total", "documentos_com_termo"])
        for termo, total in frequencia_global.most_common():
            escritor.writerow([termo, total, frequencia_documentos[termo]])

    total_tokens = sum(frequencia_global.values())
    total_termos_documento = sum(len(set(tokens)) for tokens in documentos)
    principais = frequencia_global.most_common(20)
    linhas_principais = "\n".join(
        f"| {termo} | {total} | {frequencia_documentos[termo]} |"
        for termo, total in principais
    )
    RELATORIO_BOW.parent.mkdir(parents=True, exist_ok=True)
    RELATORIO_BOW.write_text(
        "# Etapa 10 — matriz de frequência e Bag of Words\n\n"
        "A representação Bag of Words conta ocorrências de cada termo lematizado em cada vaga. "
        "Cada linha da matriz corresponde a um documento (`documento_id`, na ordem do CSV da etapa 7); "
        "cada coluna seguinte corresponde a um termo do vocabulário. Os valores são contagens inteiras "
        "brutas, sem ponderação TF-IDF e sem considerar a ordem das palavras.\n\n"
        f"- Documentos: **{len(documentos)}**\n"
        f"- Vocabulário: **{len(vocabulario)}** termos distintos\n"
        f"- Ocorrências totais: **{total_tokens}**\n"
        f"- Soma de frequências documento-termo: **{total_termos_documento}**\n"
        f"- Matriz CSV: `{ARQUIVO_MATRIZ_FREQUENCIA.name}`\n"
        f"- Frequências agregadas: `{ARQUIVO_FREQUENCIA_TERMOS.name}`\n\n"
        "## 20 termos mais frequentes\n\n"
        "| Termo | Ocorrências | Documentos com o termo |\n|---|---:|---:|\n"
        f"{linhas_principais}\n",
        encoding="utf-8",
    )
    print(f"Matriz BoW criada: {len(documentos)} documentos × {len(vocabulario)} termos")


if __name__ == "__main__":
    executar()
