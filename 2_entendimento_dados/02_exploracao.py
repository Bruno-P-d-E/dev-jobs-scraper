# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 [NOME DO AUTOR]. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""CRISP-DM 2: perfil exploratório reproduzível da base extraída."""
from statistics import mean, median

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import ARQUIVO_BRUTO, RELATORIO_EXPLORACAO
from comum.io_utils import frequencias, ler_csv, markdown_tabela


def executar():
    colunas, linhas = ler_csv(ARQUIVO_BRUTO)
    ausentes = [(c, sum(not (r.get(c) or "").strip() for r in linhas)) for c in colunas]
    blocos = ["# CRISP-DM — exploração dos dados", "",
              f"Arquivo analisado: `{ARQUIVO_BRUTO}`  ",
              f"Registros: **{len(linhas)}**  ", f"Variáveis: **{len(colunas)}**", "",
              "> Todos os valores quantitativos deste relatório foram calculados por este script, diretamente do arquivo de entrada, nesta execução. Não são números preenchidos manualmente.",
              "", "## Ausências por campo", "",
              markdown_tabela(["Campo", "Ausentes", "%"],
                              [(c, n, f"{n / len(linhas):.1%}" if linhas else "n/a") for c, n in ausentes]), ""]
    indicadores = []
    for nome, campo in (("Anúncios sem título", "jobTitle"), ("Anúncios sem descrição", "jobDescription")):
        if campo in colunas:
            indicadores.append((nome, sum(not (r.get(campo) or "").strip() for r in linhas)))
    if "jobUrl" in colunas:
        urls = [(r.get("jobUrl") or "").strip().casefold() for r in linhas]
        urls_validas = [url for url in urls if url]
        indicadores.append(("URLs vazias", len(urls) - len(urls_validas)))
        indicadores.append(("Ocorrências duplicadas de URL exata", len(urls_validas) - len(set(urls_validas))))
    if indicadores:
        blocos += ["## Indicadores de completude e duplicidade", "",
                   markdown_tabela(["Indicador", "Quantidade"], indicadores), ""]
    for campo in ("platform", "pais", "employmentType", "jobLocationType"):
        if campo in colunas:
            contagem = frequencias(linhas, campo).most_common(30)
            blocos += [f"## Distribuição: `{campo}`", "", markdown_tabela([campo, "Registros"], contagem), ""]
    if "jobDescription" in colunas:
        tamanhos = [len((r.get("jobDescription") or "").strip()) for r in linhas]
        preenchidos = [n for n in tamanhos if n]
        estatisticas = [("Descrições preenchidas", len(preenchidos)),
                        ("Comprimento mínimo", min(preenchidos) if preenchidos else 0),
                        ("Comprimento mediano", median(preenchidos) if preenchidos else 0),
                        ("Comprimento médio", round(mean(preenchidos), 2) if preenchidos else 0),
                        ("Comprimento máximo", max(preenchidos) if preenchidos else 0)]
        blocos += ["## Descrições", "", markdown_tabela(["Métrica", "Valor calculado"], estatisticas), ""]
    blocos += ["## Observações", "", "Este perfil não exclui linhas nem infere valores. Interprete diferenças entre fontes e dados ausentes antes de modelar. Ao alterar a base configurada, execute o script novamente para recalcular todos os indicadores.", ""]
    RELATORIO_EXPLORACAO.parent.mkdir(parents=True, exist_ok=True)
    RELATORIO_EXPLORACAO.write_text("\n".join(blocos), encoding="utf-8")
    print(f"Relatório criado: {RELATORIO_EXPLORACAO}")

if __name__ == "__main__":
    executar()