# Guia de rótulos das reclamações

Este guia define as 9 categorias da triagem (ADR 0007). Ele vale para a rotulagem humana (conjunto ouro), para o prompt do zero-shot e para a rotulagem fraca com LLM. **Os exemplos são fictícios**, escritos para este guia e inspirados no tipo de texto da base. Os textos reais da Olist não são copiados para o repositório.

## Como rotular

1. Leia o comentário inteiro.
2. Escolha **uma** categoria: a do problema **principal**, aquele que originou a reclamação ou que o cliente quer ver resolvido primeiro.
3. Se o comentário relata **mais de um problema**, marque "Mais de um problema" (tecla `m`).
4. Na dúvida entre duas categorias, use os **casos de fronteira** abaixo. Se ainda houver dúvida, pule (`p`) e volte depois.
5. Rotule pelo **texto**, não pelo que você imagina que aconteceu. Se o texto é vago ("Esperando solução!"), use `outro`.

**Atalhos da ferramenta:** `1` a `9` escolhem a categoria; `m` marca mais de um problema; `p` pula; `z` desfaz o último rótulo.

## Categorias

### 1. `atraso_entrega`: atraso na entrega
O produto **chegou depois do prazo**, **ainda não chegou** e o cliente está esperando (mesmo com o prazo vencido), ou o cliente reclama da **demora** ou do **prazo longo**, mesmo que tenha chegado no prazo.
- "Chegou, mas 10 dias depois do prometido."
- "Já passou do prazo e nada. Ainda vai chegar?"
- "Produto bom, só achei o prazo de entrega longo demais."
- "Demorou tanto que perdi a data do aniversário."

### 2. `nao_recebido`: não recebido
O pedido **consta como entregue**, mas o cliente diz que **não recebeu**, ou o produto **se perdeu** (extravio, devolvido ao remetente).
- "Consta como entregue, mas ninguém recebeu aqui em casa."
- "A transportadora disse que o pacote foi extraviado."
- "O rastreio diz que voltou para o remetente e eu não recebi nada."

*Regra revista em 01/11/2026 (ADR 0007, emenda).* Antes, "ainda não chegou e o prazo passou" era `nao_recebido`.

### 3. `produto_errado_ou_incompleto`: produto errado ou incompleto
Chegou **outro item** (outro modelo, cor ou tamanho escolhido), ou **faltou item** do pedido (entrega parcial).
- "Pedi o tamanho 40 e veio 42."
- "Comprei duas unidades e chegou só uma."
- "Pedi a capa preta e mandaram a vermelha."

### 4. `produto_defeituoso_ou_qualidade`: defeito, avaria ou qualidade
O item pedido chegou **quebrado, com defeito, avariado no transporte ou vazando**, ou o cliente acha a **qualidade ruim**.
- "Veio com a tampa quebrada."
- "Não liga, quero trocar."
- "Caixa toda amassada e o produto riscado."
- "Material muito fraco, rasgou na primeira semana."

### 5. `diferente_do_anuncio`: diferente do anúncio
Chegou o item que o cliente escolheu, mas ele **não corresponde ao anúncio**: medidas, material, composição, foto ou "original".
- "O anúncio dizia algodão e é poliéster."
- "As medidas são menores que as da descrição."
- "Na foto vinha com acessório, o meu veio sem."
- "Não é original como dizia o anúncio."

### 6. `atendimento_vendedor`: atendimento
A reclamação é **só** sobre o atendimento: ninguém responde, descaso, demora para resolver um chamado já aberto.
- "Abri um chamado há um mês e ninguém me responde."
- "Atendentes despreparados, não resolvem nada."

### 7. `cancelamento_ou_cobranca`: cancelamento ou cobrança
**Pedido cancelado** (inclusive por falta de estoque), **pedido de cancelamento**, **estorno** não feito ou **cobrança indevida**.
- "Cancelaram por falta de estoque e a cobrança continua na fatura."
- "Quero cancelar a compra e receber meu dinheiro."
- "Venderam sem ter o produto."

### 8. `outro`: outro
Reclamação real que não cabe nas categorias acima, ou texto vago demais.
- "Frete caríssimo."
- "Tive que buscar no correio."
- "Instalação muito difícil."
- "Esperando solução!"

### 9. `sem_problema`: sem problema
O comentário **não relata problema**: elogio ou comentário neutro, mesmo com nota 3.
- "Chegou antes do prazo, tudo certo."
- "Muito bom!"
- "Ainda não usei, está guardado na caixa."

## Casos de fronteira

| Situação | Rótulo | Por quê |
| --- | --- | --- |
| "Ainda não chegou" ou "estou aguardando", mesmo com o prazo vencido | `atraso_entrega` | O pedido ainda está a caminho. Se passar de 10 dias de atraso, a urgência sobe para alta. |
| "Chegou, mas atrasado" | `atraso_entrega` | O produto foi recebido. |
| "Marcado como entregue, mas não recebi" | `nao_recebido` | Vale o relato do cliente, não o status. |
| Extraviado ou devolvido ao remetente | `nao_recebido` | O pedido não vai mais chegar sozinho. |
| Chegou parte do pedido e "um dos produtos não veio" | `produto_errado_ou_incompleto` | Faltou item: é incompleto, mesmo que o cliente diga "não veio" ou "consta entregue". |
| Veio outra **cor** que a pedida | `produto_errado_ou_incompleto` | O cliente escolheu uma cor e recebeu outra. |
| A cor é diferente da **foto do anúncio** (cor única) | `diferente_do_anuncio` | O item é o pedido; o anúncio é que não condiz. |
| Chegou quebrado por causa da embalagem | `produto_defeituoso_ou_qualidade` | Avaria entra aqui, com ou sem culpa do transporte. |
| "Não é original" | `diferente_do_anuncio` | A promessa do anúncio não foi cumprida. |
| "Não serve no meu aparelho" sem promessa de compatibilidade | `outro` | Não é defeito nem anúncio errado. |
| Veio errado **e** ninguém responde | `produto_errado_ou_incompleto` + marcar "mais de um" | O atendimento só é principal quando aparece sozinho. |
| Atrasou **e** veio faltando item | `produto_errado_ou_incompleto` + marcar "mais de um" | O item faltando ainda precisa ser resolvido; o atraso já passou. |
| Pedido cancelado pela loja | `cancelamento_ou_cobranca` | Mesmo que o cliente diga "não recebi". |
| Elogio com uma ressalva leve ("só a caixa veio amassada") | categoria da ressalva | Existe um problema relatado, mesmo pequeno. |
| Menciona Procon, Reclame Aqui ou justiça | categoria do problema | A ameaça só afeta a **urgência**, não a categoria. |

## Urgência (calculada por regra, não rotulada)

A urgência é calculada por código (`copiloto.ai.taxonomy.urgency`) a partir da categoria, do texto e dos dados do pedido.

| Urgência | Quando |
| --- | --- |
| **alta** | Menção a Procon, Reclame Aqui, juizado, advogado, processo ou justiça; `nao_recebido`; `atraso_entrega` com mais de 10 dias de atraso; `cancelamento_ou_cobranca` (dinheiro do cliente envolvido) |
| **media** | `atraso_entrega` nos outros casos; `produto_errado_ou_incompleto`; `produto_defeituoso_ou_qualidade`; `diferente_do_anuncio` |
| **baixa** | `atendimento_vendedor`; `outro`; `sem_problema` |
