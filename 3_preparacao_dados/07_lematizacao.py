# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 [NOME DO AUTOR]. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Etapa 7: lematiza os tokens com o modelo de português do spaCy."""
from collections import Counter

import spacy

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import ARQUIVO_LEMATIZADO, ARQUIVO_SEM_STOPWORDS, RELATORIO_LEMATIZACAO
from comum.io_utils import ler_csv, escrever_csv

MODELO = "pt_core_news_sm"
# Vocabulário de TI e siglas que o modelo geral pode interpretar como verbos.
TERMOS_TECNICOS_PRESERVADOS = set("""
api apis ai ia aws azure gcp c csharp cplusplus net dotnet java javascript typescript
python node nodejs js code backend frontend back front full stack docker kubernetes k8s
git github gitlab linux windows react angular vue spring django flask fastapi rails ruby
php laravel kafka redis graphql html css sass sql nosql postgresql mysql mongodb oracle
etl bi qa devops ci cd rest grpc json xml saas erp crm ux ui cloud databricks datadog
machine learning deep learning openai chatgpt claude copilot github actions terraform vaga descrição
hibrido hibrida hibrido hibrida remoto remota presencial presenciais flexivel flexiveis
""".split())


def executar():
    try:
        nlp = spacy.load(MODELO)
    except (OSError, ImportError) as erro:
        raise RuntimeError(
            f"Modelo {MODELO} não encontrado. Instale as dependências com "
            "python -m pip install -r requirements-nlp.txt."
        ) from erro

    _, linhas = ler_csv(ARQUIVO_SEM_STOPWORDS)
    textos = [(linha.get("tokens") or "") for linha in linhas]
    documentos = []
    total_entrada = sum(len(texto.split()) for texto in textos)
    total_saida = tokens_alterados = termos_tecnicos_preservados = documentos_vazios = 0
    vocab_antes = set()
    vocab_depois = set()

    for doc in nlp.pipe(textos, batch_size=64):
        lemas = []
        for token in doc:
            if token.is_space:
                continue
            original = token.text.lower()
            lema_modelo = token.lemma_.lower().strip()
            if original in TERMOS_TECNICOS_PRESERVADOS or token.pos_ == "PROPN":
                lema = original
                termos_tecnicos_preservados += original in TERMOS_TECNICOS_PRESERVADOS
            elif token.pos_ == "NOUN" and token.morph.get("Number") == ["Sing"]:
                # Substantivos singulares normalmente já estão em sua forma-base.
                lema = original
            elif token.pos_ == "VERB" and original.endswith(("ção", "são")):
                # Protege substantivos em -ção/-são classificados equivocadamente como verbos.
                lema = original
            elif (lema_modelo == original + "r"
                  and original[-1:] not in {"a", "e", "i", "o", "u"}):
                # Evita criar infinitivos falsos para termos em inglês (ex.: back -> backr).
                lema = original
                termos_tecnicos_preservados += 1
            else:
                lema = lema_modelo
            # A etapa anterior já retirou os caracteres especiais; manter essa garantia.
            lema = "".join(ch for ch in lema if ch.isalnum())
            if not lema:
                continue
            tokens_alterados += lema != original
            lemas.append(lema)
            vocab_depois.add(lema)
        total_saida += len(lemas)
        documentos_vazios += not lemas
        vocab_antes.update(doc.text.split())
        documentos.append({"tokens": " ".join(lemas)})

    escrever_csv(ARQUIVO_LEMATIZADO, ["tokens"], documentos)
    RELATORIO_LEMATIZACAO.parent.mkdir(parents=True, exist_ok=True)
    RELATORIO_LEMATIZACAO.write_text(
        "# Etapa 7 — lematização\n\n"
        f"Os tokens da etapa 6 foram processados com o modelo `{MODELO}` do spaCy. "
        "Cada vaga continua em uma linha e a saída possui somente a coluna `tokens`. "
        "A lematização usa o contexto linguístico do modelo. Um vocabulário técnico configurado, nomes próprios e substantivos singulares são preservados para reduzir alterações ambíguas em termos de TI.\n\n"
        f"- Vagas antes/depois: **{len(linhas)} / {len(documentos)}**\n"
        f"- Tokens antes: **{total_entrada}**\n"
        f"- Tokens depois: **{total_saida}**\n"
        f"- Tokens com lema diferente da forma original: **{tokens_alterados}**\n"
        f"- Termos técnicos ou formas ambíguas preservadas: **{termos_tecnicos_preservados}**\n"
        f"- Vocabulário antes/depois: **{len(vocab_antes)} / {len(vocab_depois)}**\n"
        f"- Vagas sem tokens após lematização: **{documentos_vazios}**\n"
        f"- CSV resultante: `{ARQUIVO_LEMATIZADO.name}`\n",
        encoding="utf-8",
    )
    print(
        f"Lematização concluída: {len(documentos)} vagas, "
        f"{tokens_alterados} tokens alterados; CSV: {ARQUIVO_LEMATIZADO}"
    )


if __name__ == "__main__":
    executar()
