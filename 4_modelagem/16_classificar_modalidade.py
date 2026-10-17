# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Bruno Proença de Souza. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Etapa 16: normaliza modalidade e infere apenas menções explícitas no texto."""
import csv
import re
import unicodedata
from collections import Counter
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import ARQUIVO_HIGIENIZADO, ARQUIVO_MODALIDADE_CLASSIFICADA, RELATORIO_MODALIDADE
from comum.io_utils import ler_csv

PADROES = {
    "Remoto": re.compile(r"(?<!\w)(?:remot[oa]s?|remote|work from home|home office)(?!\w)"),
    "Híbrido": re.compile(r"(?<!\w)(?:hibrid[oa]s?|hybrid)(?!\w)"),
    "Presencial": re.compile(r"(?<!\w)(?:presencial(?:mente)?|presenciais|on[ -]?site|onsite)(?!\w)"),
}
MAPA_CAMPO = {
    "remote": "Remoto", "remoto": "Remoto", "remota": "Remoto",
    "hybrid": "Híbrido", "hibrido": "Híbrido", "híbrido": "Híbrido",
    "on-site": "Presencial", "on site": "Presencial", "onsite": "Presencial",
    "presencial": "Presencial", "presencialmente": "Presencial",
}

def normalizar(texto):
    sem_acentos = unicodedata.normalize("NFKD", (texto or "").casefold())
    return "".join(c for c in sem_acentos if not unicodedata.combining(c))


def executar():
    colunas, vagas = ler_csv(ARQUIVO_HIGIENIZADO)
    resultados = []
    totais = Counter()
    origens = Counter()
    for doc_id, vaga in enumerate(vagas, 1):
        original = (vaga.get("jobLocationType") or "").strip()
        campo_norm = normalizar(original)
        descricao = vaga.get("jobDescription_limpa") or ""
        texto_norm = normalizar(descricao)
        evidencias = []
        if original and campo_norm in MAPA_CAMPO:
            modalidade = MAPA_CAMPO[campo_norm]
            origem = "campo_estruturado"
            modalidades_texto = []
        else:
            modalidades_texto = []
            for categoria, padrao in PADROES.items():
                matches = list(padrao.finditer(texto_norm))
                # Ignora menção negada imediatamente antes do termo; não interpreta frases vagas.
                positivos = []
                for match in matches:
                    anterior = texto_norm[max(0, match.start() - 28):match.start()]
                    if re.search(r"(?:\bnao\s+(?:e|sera|seria|precisa|necessariamente)|\bnot\s+(?:be|necessarily)|\bnever)\s*$", anterior):
                        continue
                    positivos.append(match.group(0))
                if positivos:
                    modalidades_texto.append(categoria)
                    evidencias.extend(f"{categoria}: {hit}" for hit in positivos)
            modalidades_texto = sorted(set(modalidades_texto))
            if len(modalidades_texto) == 1:
                modalidade = modalidades_texto[0]
                origem = "texto_explicito"
            elif len(modalidades_texto) > 1:
                modalidade = "Menções ambíguas"
                origem = "texto_com_multiplas_modalidades"
            else:
                modalidade = "Não informado"
                origem = "sem_evidencia"

        totais[modalidade] += 1
        origens[origem] += 1
        resultados.append({
            "documento_id": doc_id,
            "platform": vaga.get("platform", ""),
            "jobTitle": vaga.get("jobTitle", ""),
            "jobUrl": vaga.get("jobUrl", ""),
            "modalidade_original": original,
            "modalidade_classificada": modalidade,
            "origem_classificacao": origem,
            "modalidades_detectadas_no_texto": "; ".join(modalidades_texto),
            "evidencias_textuais": "; ".join(evidencias),
        })

    campos = ["documento_id", "platform", "jobTitle", "jobUrl", "modalidade_original", "modalidade_classificada", "origem_classificacao", "modalidades_detectadas_no_texto", "evidencias_textuais"]
    with ARQUIVO_MODALIDADE_CLASSIFICADA.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos); w.writeheader(); w.writerows(resultados)
    linhas = [
        "# Etapa 16 — classificação de modalidade de trabalho", "",
        "O campo de origem foi normalizado: `remote` → Remoto, `hybrid` → Híbrido e `on-site`/`onsite` → Presencial. Quando o campo está vazio, o texto da descrição só é usado se trouxer menção explícita; uma única modalidade encontrada é marcada como inferida, menções a mais de uma são mantidas como ambíguas e ausência de evidência permanece Não informado.",
        "",
        f"- Anúncios analisados: **{len(vagas)}**",
        f"- Campo estruturado: **{origens['campo_estruturado']}**",
        f"- Inferidos de menção textual única: **{origens['texto_explicito']}**",
        f"- Menções textuais múltiplas/ambíguas: **{origens['texto_com_multiplas_modalidades']}**",
        f"- Sem evidência textual: **{origens['sem_evidencia']}**",
        f"- CSV com rótulo, origem e evidências: `{ARQUIVO_MODALIDADE_CLASSIFICADA.name}`",
        "",
        "## Contagens por classe",
        "",
        "| Modalidade | Anúncios | Percentual do corpus |",
        "|---|---:|---:|",
    ]
    for categoria, total in totais.most_common():
        linhas.append(f"| {categoria} | {total} | {100 * total / len(vagas):.1f}% |")
    linhas.extend([
        "",
        "As inferências se baseiam em correspondências literais na descrição; não equivalem à confirmação do empregador. A regra não força uma categoria quando o texto menciona modalidades distintas. ‘Não informado’ agora significa que o campo estava vazio e não foi encontrada evidência explícita única no texto. Consulte os registros individuais antes de usar a classificação como resultado substantivo.",
        "",
    ])
    RELATORIO_MODALIDADE.write_text("\n".join(linhas), encoding="utf-8")
    print(f"Modalidades classificadas: {dict(totais)}; relatório: {RELATORIO_MODALIDADE}")


if __name__ == "__main__":
    executar()
