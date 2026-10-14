# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 [NOME DO AUTOR]. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Etapa 8 do fluxo: ponto de partida para modelagem, a definir pela pergunta."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import PLANO_MODELAGEM


def executar():
    PLANO_MODELAGEM.parent.mkdir(parents=True, exist_ok=True)
    PLANO_MODELAGEM.write_text(
        "# Etapa 8 — modelagem (a definir)\n\n"
        "Nenhum modelo foi ajustado. Antes de modelar, registrar:\n\n"
        "1. Pergunta de pesquisa e tarefa (descritiva, tópicos, classificação etc.).\n"
        "2. Unidade de análise e variável-alvo, se supervisionada.\n"
        "3. Representação textual e baseline.\n"
        "4. Estratégia de validação que evite vazamento entre anúncios relacionados.\n"
        "5. Semente, hiperparâmetros e versões das bibliotecas.\n",
        encoding="utf-8",
    )
    print(f"Plano de modelagem criado: {PLANO_MODELAGEM}")


if __name__ == "__main__":
    executar()