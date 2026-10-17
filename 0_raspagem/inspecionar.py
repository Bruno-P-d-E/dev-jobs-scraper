# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Bruno Proença de Souza. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""
Uso:
    python 0_raspagem/inspecionar.py dados/bruto/diagnostico_html/catho_desenvolvedor.html
"""
import sys
from pathlib import Path
from bs4 import BeautifulSoup

DADOS_BRUTOS = Path(__file__).resolve().parent.parent / "dados" / "bruto"
caminho = sys.argv[1] if len(sys.argv) > 1 else DADOS_BRUTOS / "diagnostico_html" / "catho_desenvolvedor.html"

with open(caminho, encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

print("TAMANHO DO HTML:", len(html))
print()
print("TITULO DA PAGINA:", soup.title.get_text() if soup.title else None)
print()
print("--- Primeiros 800 caracteres de texto visivel ---")
print(soup.get_text(" ", strip=True)[:800])
print()
print("--- Todos os hrefs que contem 'vaga' (ate 40) ---")
contador = 0
for a in soup.find_all("a", href=True):
    if "vaga" in a["href"].lower():
        print(a["href"])
        contador += 1
        if contador >= 40:
            break
if contador == 0:
    print("(nenhum href com 'vaga' encontrado)")
print()
print("--- Scripts JSON-LD encontrados ---")
scripts = soup.find_all("script", type="application/ld+json")
if not scripts:
    print("(nenhum script ld+json encontrado)")
for i, s in enumerate(scripts):
    conteudo = s.string or s.get_text() or ""
    print(f"--- script {i} (primeiros 300 chars) ---")
    print(conteudo[:300])
