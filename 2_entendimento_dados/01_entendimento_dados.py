# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Bruno Proença de Souza. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""CRISP-DM 1–2: registra o estado inicial e questões de entendimento."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import ARQUIVO_BRUTO, RELATORIO_ENTENDIMENTO
from comum.io_utils import ler_csv, markdown_tabela


def executar():
    colunas, linhas = ler_csv(ARQUIVO_BRUTO)
    resumo = [(c, sum(not (r.get(c) or "").strip() for r in linhas)) for c in colunas]
    RELATORIO_ENTENDIMENTO.parent.mkdir(parents=True, exist_ok=True)
    RELATORIO_ENTENDIMENTO.write_text(
        "# CRISP-DM — entendimento do negócio e dos dados\n\n"
        "> A extração já foi realizada. Este pipeline usa a base existente e não executa raspagem.\n\n"
        "## Objetivo do estudo\n\n"
        "**Pendente de confirmação pelo pesquisador:** registrar a pergunta de pesquisa e a decisão que a análise deverá apoiar.\n\n"
        "## Escopo da base\n\n"
        f"- Arquivo de origem: `{ARQUIVO_BRUTO.name}`\n- Registros: {len(linhas)}\n"
        f"- Variáveis: {len(colunas)}\n- Unidade observacional presumida: anúncio de vaga (confirmar).\n\n"
        "## Completude inicial\n\n" + markdown_tabela(["Campo", "Valores ausentes"], resumo) +
        "\n\n## Decisões a documentar\n\n"
        "- População, período, plataformas e consultas que delimitam o estudo.\n"
        "- Critérios de inclusão/exclusão e variável de interesse (se houver).\n"
        "- Limitações de cobertura, divulgação salarial e dados pessoais.\n",
        encoding="utf-8",
    )
    print(f"Relatório criado: {RELATORIO_ENTENDIMENTO}")


if __name__ == "__main__":
    executar()
