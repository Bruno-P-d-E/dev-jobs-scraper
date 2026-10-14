# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 [NOME DO AUTOR]. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Utilitários simples e sem dependências externas para CSVs do projeto."""
import csv
from collections import Counter
from pathlib import Path

from comum.config import ENCODING


def ler_csv(caminho: Path):
    if not caminho.exists():
        raise FileNotFoundError(f"Base não encontrada: {caminho}")
    with caminho.open("r", encoding=ENCODING, newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        if not leitor.fieldnames:
            raise ValueError(f"CSV sem cabeçalho: {caminho}")
        return leitor.fieldnames, list(leitor)


def escrever_csv(caminho: Path, colunas, linhas):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(linhas)


def frequencias(linhas, coluna):
    return Counter((linha.get(coluna) or "").strip() or "(ausente)" for linha in linhas)


def markdown_tabela(cabecalhos, linhas):
    def fmt(valor):
        return str(valor).replace("|", "\\|").replace("\n", " ")
    topo = "| " + " | ".join(map(fmt, cabecalhos)) + " |"
    separador = "| " + " | ".join("---" for _ in cabecalhos) + " |"
    corpo = ["| " + " | ".join(fmt(v) for v in linha) + " |" for linha in linhas]
    return "\n".join([topo, separador, *corpo])
