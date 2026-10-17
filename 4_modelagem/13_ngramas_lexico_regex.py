# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Bruno Proença de Souza. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Etapa 13: n-gramas, léxico de domínio e extrações explícitas por regex."""
import csv
import re
import unicodedata
from collections import Counter

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import (
    ARQUIVO_LEXICO, ARQUIVO_LEXICO_RESUMO, ARQUIVO_NGRAMAS, ARQUIVO_PREPARADO,
    ARQUIVO_REGEX, RELATORIO_ANALISE_TEXTUAL, SAIDA,
)
from comum.io_utils import ler_csv

# Léxico inicial e editável. É uma lista-semente, não uma taxonomia validada.
LEXICO = {
    "tecnologia": "python,java,javascript,typescript,node.js,react,angular,vue,sql,postgresql,mysql,mongodb,redis,kafka,docker,kubernetes,aws,azure,gcp,terraform,git,github,linux,api,rest,graphql,spring,django,flask,fastapi,c++,c#,.net,php,ruby,go,rust,html,css,ci/cd",
    "hard_skill": "desenvolvimento de software,engenharia de software,desenvolvimento backend,desenvolvimento frontend,desenvolvimento full stack,modelagem de dados,análise de dados,ciência de dados,machine learning,inteligência artificial,aprendizado de máquina,arquitetura de software,integração de sistemas,teste de software,controle de versão,metodologia ágil,computação em nuvem,segurança da informação",
    "soft_skill": "comunicação,trabalho em equipe,liderança,proatividade,autonomia,resolução de problemas,pensamento crítico,organização,adaptabilidade,criatividade, colaboração",
    "formacao": "graduação,bacharelado,licenciatura,tecnólogo,pós-graduação,especialização,mestrado,doutorado,ensino superior,ciência da computação,sistemas de informação,engenharia da computação,análise e desenvolvimento de sistemas",
}
STOPWORDS_RELATORIO = set("a ao aos as com como da das de do dos e em entre na nas no nos o os ou para pela pelo por que se sem um uma uns umas the and for from in of on or the to with".split())

def normalizar(texto):
    texto = unicodedata.normalize("NFKD", (texto or "").casefold())
    return "".join(ch for ch in texto if not unicodedata.combining(ch))

def tokens(texto):
    return re.findall(r"(?i)(?:\.net|c\+\+|c#|ci/cd|[\w]+(?:[./+#-][\w+#-]+)*)", texto or "")

def executar():
    colunas, vagas = ler_csv(ARQUIVO_PREPARADO)
    ngramas = Counter()
    ngramas_docs = Counter()
    regex_rows = []
    lex_rows = []
    lex_totais = Counter()
    lex_docs = Counter()
    padrao_anos = re.compile(
        r"(?i)(?:(?:mínimo|minimo|pelo menos|at least)\s*)?(\d{1,2})\s*(?:\+\s*)?(?:anos?|years?)\s*(?:de|of)?\s*(?:experiência|experiencia|experience)?"
        r"|(?:experiência|experiencia|experience)\s*(?:de|of)?\s*(\d{1,2})\s*(?:\+\s*)?(?:anos?|years?)"
        r"|(\d{1,2})\s*[-–a]\s*(\d{1,2})\s*(?:anos?|years?)\s*(?:de|of)?\s*(?:experiência|experiencia|experience)"
    )
    modalidade = re.compile(r"(?i)\b(remot[oa]s?|remote|h[ií]brid[oa]s?|hybrid|presenciais?|onsite|on-site)\b")

    for doc_id, vaga in enumerate(vagas, 1):
        for campo, origem in (("jobTitle", "titulo"), ("jobDescription_limpa", "descricao")):
            bruto = vaga.get(campo) or ""
            toks = [normalizar(t) for t in tokens(bruto)]
            seen = set()
            for n in (1, 2, 3):
                for i in range(len(toks) - n + 1):
                    termo = " ".join(toks[i:i+n])
                    ngramas[(origem, n, termo)] += 1
                    seen.add((origem, n, termo))
            ngramas_docs.update(seen)

        descricao = vaga.get("jobDescription_limpa") or ""
        texto_norm = normalizar((vaga.get("jobTitle") or "") + " " + descricao)
        for categoria, termos_csv in LEXICO.items():
            for termo in (t.strip() for t in termos_csv.split(",") if t.strip()):
                termo_norm = normalizar(termo)
                ocorrencias = len(re.findall(r"(?<!\w)" + re.escape(termo_norm) + r"(?!\w)", texto_norm))
                if ocorrencias:
                    lex_rows.append([doc_id, vaga.get("platform", ""), vaga.get("jobTitle", ""), categoria, termo, ocorrencias])
                    lex_totais[(categoria, termo)] += ocorrencias
                    lex_docs[(categoria, termo)] += 1

        trechos = [("descricao", descricao)]
        for campo in ("jobTitle", "jobLocationType"):
            if vaga.get(campo):
                trechos.append((campo, vaga[campo]))
        for origem, texto in trechos:
            for m in padrao_anos.finditer(texto or ""):
                nums = [x for x in m.groups() if x]
                regex_rows.append([doc_id, vaga.get("platform", ""), vaga.get("jobTitle", ""), "anos_experiencia", origem, m.group(0), "-".join(nums)])
            for m in modalidade.finditer(texto or ""):
                regex_rows.append([doc_id, vaga.get("platform", ""), vaga.get("jobTitle", ""), "modalidade", origem, m.group(0), normalizar(m.group(0))])

    SAIDA.mkdir(parents=True, exist_ok=True)
    with ARQUIVO_NGRAMAS.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["campo", "n", "termo", "ocorrencias", "documentos"])
        for (origem, n, termo), total in ngramas.most_common():
            w.writerow([origem, n, termo, total, ngramas_docs[(origem, n, termo)]])
    with ARQUIVO_LEXICO.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["documento_id", "platform", "jobTitle", "categoria", "termo", "ocorrencias"]); w.writerows(lex_rows)
    with ARQUIVO_LEXICO_RESUMO.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["categoria", "termo", "ocorrencias", "documentos"])
        for (categoria, termo), total in lex_totais.most_common():
            w.writerow([categoria, termo, total, lex_docs[(categoria, termo)]])
    with ARQUIVO_REGEX.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["documento_id", "platform", "jobTitle", "tipo", "origem", "trecho", "valor_normalizado"]); w.writerows(regex_rows)
    top = []
    for n in (1, 2, 3):
        itens = [item for item in ngramas.items() if item[0][1] == n]
        if n == 1:
            itens = [item for item in itens if item[0][2] not in STOPWORDS_RELATORIO]
        top.extend(sorted(itens, key=lambda item: item[1], reverse=True)[:10])
    tabela = "\n".join(f"| {campo} | {n} | {termo} | {total} | {ngramas_docs[(campo, n, termo)]} |" for (campo, n, termo), total in top)
    RELATORIO_ANALISE_TEXTUAL.write_text(
        "# Etapa 13 — n-gramas, léxico de domínio e regex\n\n"
        f"N-gramas são contados separadamente em títulos e descrições para n=1, 2 e 3. Foram analisadas {len(vagas)} vagas.\n\n"
        "## Dez combinações mais frequentes por tamanho\n\nUnigramas comuns de função (stopwords) foram omitidos apenas deste resumo; o CSV completo mantém todas as contagens.\n\n| Campo | n | N-grama | Ocorrências | Documentos |\n|---|---:|---|---:|---:|\n"
        f"{tabela}\n\n"
        f"O léxico-semente identificou {len(lex_rows)} combinações vaga-termo em {len(lex_totais)} termos/categorias; "
        f"as regex registraram {len(regex_rows)} ocorrências. Saídas: `{ARQUIVO_NGRAMAS.name}`, "
        f"`{ARQUIVO_LEXICO.name}`, `{ARQUIVO_LEXICO_RESUMO.name}` e `{ARQUIVO_REGEX.name}`.\n\n"
        "O léxico é inicial, configurável no script e requer revisão/validação manual antes de inferir competências. "
        "As regex indicam apenas correspondências textuais e não garantem que o requisito foi corretamente interpretado.\n",
        encoding="utf-8",
    )
    print(f"N-gramas e extrações concluídos: {len(vagas)} vagas; {len(ngramas)} n-gramas distintos; {len(regex_rows)} ocorrências regex")

if __name__ == "__main__":
    executar()
