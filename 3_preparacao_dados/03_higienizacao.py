# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Bruno Proença de Souza. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
"""Etapa 3 do fluxo: higieniza a base e contabiliza cada regra aplicada."""
import re
import unicodedata
from collections import Counter

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # permite `from comum...`
from comum.config import (
    ARQUIVO_BRUTO, ARQUIVO_EXCLUIDOS, ARQUIVO_EXCLUIDOS_IDIOMA,
    ARQUIVO_HIGIENIZADO,
    ARQUIVO_DISTRIBUICAO_IDIOMA, ARQUIVO_TITULOS_SEM_TERMO,
    COLUNA_TEXTO, COLUNA_URL, LOG_HIGIENIZACAO_CSV,
    MARCADORES_IDIOMA, RELATORIO_HIGIENIZACAO, TERMOS_PROFISSAO_TITULO,
)
from comum.io_utils import ler_csv, escrever_csv, markdown_tabela


def registrar(etapa, regra, antes, depois, alterados=0, detectadas=0):
    return {
        "etapa": etapa, "regra_aplicada": regra,
        "vagas_antes": antes, "vagas_depois": depois,
        "vagas_removidas": antes - depois,
        "vagas_com_valor_alterado": alterados,
        "duplicidades_ou_ocorrencias_detectadas": detectadas,
    }


def normalizar_para_busca(texto):
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto.casefold()).strip()


def titulo_corresponde(titulo):
    normalizado = normalizar_para_busca(titulo)
    for termo in TERMOS_PROFISSAO_TITULO:
        termo_normalizado = normalizar_para_busca(termo)
        palavras = r"\s+".join(re.escape(p) for p in termo_normalizado.split())
        if re.search(r"(?<!\w)" + palavras + r"(?!\w)", normalizado):
            return True
    return False


def detectar_idioma_principal(texto):
    """Classificação determinística por marcadores lexicais configurados."""
    tokens = re.findall(r"[a-z]+", normalizar_para_busca(texto))
    if not tokens:
        return "indeterminado"
    frequencias = Counter(tokens)
    pontuacoes = {
        idioma: sum(frequencias[palavra] for palavra in marcadores)
        for idioma, marcadores in MARCADORES_IDIOMA.items()
    }
    idioma, pontuacao = max(pontuacoes.items(), key=lambda item: item[1])
    return idioma if pontuacao else "indeterminado"


def normalizar_conteudo(texto):
    return re.sub(r"\s+", " ", normalizar_para_busca(texto)).strip()


def remover_emojis_icones(texto, colapsar_espacos=True):
    """Remove pictogramas/símbolos decorativos sem apagar matemática ou moedas."""
    resultado = []
    for caractere in texto:
        codigo = ord(caractere)
        categoria = unicodedata.category(caractere)
        eh_seletor_ou_juncao = (
            codigo in {0x200D, 0xFE0E, 0xFE0F, 0x20E3}
            or 0xE0020 <= codigo <= 0xE007F
        )
        if categoria in {"So", "Sk"} or eh_seletor_ou_juncao:
            continue
        resultado.append(caractere)
    texto_saida = "".join(resultado)
    return " ".join(texto_saida.split()) if colapsar_espacos else texto_saida


def executar():
    colunas, linhas = ler_csv(ARQUIVO_BRUTO)
    log = [registrar("Entrada", "Base original, sem alteração", len(linhas), len(linhas))]
    excluidos = []

    antes = len(linhas)
    preparados = []
    textos_alterados = 0
    for linha in linhas:
        nova = dict(linha)
        original = linha.get(COLUNA_TEXTO) or ""
        limpo = " ".join(original.split())
        textos_alterados += limpo != original
        nova[COLUNA_TEXTO] = limpo
        nova["jobDescription_limpa"] = limpo
        preparados.append(nova)
    log.append(registrar(
        "Normalização de espaços",
        "Consolida espaços, tabs e quebras de linha na descrição",
        antes, len(preparados), textos_alterados,
    ))

    antes = len(preparados)
    descricoes_alteradas = 0
    for linha in preparados:
        alterada = False
        texto = linha.get(COLUNA_TEXTO) or ""
        texto_sem_icones = remover_emojis_icones(texto)
        if texto_sem_icones != texto:
            linha[COLUNA_TEXTO] = texto_sem_icones
            alterada = True
        html = linha.get("jobDescriptionHTML") or ""
        html_sem_icones = remover_emojis_icones(html, colapsar_espacos=False)
        if html_sem_icones != html:
            linha["jobDescriptionHTML"] = html_sem_icones
            alterada = True
        # Mantém o campo explicitamente destinado à mineração sincronizado com
        # o campo principal já higienizado, sem emojis/ícones.
        linha["jobDescription_limpa"] = texto_sem_icones
        descricoes_alteradas += alterada
    log.append(registrar(
        "Remoção de emojis e ícones",
        "Remove caracteres Unicode pictográficos/decorativos de jobDescription e jobDescriptionHTML; preserva símbolos matemáticos e monetários",
        antes, len(preparados), descricoes_alteradas,
    ))

    antes = len(preparados)
    mantidos = []
    for linha in preparados:
        if not linha["jobDescription_limpa"]:
            excluidos.append({**linha, "motivo_exclusao": "descrição vazia"})
        else:
            mantidos.append(linha)
    preparados = mantidos
    log.append(registrar(
        "Exclusão sem descrição",
        "Remove anúncios sem texto de descrição após normalização",
        antes, len(preparados),
    ))

    antes = len(preparados)
    idiomas = Counter()
    excluidos_idioma = []
    mantidos = []
    for linha in preparados:
        idioma = detectar_idioma_principal(linha["jobDescription_limpa"])
        nova = {**linha, "idioma_detectado": idioma}
        idiomas[idioma] += 1
        if idioma == "português":
            mantidos.append(nova)
        else:
            vaga_excluida = {
                **nova,
                "motivo_exclusao": f"idioma principal não português ({idioma})",
            }
            excluidos.append(vaga_excluida)
            excluidos_idioma.append(vaga_excluida)
    preparados = mantidos
    log.append(registrar(
        "Exclusão de idioma não português",
        "Mantém apenas descrições classificadas como português; idioma indeterminado também é excluído",
        antes, len(preparados),
    ))

    antes = len(preparados)
    mantidos = []
    titulos_sem_termo = Counter()
    for linha in preparados:
        titulo = (linha.get("jobTitle") or "").strip()
        if titulo_corresponde(titulo):
            mantidos.append(linha)
        else:
            titulos_sem_termo[titulo or "(título vazio)"] += 1
            excluidos.append({**linha, "motivo_exclusao": "título sem termo da profissão-alvo"})
    preparados = mantidos
    log.append(registrar(
        "Filtro de profissão pelo título",
        "Mantém títulos que contêm como palavra ou expressão pelo menos um termo configurado",
        antes, len(preparados),
    ))

    antes = len(preparados)
    vistos_empresa_descricao = set()
    mantidos = []
    for linha in preparados:
        empresa = normalizar_conteudo(linha.get("companyName") or "")
        descricao = normalizar_conteudo(linha.get("jobDescription_limpa") or "")
        chave = (empresa, descricao)
        if empresa and descricao and chave in vistos_empresa_descricao:
            excluidos.append({
                **linha,
                "motivo_exclusao": "descrição duplicada para a mesma empresa",
            })
        else:
            if empresa and descricao:
                vistos_empresa_descricao.add(chave)
            mantidos.append(linha)
    preparados = mantidos
    log.append(registrar(
        "Exclusão de descrição duplicada por empresa",
        "Mantém primeira ocorrência com mesma empresa e descrição normalizadas; não compara quando empresa está vazia",
        antes, len(preparados),
    ))

    antes = len(preparados)
    vistos = set()
    urls_duplicadas = 0
    for linha in preparados:
        url = (linha.get(COLUNA_URL) or "").strip()
        chave = url.casefold() if url else ""
        if chave and chave in vistos:
            urls_duplicadas += 1
        else:
            if chave:
                vistos.add(chave)
    log.append(registrar(
        "Auditoria de URLs duplicadas",
        "O scraper já deduplica URLs; esta etapa apenas contabiliza possíveis ocorrências residuais",
        antes, antes, detectadas=urls_duplicadas,
    ))

    colunas_saida = colunas + [c for c in ("jobDescription_limpa", "idioma_detectado") if c not in colunas]
    escrever_csv(ARQUIVO_HIGIENIZADO, colunas_saida, preparados)
    escrever_csv(ARQUIVO_EXCLUIDOS, colunas_saida + ["motivo_exclusao"], excluidos)
    escrever_csv(ARQUIVO_EXCLUIDOS_IDIOMA, colunas_saida + ["motivo_exclusao"], excluidos_idioma)
    escrever_csv(ARQUIVO_TITULOS_SEM_TERMO, ["titulo", "quantidade"],
                 [{"titulo": t, "quantidade": n} for t, n in titulos_sem_termo.most_common()])
    escrever_csv(ARQUIVO_DISTRIBUICAO_IDIOMA, ["idioma_detectado", "quantidade"],
                 [{"idioma_detectado": idioma, "quantidade": n}
                  for idioma, n in idiomas.most_common()])
    escrever_csv(LOG_HIGIENIZACAO_CSV, list(log[0]), log)

    tabela = markdown_tabela(
        ["Higienização", "Vagas antes", "Vagas depois", "Removidas", "Vagas alteradas", "Duplicidades detectadas", "Regra"],
        [(r["etapa"], r["vagas_antes"], r["vagas_depois"], r["vagas_removidas"],
          r["vagas_com_valor_alterado"], r["duplicidades_ou_ocorrencias_detectadas"],
          r["regra_aplicada"]) for r in log],
    )
    RELATORIO_HIGIENIZACAO.parent.mkdir(parents=True, exist_ok=True)
    RELATORIO_HIGIENIZACAO.write_text(
        "# Etapa 3 — higienização\n\n"
        f"Entrada: `{ARQUIVO_BRUTO}`. Todas as quantidades são calculadas pelo script.\n\n"
        "## Higienizações já realizadas durante a extração\n\n"
        "O scraper `0_raspagem/vagas_scraper_unificado.py` converte descrições HTML em texto simples com `html_para_texto` (remove marcação, linhas vazias e linhas consecutivas repetidas); usa `normalizar` para comparação; com `filtrar_dev=True` (padrão), filtra relevância por palavras-chave no título e na descrição; e deduplica URLs por plataforma e na união final. O descarte por falta de conteúdo ocorre quando título e descrição estão ambos vazios, não quando somente a descrição está vazia.\n\n"
        "Esta etapa não repete a conversão HTML nem remove novamente URLs duplicadas: audita as URLs residuais. Normalização de espaços para mineração, remoção de emojis/ícones, filtro de idioma, filtro por termos no título e duplicidade de descrição por empresa são aplicados após a extração.\n\n"
        f"{tabela}\n\n"
        "- Detecção do idioma: classificação local e determinística por frequência de marcadores lexicais em português, inglês, espanhol e francês. Idioma indeterminado também é excluído; revise a distribuição e os registros excluídos, pois essa heurística pode errar em textos curtos ou mistos.\n"
        f"- Distribuição de idioma: `{ARQUIVO_DISTRIBUICAO_IDIOMA.name}`\n"
        f"- Títulos sem termo profissional: **{sum(titulos_sem_termo.values())}**\n"
        f"- Termos configurados: {', '.join(f'`{t}`' for t in TERMOS_PROFISSAO_TITULO)}\n"
        f"- Base higienizada: `{ARQUIVO_HIGIENIZADO.name}` ({len(preparados)} vagas)\n"
        f"- Excluídas com motivo: `{ARQUIVO_EXCLUIDOS.name}` ({len(excluidos)} vagas)\n"
        f"- Excluídas especificamente pelo filtro de idioma: `{ARQUIVO_EXCLUIDOS_IDIOMA.name}` ({len(excluidos_idioma)} vagas)\n"
        f"- Títulos sem correspondência: `{ARQUIVO_TITULOS_SEM_TERMO.name}`\n"
        f"- Log por regra: `{LOG_HIGIENIZACAO_CSV.name}`\n",
        encoding="utf-8",
    )
    print(f"Higienização concluída: {len(preparados)} vagas mantidas; {len(excluidos)} excluídas.")


if __name__ == "__main__":
    executar()
