# Etapa 15 — avaliação e validação

## Métricas automatizadas

- Coerência LDA: **pendente** (execute a etapa 14 com `--modelagem` para gerar os tópicos).
- Métricas e estados registrados: **3** linhas em `metricas_modelos.csv`.
- Planilha para revisão humana: `amostra_revisao_humana.csv` (**30** registros na seleção desta execução; anotações existentes são preservadas).

UMass estima a coocorrência dos termos de maior peso no corpus; é uma medida interna e não determina sozinha o número ótimo de tópicos. Para selecioná-lo, compare uma grade de valores de K, coerência, estabilidade entre sementes e inspeção humana. Precisão/recall do léxico requerem decisões humanas em amostras de positivos e negativos; recall não pode ser estimado apenas revisando hits. Não há rótulos de referência para tópicos ou clusters, portanto não se reporta precisão/recall desses métodos.

## Protocolo Human-in-the-Loop

1. Dois avaliadores com conhecimento do domínio codificam independentemente a amostra estratificada da planilha. Para léxico, marcam o termo candidato como correto/incorreto e registram competências ausentes nos controles negativos. Para tópicos/clusters, descrevem o tema do anúncio e sua aderência ao grupo sugerido.
2. Compare as decisões, registre divergências e resolva-as por discussão ou terceiro avaliador. Calcule precisão do léxico como acertos/(acertos+falsos positivos); reporte denominador e protocolo. Estime recall somente com uma amostra de negativos revisada de modo exaustivo e denominador documentado.
3. Use codificação aberta e comparação constante para criar códigos, depois agrupe relações em categorias (codificação axial) e integre categorias centrais em memo. Revise categorias contra casos discrepantes e mantenha trilha de decisões. Só denomine o estudo Grounded Theory se a pergunta e o desenho realmente adotarem amostragem teórica, comparação constante e desenvolvimento de teoria; a revisão da amostra por si só não constitui Grounded Theory.
4. Anote mudanças na planilha de revisão; execuções futuras preservam respostas e acrescentam apenas novos exemplos. Documente avaliadores, treinamento, divergências, códigos, amostra e saturação/limites.

A seleção automatizada é intencional e voltada a exemplos representativos, não uma amostra probabilística para estimar prevalência. Não generalize frequências de anotação sem desenho amostral apropriado.
