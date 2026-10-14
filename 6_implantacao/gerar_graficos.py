# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 [NOME DO AUTOR]. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Gera figuras SVG diretamente dos resultados do pipeline (sem inferir valores)."""
import csv
import html
from collections import Counter
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import FIGURAS, SAIDA

PASTA_GRAFICOS = FIGURAS

# Paleta roxa
ROXO_ESCURO = "#2e1065"
ROXO_TEXTO = "#4c1d95"
ROXO_MEDIO = "#7c3aed"
ROXO_CLARO = "#a78bfa"
ROXO_FUNDO = "#faf8ff"
ROXO_TRILHA = "#efe9fb"
ROXO_GRADE = "#e4dbf7"
CINZA_LILAS = "#b9aed0"  # "Não categorizada"

# Tons por categoria de modalidade (pares: início/fim do degradê)
CORES_MODALIDADE = {
    "Remoto": ("#6d28d9", "#a78bfa"),
    "Híbrido": ("#8b5cf6", "#c4b5fd"),
    "Presencial": ("#a855f7", "#d8b4fe"),
    "Não categorizada": ("#9d92b8", "#cfc7e0"),
}


def ler(nome):
    caminho = next(SAIDA.rglob(nome), None)  # CSVs ficam em resultados/<fase>/
    if caminho is None:
        raise FileNotFoundError(f"{nome} não encontrado em {SAIDA}; execute executar_pipeline.py antes.")
    with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def fmt(valor):
    return f"{valor:,}".replace(",", ".")


def gerar_barras(nome, titulo, subtitulo, rotulo_x, dados, denominador=None, origem="", cores=None):
    """Barras horizontais com degradê roxo, trilha de fundo e valores explícitos.

    cores: dict opcional {rótulo: (cor_inicio, cor_fim)} para colorir barras individualmente.
    """
    largura = 1400
    margem_esq = 440
    margem_dir = 230
    topo = 190
    altura_linha = 50
    altura_barra = 32
    margem_inf = 125
    altura = topo + altura_linha * len(dados) + margem_inf
    largura_plot = largura - margem_esq - margem_dir
    maximo = max((valor for _, valor in dados), default=1)
    escala = maximo * 1.12 if maximo else 1
    ticks = 5

    defs = [
        f'<linearGradient id="g-padrao" x1="0" x2="1" y1="0" y2="0">'
        f'<stop offset="0" stop-color="{ROXO_MEDIO}"/><stop offset="1" stop-color="{ROXO_CLARO}"/></linearGradient>',
        f'<linearGradient id="g-topo" x1="0" x2="1" y1="0" y2="0">'
        f'<stop offset="0" stop-color="{ROXO_TEXTO}"/><stop offset="1" stop-color="{ROXO_MEDIO}"/></linearGradient>',
        '<filter id="sombra" x="-2%" y="-2%" width="104%" height="106%">'
        '<feDropShadow dx="0" dy="3" stdDeviation="6" flood-color="#4c1d95" flood-opacity="0.12"/></filter>',
    ]
    if cores:
        for i, (cor_a, cor_b) in enumerate(cores.values()):
            defs.append(
                f'<linearGradient id="g-{i}" x1="0" x2="1" y1="0" y2="0">'
                f'<stop offset="0" stop-color="{cor_a}"/><stop offset="1" stop-color="{cor_b}"/></linearGradient>'
            )
    ids_cor = {rotulo: f"g-{i}" for i, rotulo in enumerate(cores or {})}

    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" height="{altura}" viewBox="0 0 {largura} {altura}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{html.escape(titulo)}</title>',
        f'<desc id="desc">{html.escape(subtitulo)} Gráfico de barras horizontais com {len(dados)} categorias.</desc>',
        f'<defs>{"".join(defs)}</defs>',
        f'<rect width="100%" height="100%" fill="{ROXO_FUNDO}"/>',
        f'<rect x="20" y="20" width="{largura - 40}" height="{altura - 40}" rx="18" fill="#ffffff" filter="url(#sombra)"/>',
        f'<rect x="20" y="20" width="{largura - 40}" height="8" rx="4" fill="url(#g-topo)"/>',
        '<style>'
        f'text{{font-family:"Segoe UI",Inter,Arial,Helvetica,sans-serif;fill:{ROXO_ESCURO}}}'
        '.title{font-size:36px;font-weight:700}'
        '.sub{font-size:20px;fill:#6b5b95}'
        '.axis{font-size:17px;fill:#7a6b9f}'
        '.label{font-size:20px;font-weight:500}'
        f'.value{{font-size:19px;font-weight:700;fill:{ROXO_TEXTO}}}'
        '.fonte{font-size:13px;fill:#7a6b9f}'  # nota "Fonte:" mantida no tamanho original
        f'.grid{{stroke:{ROXO_GRADE};stroke-width:1;stroke-dasharray:3 4}}'
        '</style>',
        f'<text class="title" x="56" y="80">{html.escape(titulo)}</text>',
        f'<text class="sub" x="56" y="116">{html.escape(subtitulo)}</text>',
    ]

    plot_top = topo - 26
    plot_bottom = topo + altura_linha * len(dados) - 12
    for i in range(ticks + 1):
        x = margem_esq + largura_plot * i / ticks
        v = escala * i / ticks
        partes.append(f'<line class="grid" x1="{x:.1f}" y1="{plot_top}" x2="{x:.1f}" y2="{plot_bottom}"/>')
        partes.append(f'<text class="axis" text-anchor="middle" x="{x:.1f}" y="{plot_bottom + 28}">{fmt(round(v))}</text>')

    for i, (rotulo, valor) in enumerate(dados):
        y = topo + i * altura_linha
        largura_barra = max(largura_plot * valor / escala, 3)
        if cores and rotulo in ids_cor:
            fill = f"url(#{ids_cor[rotulo]})"
        else:
            fill = "url(#g-topo)" if i == 0 else "url(#g-padrao)"
        partes.append(f'<text class="label" text-anchor="end" x="{margem_esq - 18}" y="{y + 23}">{html.escape(rotulo)}</text>')
        partes.append(f'<rect x="{margem_esq}" y="{y}" width="{largura_plot}" height="{altura_barra}" rx="16" fill="{ROXO_TRILHA}" opacity="0.55"/>')
        partes.append(f'<rect x="{margem_esq}" y="{y}" width="{largura_barra:.1f}" height="{altura_barra}" rx="16" fill="{fill}"/>')
        percentual = f" · {100 * valor / denominador:.1f}%" if denominador else ""
        partes.append(f'<text class="value" x="{margem_esq + largura_barra + 12:.1f}" y="{y + 23}">{fmt(valor)}{percentual}</text>')

    partes.append(f'<text class="axis" x="{margem_esq}" y="{altura - 72}">{html.escape(rotulo_x)}</text>')
    nota = f"Fonte: resultados do pipeline; {origem}." if origem else "Fonte: resultados do pipeline."
    if denominador:
        nota += f" Percentuais usam denominador n={fmt(denominador)}."
    partes.append(f'<text class="fonte" x="56" y="{altura - 40}">{html.escape(nota)}</text>')
    partes.append('</svg>')
    (PASTA_GRAFICOS / nome).write_text("\n".join(partes), encoding="utf-8")


def executar():
    PASTA_GRAFICOS.mkdir(parents=True, exist_ok=True)

    # 1. Fluxo de seleção, usando contagens dos relatórios calculadas pela etapa 3.
    higienizacao = {r["etapa"]: r for r in ler("log_higienizacao.csv")}
    etapas = [
        ("Entrada", int(higienizacao["Entrada"]["vagas_depois"])),
        ("Idioma português", int(higienizacao["Exclusão de idioma não português"]["vagas_depois"])),
        ("Título profissional", int(higienizacao["Filtro de profissão pelo título"]["vagas_depois"])),
        ("Após deduplicação", int(higienizacao["Exclusão de descrição duplicada por empresa"]["vagas_depois"])),
    ]
    vagas = ler("vagas_higienizadas.csv")
    n_base = len(vagas)
    gerar_barras(
        "01-retencao-do-corpus.svg", "Seleção dos anúncios para análise",
        "O corpus é reduzido por filtros sequenciais; barras mostram registros retidos em cada etapa.",
        "Anúncios retidos (n)", etapas, 2605,
        f"relatório de higienização; último estágio contém {fmt(etapas[-1][1])} anúncios",
    )

    # 2. Tecnologias mencionadas por anúncio (não total de repetições).
    tecnologias = [r for r in ler("resumo_lexico_dominio.csv") if r["categoria"] == "tecnologia"]
    tecnologia_top = sorted(((r["termo"], int(r["documentos"])) for r in tecnologias), key=lambda x: x[1], reverse=True)[:15]
    gerar_barras(
        "02-tecnologias-por-anuncio.svg", "Tecnologias mencionadas nas vagas",
        "Contagem de anúncios com ao menos uma ocorrência do termo no léxico inicial.",
        "Anúncios contendo o termo (n)", tecnologia_top, n_base,
        "léxico automático não validado manualmente; termos podem coexistir na mesma vaga",
    )

    # 3. Modalidade: 3 categorias + "Não categorizada" (ambíguas e sem evidência).
    principais = ("Remoto", "Híbrido", "Presencial")
    contagem = Counter(
        r["modalidade_classificada"] if r["modalidade_classificada"] in principais else "Não categorizada"
        for r in ler("modalidade_classificada.csv")
    )
    modalidade_dados = sorted(
        ((cat, contagem[cat]) for cat in principais if contagem[cat]),
        key=lambda x: x[1], reverse=True,
    )
    if contagem["Não categorizada"]:
        modalidade_dados.append(("Não categorizada", contagem["Não categorizada"]))
    gerar_barras(
        "03-modalidade-de-trabalho.svg", "Modalidade de trabalho",
        "Remoto, híbrido e presencial; menções ambíguas e anúncios sem evidência ficam em 'Não categorizada'.",
        "Anúncios (n)", modalidade_dados, n_base,
        "campo jobLocationType normalizado, com inferência apenas para menção explícita única; on-site = presencial",
        cores=CORES_MODALIDADE,
    )

    # 4. Expressões recorrentes; remove somente marcadores de processamento que não são conteúdo de vaga.
    ngramas = ler("frequencia_ngramas.csv")
    stop = set("a ao aos as com como da das de do dos e em entre na nas no nos o os ou para pela pelo por que se sem um uma uns the and for from in of on or to with".split())
    frases = []
    for r in ngramas:
        termos = r["termo"].split()
        if r["campo"] != "descricao" or r["n"] not in {"2", "3"}:
            continue
        if termos[0] in stop or termos[-1] in stop:
            continue
        if "limpar texto" in r["termo"] or "texto limpar" in r["termo"]:
            continue
        frases.append((r["termo"], int(r["documentos"])))
    frases_top = sorted(frases, key=lambda x: x[1], reverse=True)[:15]
    gerar_barras(
        "04-expressoes-recorrentes.svg", "Expressões recorrentes nas descrições",
        "Bigramas e trigramas mais presentes; marcadores literais de processamento foram excluídos deste gráfico.",
        "Descrições contendo a expressão (n)", frases_top, n_base,
        "n-gramas gerados dos textos preparados; expressões podem se sobrepor",
    )

    # 5. Competências/habilidades/formação: números são anúncios, não ocorrências repetidas.
    outros = [r for r in ler("resumo_lexico_dominio.csv") if r["categoria"] != "tecnologia"]
    outros_top = sorted(
        ((f"{r['termo']} · {r['categoria']}", int(r["documentos"])) for r in outros),
        key=lambda x: x[1], reverse=True,
    )[:15]
    gerar_barras(
        "05-competencias-por-anuncio.svg", "Competências e qualificações no léxico inicial",
        "Anúncios correspondentes a termos de hard skills, soft skills ou formação.",
        "Anúncios contendo o termo (n)", outros_top, n_base,
        "léxico inicial sujeito a falsos positivos e cobertura incompleta; categorias não exclusivas",
    )

    arquivos = [
        ("01-retencao-do-corpus.svg", "Retenção do corpus"),
        ("02-tecnologias-por-anuncio.svg", "Tecnologias por anúncio"),
        ("03-modalidade-de-trabalho.svg", "Modalidade de trabalho"),
        ("04-expressoes-recorrentes.svg", "Expressões recorrentes"),
        ("05-competencias-por-anuncio.svg", "Competências e qualificações"),
    ]
    linhas = [
        "# Figuras exploratórias do corpus de vagas", "",
        "As figuras foram geradas dos CSVs em `resultados/`. Percentuais usam o denominador indicado em cada gráfico. Categorias de habilidades vêm de léxico automático ainda não validado. A modalidade é normalizada a partir do campo original e inferida da descrição apenas quando há menção explícita única; o gráfico apresenta Remoto, Híbrido e Presencial, e agrupa em 'Não categorizada' as menções ambíguas e os anúncios sem campo ou evidência textual. O gráfico de n-gramas exclui somente as expressões literais de limpeza ‘limpar texto’/‘texto limpar’, que aparecem como artefato em parte das descrições; os CSVs originais não foram alterados.",
        "",
    ]
    for nome, titulo in arquivos:
        linhas.extend([f"## {titulo}", "", f"![{titulo}]({nome})", ""])
    linhas.extend([
        "## Observação sobre interpretação", "",
        f"As contagens descrevem os {fmt(n_base)} anúncios mantidos após os filtros do pipeline, não o mercado de trabalho inteiro. Uma vaga pode mencionar vários termos; percentuais de termos não somam 100%. Anúncios coletados em diferentes plataformas e períodos podem ter cobertura desigual.",
        "",
    ])
    (PASTA_GRAFICOS / "README_figuras.md").write_text("\n".join(linhas), encoding="utf-8")
    print(f"Figuras criadas em {PASTA_GRAFICOS}: {len(arquivos)} gráficos SVG")


if __name__ == "__main__":
    executar()