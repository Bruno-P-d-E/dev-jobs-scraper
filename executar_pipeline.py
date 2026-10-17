# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Bruno Proença de Souza. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Executa as fases 2 a 5 do CRISP-DM sobre a extração já existente; não faz scraping.

A fase 0 (0_raspagem) é manual: gera dados/bruto/vagas_unificado.csv.
Ordem: fase a fase, e dentro de cada fase pela numeração dos scripts.
"""
import argparse
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

# (script, opção que o habilita; None = sempre roda)
ETAPAS = [
    ("2_entendimento_dados/01_entendimento_dados.py", None),
    ("2_entendimento_dados/02_exploracao.py", None),
    ("3_preparacao_dados/03_higienizacao.py", None),
    ("3_preparacao_dados/04_preparacao.py", None),
    ("3_preparacao_dados/05_tokenizacao.py", None),
    ("3_preparacao_dados/06_remocao_stopwords.py", None),
    ("3_preparacao_dados/07_lematizacao.py", None),
    ("3_preparacao_dados/10_matriz_frequencia_bow.py", None),
    ("3_preparacao_dados/11_tfidf.py", None),
    ("3_preparacao_dados/12_embeddings_sbert.py", "embeddings"),
    ("4_modelagem/08_modelagem.py", None),
    ("4_modelagem/13_ngramas_lexico_regex.py", None),
    ("4_modelagem/14_modelagem_topicos_clusters.py", "modelagem"),
    ("4_modelagem/16_classificar_modalidade.py", None),
    ("5_avaliacao/09_avaliacao.py", None),
    ("5_avaliacao/15_avaliacao_validacao.py", None),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--embeddings", action="store_true",
        help="executa também a etapa opcional SBERT (requer requirements/requirements-embeddings.txt)",
    )
    parser.add_argument(
        "--modelagem", action="store_true",
        help="executa também LDA e K-Means (requer requirements/requirements-modelagem.txt)",
    )
    args = parser.parse_args()
    for etapa, opcao in ETAPAS:
        if opcao and not getattr(args, opcao):
            continue
        print(f"\n=== {etapa} ===", flush=True)
        subprocess.run([sys.executable, str(RAIZ / etapa)], cwd=RAIZ, check=True)


if __name__ == "__main__":
    main()
