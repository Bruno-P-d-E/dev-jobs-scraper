# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Bruno Proença de Souza. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Etapa 11: ponderação TF-IDF esparsa calculada sem bibliotecas externas."""
import csv
import math
from collections import Counter

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import ARQUIVO_LEMATIZADO, ARQUIVO_TF_IDF, RELATORIO_TF_IDF
from comum.io_utils import ler_csv


def executar():
    _, linhas = ler_csv(ARQUIVO_LEMATIZADO)
    documentos = [(linha.get("tokens") or "").split() for linha in linhas]
    df = Counter(termo for tokens in documentos for termo in set(tokens))
    n_documentos = len(documentos)

    # IDF suavizado: evita pesos extremos e continua definido para todo termo observado.
    idf = {termo: math.log((1 + n_documentos) / (1 + n)) + 1
           for termo, n in df.items()}
    total_pesos = 0
    ARQUIVO_TF_IDF.parent.mkdir(parents=True, exist_ok=True)
    with ARQUIVO_TF_IDF.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["documento_id", "termo", "tf", "idf", "tfidf"])
        for doc_id, tokens in enumerate(documentos, start=1):
            contagens = Counter(tokens)
            for termo, frequencia in sorted(contagens.items()):
                peso = frequencia * idf[termo]
                escritor.writerow([doc_id, termo, frequencia, f"{idf[termo]:.8f}", f"{peso:.8f}"])
                total_pesos += 1

    RELATORIO_TF_IDF.parent.mkdir(parents=True, exist_ok=True)
    RELATORIO_TF_IDF.write_text(
        "# Etapa 11 — TF-IDF\n\n"
        "A matriz usa TF como contagem bruta do termo no documento e IDF suavizado "
        "`log((1 + N) / (1 + df)) + 1`, em que `N` é o número de vagas e `df` é o número "
        "de vagas que contêm o termo. O peso é `TF × IDF`; termos presentes em quase todas "
        "as vagas recebem menor peso relativo. O arquivo é esparso: registra apenas pares "
        "documento-termo observados. Os pesos não foram normalizados por comprimento do documento.\n\n"
        f"- Documentos: **{n_documentos}**\n"
        f"- Vocabulário: **{len(df)}** termos\n"
        f"- Células não nulas gravadas: **{total_pesos}**\n"
        f"- Arquivo: `{ARQUIVO_TF_IDF.name}`\n",
        encoding="utf-8",
    )
    print(f"TF-IDF criado: {total_pesos} pesos não nulos")


if __name__ == "__main__":
    executar()
