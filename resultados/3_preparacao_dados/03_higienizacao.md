# Etapa 3 — higienização

Entrada: `C:\Users\bruno\Desktop\Mestrado\DADO - 7001 FUNDAMENTOS E FERRAMENTAS DE CIÊNCIA DE DADOS - 3F 2026\artigo_final\raspagem_vagas\vagas_unificado.csv`. Todas as quantidades são calculadas pelo script.

## Higienizações já realizadas durante a extração

O scraper `../vagas_scraper_unificado.py` converte descrições HTML em texto simples com `html_para_texto` (remove marcação, linhas vazias e linhas consecutivas repetidas); usa `normalizar` para comparação; com `filtrar_dev=True` (padrão), filtra relevância por palavras-chave no título e na descrição; e deduplica URLs por plataforma e na união final. O descarte por falta de conteúdo ocorre quando título e descrição estão ambos vazios, não quando somente a descrição está vazia.

Esta etapa não repete a conversão HTML nem remove novamente URLs duplicadas: audita as URLs residuais. Normalização de espaços para mineração, remoção de emojis/ícones, filtro de idioma, filtro por termos no título e duplicidade de descrição por empresa são aplicados após a extração.

| Higienização | Vagas antes | Vagas depois | Removidas | Vagas alteradas | Duplicidades detectadas | Regra |
| --- | --- | --- | --- | --- | --- | --- |
| Entrada | 2605 | 2605 | 0 | 0 | 0 | Base original, sem alteração |
| Normalização de espaços | 2605 | 2605 | 0 | 2184 | 0 | Consolida espaços, tabs e quebras de linha na descrição |
| Remoção de emojis e ícones | 2605 | 2605 | 0 | 703 | 0 | Remove caracteres Unicode pictográficos/decorativos de jobDescription e jobDescriptionHTML; preserva símbolos matemáticos e monetários |
| Exclusão sem descrição | 2605 | 2605 | 0 | 0 | 0 | Remove anúncios sem texto de descrição após normalização |
| Exclusão de idioma não português | 2605 | 1993 | 612 | 0 | 0 | Mantém apenas descrições classificadas como português; idioma indeterminado também é excluído |
| Filtro de profissão pelo título | 1993 | 1435 | 558 | 0 | 0 | Mantém títulos que contêm como palavra ou expressão pelo menos um termo configurado |
| Exclusão de descrição duplicada por empresa | 1435 | 1371 | 64 | 0 | 0 | Mantém primeira ocorrência com mesma empresa e descrição normalizadas; não compara quando empresa está vazia |
| Auditoria de URLs duplicadas | 1371 | 1371 | 0 | 0 | 0 | O scraper já deduplica URLs; esta etapa apenas contabiliza possíveis ocorrências residuais |

- Detecção do idioma: classificação local e determinística por frequência de marcadores lexicais em português, inglês, espanhol e francês. Idioma indeterminado também é excluído; revise a distribuição e os registros excluídos, pois essa heurística pode errar em textos curtos ou mistos.
- Distribuição de idioma: `distribuicao_idioma.csv`
- Títulos sem termo profissional: **558**
- Termos configurados: `desenvolvedor`, `desenvolvedora`, `desenvolvedores`, `desenvolvedoras`, `developer`, `developers`, `dev`, `programador`, `programadora`, `programadores`, `programadoras`, `programmer`, `programmers`, `engenheiro de software`, `engenheira de software`, `engenheiros de software`, `engenheiras de software`, `engenheiro(a) de software`, `software engineer`, `software engineers`
- Base higienizada: `vagas_higienizadas.csv` (1371 vagas)
- Excluídas com motivo: `vagas_excluidas_com_motivo.csv` (1234 vagas)
- Excluídas especificamente pelo filtro de idioma: `vagas_excluidas_filtro_idioma.csv` (612 vagas)
- Títulos sem correspondência: `titulos_sem_termo_profissao.csv`
- Log por regra: `log_higienizacao.csv`
