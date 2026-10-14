# Etapa 16 — classificação de modalidade de trabalho

O campo de origem foi normalizado: `remote` → Remoto, `hybrid` → Híbrido e `on-site`/`onsite` → Presencial. Quando o campo está vazio, o texto da descrição só é usado se trouxer menção explícita; uma única modalidade encontrada é marcada como inferida, menções a mais de uma são mantidas como ambíguas e ausência de evidência permanece Não informado.

- Anúncios analisados: **1371**
- Campo estruturado: **481**
- Inferidos de menção textual única: **249**
- Menções textuais múltiplas/ambíguas: **57**
- Sem evidência textual: **584**
- CSV com rótulo, origem e evidências: `modalidade_classificada.csv`

## Contagens por classe

| Modalidade | Anúncios | Percentual do corpus |
|---|---:|---:|
| Não informado | 584 | 42.6% |
| Remoto | 368 | 26.8% |
| Presencial | 193 | 14.1% |
| Híbrido | 169 | 12.3% |
| Menções ambíguas | 57 | 4.2% |

As inferências se baseiam em correspondências literais na descrição; não equivalem à confirmação do empregador. A regra não força uma categoria quando o texto menciona modalidades distintas. ‘Não informado’ agora significa que o campo estava vazio e não foi encontrada evidência explícita única no texto. Consulte os registros individuais antes de usar a classificação como resultado substantivo.
