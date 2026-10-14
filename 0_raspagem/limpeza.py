# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 [NOME DO AUTOR]. Uso, cópia ou obra derivada exigem manter este aviso e citar a obra (ver NOTICE e CITATION.cff).
from pathlib import Path

import pandas as pd

# Caminho do arquivo de entrada e saída (ajuste se necessário)
DADOS_BRUTOS = Path(__file__).resolve().parent.parent / "dados" / "bruto"
ARQUIVO_ENTRADA = DADOS_BRUTOS / "vagas_unificado.csv"
ARQUIVO_SAIDA = DADOS_BRUTOS / "anuncio_vagas.csv"

# Colunas que devem ser mantidas (hardcoded)
COLUNAS_MANTER = [
    "platform",
    "jobUrl",
    "jobTitle",
    "jobDescription",
    "companyName",
    "companyLocation",
    "keywordsBusca",
    "dataColeta",
]

# Lê o CSV original
df = pd.read_csv(ARQUIVO_ENTRADA)

# Mantém apenas as colunas que existem no DataFrame (evita erro se alguma faltar)
colunas_existentes = [c for c in COLUNAS_MANTER if c in df.columns]
colunas_faltando = [c for c in COLUNAS_MANTER if c not in df.columns]

if colunas_faltando:
    print(f"Aviso: as colunas a seguir não foram encontradas no CSV original e serão ignoradas: {colunas_faltando}")

df_filtrado = df[colunas_existentes]

# Salva o novo CSV
df_filtrado.to_csv(ARQUIVO_SAIDA, index=False)

print(f"Arquivo salvo em: {ARQUIVO_SAIDA}")
print(f"Colunas mantidas: {list(df_filtrado.columns)}")
print(f"Total de linhas: {len(df_filtrado)}")