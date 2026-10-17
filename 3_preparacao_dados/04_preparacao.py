# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Bruno Proença de Souza. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Etapa 4 do fluxo: recebe a base higienizada sem repetir as regras de limpeza."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import ARQUIVO_HIGIENIZADO, ARQUIVO_PREPARADO, RELATORIO_PREPARACAO
from comum.io_utils import ler_csv, escrever_csv


def executar():
    colunas, linhas = ler_csv(ARQUIVO_HIGIENIZADO)
    escrever_csv(ARQUIVO_PREPARADO, colunas, linhas)
    RELATORIO_PREPARACAO.parent.mkdir(parents=True, exist_ok=True)
    RELATORIO_PREPARACAO.write_text(
        "# Etapa 4 — preparação dos dados\n\n"
        "Esta etapa começa após a higienização e não repete filtros.\n\n"
        f"- Entrada: `{ARQUIVO_HIGIENIZADO.name}`\n"
        f"- Vagas recebidas: **{len(linhas)}** (contagem executada pelo script)\n"
        f"- Vagas após preparação: **{len(linhas)}**\n"
        "- Limpezas ou exclusões nesta etapa: **0**\n"
        f"- Saída para as próximas etapas: `{ARQUIVO_PREPARADO.name}`\n",
        encoding="utf-8",
    )
    print(f"Preparação concluída: {len(linhas)} vagas encaminhadas à modelagem.")


if __name__ == "__main__":
    executar()
