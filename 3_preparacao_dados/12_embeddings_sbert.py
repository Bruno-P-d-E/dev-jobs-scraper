# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 [NOME DO AUTOR]. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Etapa 12 opcional: embeddings semânticos de documentos usando SBERT multilíngue."""
import csv

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import ARQUIVO_EMBEDDINGS, ARQUIVO_LEMATIZADO, ARQUIVO_SIMILARIDADES, RELATORIO_EMBEDDINGS
from comum.io_utils import ler_csv

MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def executar():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as erro:
        raise RuntimeError(
            "Dependência ausente. Instale com: python -m pip install -r requirements-embeddings.txt"
        ) from erro

    _, linhas = ler_csv(ARQUIVO_LEMATIZADO)
    textos = [linha.get("tokens") or "" for linha in linhas]
    modelo = SentenceTransformer(MODELO)
    vetores = modelo.encode(
        textos, batch_size=32, show_progress_bar=True,
        convert_to_numpy=True, normalize_embeddings=True,
    )

    with ARQUIVO_EMBEDDINGS.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["documento_id", *(f"dim_{i + 1}" for i in range(vetores.shape[1]))])
        for indice, vetor in enumerate(vetores, start=1):
            escritor.writerow([indice, *(f"{valor:.8f}" for valor in vetor)])

    # Embeddings normalizados: produto interno equivale à similaridade cosseno.
    with ARQUIVO_SIMILARIDADES.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["documento_id", "vizinho_id", "similaridade_cosseno"])
        for i, vetor in enumerate(vetores):
            scores = vetores @ vetor
            scores[i] = -1
            vizinhos = scores.argsort()[-5:][::-1]
            for j in vizinhos:
                escritor.writerow([i + 1, int(j) + 1, f"{scores[j]:.8f}"])

    RELATORIO_EMBEDDINGS.parent.mkdir(parents=True, exist_ok=True)
    RELATORIO_EMBEDDINGS.write_text(
        "# Etapa 12 — embeddings semânticos com SBERT\n\n"
        f"Modelo: `{MODELO}`. O modelo multilíngue inclui português. Cada linha da entrada é codificada "
        "como um vetor denso normalizado a partir da sequência de tokens lematizados; por isso, esta etapa "
        "usa a representação contextual do modelo, diferente da contagem BoW/TF-IDF. A similaridade "
        "cosseno foi calculada e os cinco vizinhos mais próximos de cada documento foram registrados.\n\n"
        f"- Documentos: **{len(textos)}**\n"
        f"- Dimensões por vetor: **{vetores.shape[1]}**\n"
        f"- Embeddings: `{ARQUIVO_EMBEDDINGS.name}`\n"
        f"- Cinco vizinhos por documento: `{ARQUIVO_SIMILARIDADES.name}`\n"
        "\nA primeira execução pode baixar os pesos do modelo; registre a versão/identificador do modelo e "
        "mantenha os arquivos de saída para reproduzir a análise.\n",
        encoding="utf-8",
    )
    print(f"Embeddings concluídos: {len(textos)} documentos × {vetores.shape[1]} dimensões")


if __name__ == "__main__":
    executar()
