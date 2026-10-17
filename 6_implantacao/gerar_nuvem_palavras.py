# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Bruno Proença de Souza. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Gera uma nuvem de palavras (PNG + SVG) das descrições higienizadas."""
import zlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wordcloud import WordCloud

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import FIGURAS
from gerar_graficos import ler


PASTA_GRAFICOS = FIGURAS
STOP = set("""a ao aos aquela aquelas aquele aqueles aquilo as até com como contra da das de dela delas dele deles depois desde desta deste do dos e ela elas ele eles em entre era eram essa essas esse esses esta estas este estes eu foi foram há isso isto já lhe lhes mais mas me mesmo minha minhas muito na nas nem nenhum nessa nesse nesta neste no nos nossa nossas nosso nossos o os ou para pela pelas pelo pelos por porque qual quando que quem se sem seu seus sua suas também te tem tendo ter teu teus toda todas todo todos tu um uma umas uns vai voce voces você vocês the a an and are as at be been but by can could did do does for from had has have he her hers him his i if in into is it its may more must my no not of on or our out over she should so such than that the their them then there these they this through to was we were what which who will with would you your about after again all also any before both during each further here how other own same some too very yet""".split())

FUNDO = "#fbfaf7"
CORES = ["#174A6E", "#246B8E", "#2B7A78", "#B05A35", "#5B5F97", "#347A58"]
MAX_PALAVRAS = 120


def cor_palavra(word, **kwargs):
    """Cor estável por palavra (não muda entre execuções)."""
    return CORES[zlib.crc32(word.encode("utf-8")) % len(CORES)]


def carregar_frequencias():
    frequencias = {}
    for linha in ler("frequencia_ngramas.csv"):
        if linha["campo"] != "descricao" or linha["n"] != "1":
            continue
        termo = linha["termo"].strip().lower()
        if len(termo) < 3 or termo in STOP or "limpar" in termo or termo == "texto":
            continue
        frequencias[termo] = max(frequencias.get(termo, 0), int(linha["ocorrencias"]))
    if not frequencias:
        raise RuntimeError("Não há unigramas de descrição para gerar a nuvem.")
    return frequencias


def gerar():
    frequencias = carregar_frequencias()

    nuvem = WordCloud(
        width=1800,
        height=1000,
        background_color=FUNDO,
        color_func=cor_palavra,
        max_words=MAX_PALAVRAS,
        min_font_size=12,
        max_font_size=220,
        prefer_horizontal=0.85,   # 15% das palavras ficam na vertical
        relative_scaling=0.6,     # equilíbrio entre frequência e ranking
        margin=6,
        random_state=42,          # layout reprodutível
        # font_path="caminho/para/Fonte.ttf",  # opcional: fonte personalizada
    ).generate_from_frequencies(frequencias)

    fig, ax = plt.subplots(figsize=(18, 10.5), facecolor=FUNDO)
    ax.imshow(nuvem, interpolation="bilinear")
    ax.axis("off")
    fig.suptitle("Palavras mais frequentes nas descrições",
                 x=0.04, y=0.97, ha="left", fontsize=26, fontweight="bold", color="#182b3a")
    fig.text(0.04, 0.925, "Descrições higienizadas · tamanho proporcional à frequência de ocorrência",
             ha="left", fontsize=13, color="#52616b")
    n_vagas = len(ler("vagas_higienizadas.csv"))
    fig.text(0.04, 0.025,
             f"Fonte: etapa 13 do pipeline CRISP-DM · corpus higienizado (n={n_vagas}) · stopwords removidas",
             ha="left", fontsize=10, color="#66727a")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.06)

    PASTA_GRAFICOS.mkdir(parents=True, exist_ok=True)
    base = PASTA_GRAFICOS / "06-nuvem-palavras-descricoes"
    fig.savefig(base.with_suffix(".png"), dpi=200, facecolor=FUNDO)
    plt.close(fig)

    # Versão vetorial da própria nuvem (sem título/rodapé), com fonte embutida
    base.with_suffix(".svg").write_text(
        nuvem.to_svg(embed_font=True), encoding="utf-8"
    )
    print(f"Figuras salvas: {base}.png e {base}.svg ({len(nuvem.words_)} palavras)")

if __name__ == "__main__":
    gerar()
