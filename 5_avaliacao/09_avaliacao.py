# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 [NOME DO AUTOR]. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Etapa 9 do fluxo: roteiro de avaliação e reprodução dos resultados."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import PLANO_AVALIACAO


def executar():
    PLANO_AVALIACAO.parent.mkdir(parents=True, exist_ok=True)
    PLANO_AVALIACAO.write_text(
        "# Etapa 9 — avaliação (a completar)\n\n"
        "Registrar após a modelagem:\n\n"
        "- Critérios e métricas alinhados à pergunta; baseline e resultados por fonte.\n"
        "- Inspeção humana, erros, incerteza e limitações.\n"
        "- Decisão sobre resultados e iterações necessárias.\n"
        "- Arquivos, comandos e ambiente necessários para reproduzir tabelas e figuras.\n",
        encoding="utf-8",
    )
    print(f"Plano de avaliação criado: {PLANO_AVALIACAO}")


if __name__ == "__main__":
    executar()