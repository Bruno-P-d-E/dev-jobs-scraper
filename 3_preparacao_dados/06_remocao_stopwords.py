# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 [NOME DO AUTOR]. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Etapa 6: normaliza tokens e remove stopwords, com auditoria por operação."""
from collections import Counter
import unicodedata

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import ARQUIVO_SEM_STOPWORDS, ARQUIVO_TOKENIZADO, RELATORIO_STOPWORDS
from comum.io_utils import ler_csv, escrever_csv

# Lista explícita, local e reproduzível; pode ser ajustada conforme a pesquisa.
STOPWORDS = set("""
a ao aos aquela aquelas aquele aqueles aquilo as até com como da das de dela delas dele deles
 depois do dos e ela elas ele eles em entre era eram essa essas este estes foi foram isso isto
 já lhe lhes mas me mesmo minha minhas muito na nas nem no nos nossa nossas nosso nossos num numa
 o os ou para pela pelas pelo pelos por qual quando que quem se sem seu seus sob sobre sua suas
 também te tem tendo ter teu teus toda todas todo todos tu tua tuas um uma umas uns você vocês
 é são não mais menos pode podem vai vão será serão está estão estar estavam
 the a an and are as at be been but by can could did do does doing for from had has have he her
 here hers him his how i if in into is it its me my no of on or our ours she should so than that
 their theirs them then there these they this those through to too up us very was we were what
 when where which while who why will with would you your yours
""".split())


def normalizar_token(token):
    """Converte para minúsculas e troca todo caractere não alfanumérico por espaço."""
    minusculo = token.lower()
    partes = []
    especiais = 0
    for caractere in minusculo:
        if unicodedata.category(caractere)[0] in {"L", "N"}:
            partes.append(caractere)
        else:
            partes.append(" ")
            especiais += 1
    return "".join(partes).split(), minusculo != token, especiais


def executar():
    _, linhas = ler_csv(ARQUIVO_TOKENIZADO)
    documentos = []
    frequencia_removidas = Counter()
    total_entrada = total_normalizado = total_depois = 0
    ocorrencias_minusculas = caracteres_especiais = 0
    vagas_normalizadas = vagas_com_stopwords = vagas_vazias_depois = 0

    for linha in linhas:
        tokens_entrada = (linha.get("tokens") or "").split()
        total_entrada += len(tokens_entrada)
        tokens_normalizados = []
        alterou_vaga = False
        stopwords_vaga = 0
        for token in tokens_entrada:
            partes, mudou_caixa, especiais = normalizar_token(token)
            ocorrencias_minusculas += mudou_caixa
            caracteres_especiais += especiais
            alterou_vaga |= mudou_caixa or especiais > 0
            tokens_normalizados.extend(partes)
        vagas_normalizadas += alterou_vaga
        total_normalizado += len(tokens_normalizados)

        mantidos = []
        for token in tokens_normalizados:
            if token in STOPWORDS:
                frequencia_removidas[token] += 1
                stopwords_vaga += 1
            else:
                mantidos.append(token)
        vagas_com_stopwords += stopwords_vaga > 0
        vagas_vazias_depois += not mantidos
        total_depois += len(mantidos)
        documentos.append({"tokens": " ".join(mantidos)})

    escrever_csv(ARQUIVO_SEM_STOPWORDS, ["tokens"], documentos)
    RELATORIO_STOPWORDS.parent.mkdir(parents=True, exist_ok=True)
    vocab_antes = {t for linha in linhas for t in (linha.get("tokens") or "").split()}
    vocab_depois = {t for doc in documentos for t in doc["tokens"].split()}
    tabela = "\n".join(
        f"| {termo} | {qtd} |" for termo, qtd in frequencia_removidas.most_common(20)
    ) or "| (nenhuma) | 0 |"
    removidos_stopwords = total_normalizado - total_depois
    RELATORIO_STOPWORDS.write_text(
        "# Etapa 6 — normalização e remoção de stopwords\n\n"
        "Ordem aplicada: converter tokens para minúsculas; remover pontuação, símbolos e demais "
        "caracteres não alfanuméricos, usando espaço como separador para não juntar palavras; "
        "remover stopwords em português e inglês. Letras acentuadas e números dentro de tokens "
        "são preservados. A entrada e a saída mantêm uma coluna (`tokens`) e uma linha por vaga.\n\n"
        f"- Vagas antes/depois: **{len(linhas)} / {len(documentos)}**\n"
        f"- Vagas com caixa ou caracteres especiais normalizados: **{vagas_normalizadas}**\n"
        f"- Tokens em minúsculas: **{ocorrencias_minusculas}**\n"
        f"- Caracteres especiais removidos: **{caracteres_especiais}**\n"
        f"- Tokens de entrada: **{total_entrada}**\n"
        f"- Tokens após normalização e antes de stopwords: **{total_normalizado}**\n"
        f"- Vagas com stopwords removidas: **{vagas_com_stopwords}**\n"
        f"- Stopwords removidas: **{removidos_stopwords}**\n"
        f"- Tokens finais: **{total_depois}**\n"
        f"- Vagas sem tokens finais: **{vagas_vazias_depois}**\n"
        f"- Vocabulário antes/depois: **{len(vocab_antes)} / {len(vocab_depois)}**\n"
        f"- CSV resultante: `{ARQUIVO_SEM_STOPWORDS.name}`\n\n"
        "## 20 stopwords mais removidas\n\n| Stopword | Ocorrências |\n|---|---:|\n"
        f"{tabela}\n",
        encoding="utf-8",
    )
    print(
        f"Etapa 6 concluída: {len(documentos)} vagas; "
        f"{caracteres_especiais} caracteres especiais removidos; "
        f"{removidos_stopwords} stopwords removidas; {total_depois} tokens finais."
    )
    print(f"CSV resultante: {ARQUIVO_SEM_STOPWORDS}")


if __name__ == "__main__":
    executar()
