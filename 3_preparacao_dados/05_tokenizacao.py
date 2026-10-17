# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Bruno Proença de Souza. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Etapa 5: reúne e tokeniza os campos textuais relevantes de cada vaga."""
import re
from collections import Counter

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import (ARQUIVO_PREPARADO, ARQUIVO_TOKENIZADO,
                    COLUNAS_TEXTO_VAGA, RELATORIO_TOKENIZACAO)
from comum.io_utils import ler_csv, escrever_csv

# Remove endereços web/e-mail antes de separar tokens.
PADRAO_URL_EMAIL = re.compile(r"(?i)(?:https?://|www\.)\S+|[\w.+-]+@[\w.-]+\.[a-z]{2,}")

# Alternativas especiais preservam identificadores técnicos como C++, C# e .NET.
PADRAO_TOKEN = re.compile(
    r"(?i)(?<!\w)\.net(?!\w)|(?<!\w)c\+\+(?!\w)|(?<!\w)c\#(?!\w)|"
    r"(?<!\w)f\#(?!\w)|(?<!\w)ci/cd(?!\w)|"
    r"[\w]+(?:[./+#-][\w+#-]+)*",
    flags=re.UNICODE,
)

def tokenizar(texto):
    """Tokeniza texto sem URLs/e-mails e números isolados."""
    texto = PADRAO_URL_EMAIL.sub(" ", texto or "")
    tokens = []
    for correspondencia in PADRAO_TOKEN.findall(texto):
        token = correspondencia.casefold()
        if not token:
            continue
        # Remove números puros, preservando nomes técnicos alfanuméricos.
        if re.fullmatch(r"\d+(?:[.,]\d+)*%?", token):
            continue
        tokens.append(token)
    return tokens


def executar():
    colunas, linhas = ler_csv(ARQUIVO_PREPARADO)
    documentos = []
    frequencias = Counter()
    total_tokens = 0
    documentos_vazios = 0
    for linha in linhas:
        # Junta atributos textuais da vaga; URLs, IDs, datas, salários e demais
        # campos numéricos/metadados não entram na representação tokenizada.
        texto = " ".join(
            (linha.get(campo) or "").strip()
            for campo in COLUNAS_TEXTO_VAGA
            if (linha.get(campo) or "").strip()
        )
        tokens = tokenizar(texto)
        documentos.append({"tokens": " ".join(tokens)})
        frequencias.update(tokens)
        total_tokens += len(tokens)
        documentos_vazios += not tokens

    escrever_csv(ARQUIVO_TOKENIZADO, ["tokens"], documentos)
    RELATORIO_TOKENIZACAO.parent.mkdir(parents=True, exist_ok=True)
    media_tokens = total_tokens / len(documentos) if documentos else 0
    RELATORIO_TOKENIZACAO.write_text(
        "# Etapa 5 — tokenização\n\n"
        "Uma linha por vaga. O conteúdo é a junção dos campos textuais configurados em `config.py`, gravada em uma única coluna (`tokens`). URLs/e-mails e números isolados foram removidos; stopwords são mantidas nesta etapa e removidas na etapa 6; tokens ficam em minúsculas, com acentos preservados. Expressões técnicas como C++, C#, .NET e CI/CD são preservadas. Não foi aplicado stemming ou lematização.\n\n"
        f"- Documentos tokenizados: **{len(documentos)}**\n"
        f"- Total de tokens: **{total_tokens}**\n"
        f"- Vocabulário (tokens únicos): **{len(frequencias)}**\n"
        f"- Média de tokens por vaga: **{media_tokens:.2f}**\n"
        f"- Vagas sem tokens: **{documentos_vazios}**\n"
        f"- CSV tokenizado: `{ARQUIVO_TOKENIZADO.name}`\n",
        encoding="utf-8",
    )
    print(f"Tokenização concluída: {len(documentos)} vagas, {total_tokens} tokens, {len(frequencias)} tokens únicos.")
    print(f"CSV tokenizado: {ARQUIVO_TOKENIZADO}")


if __name__ == "__main__":
    executar()
