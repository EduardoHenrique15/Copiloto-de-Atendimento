# ADR 0007: taxonomia das reclamações

- Status: aceita
- Data: 2026-10-31

## Contexto

A especificação sugeria 8 categorias iniciais, a serem ajustadas depois da leitura de 100 comentários. Lemos 100 reclamações sorteadas de `fct_complaints` (estratificadas por nota e semestre, com a semente 7, por `scripts/sample_for_taxonomy.py`). Essas 100 ficam fora do conjunto ouro.

## O que a leitura mostrou

Contagem aproximada da leitura de trabalho. Não são rótulos e não entram em métricas.
- "Não recebi" foi o tema mais frequente (cerca de 25 de 100), muitas vezes com o pedido marcado como "entregue".
- Atendimento quase nunca aparece sozinho: vem junto de outro problema.
- Cerca de 15% dos comentários têm mais de um problema.
- Cerca de 5 comentários (nota 3) são elogios sem problema.
- Cancelamento, falta de estoque e estorno (cerca de 6) não tinham categoria.

## Decisão (aprovada pelo Eduardo)

1. **Nova categoria `sem_problema`**, para elogios e comentários neutros. Na triagem, vira "nenhuma ação".
2. **`cobranca_ou_pagamento` passa a ser `cancelamento_ou_cobranca`**, cobrindo cancelamento, falta de estoque, estorno e cobrança indevida.
3. **`produto_errado_ou_incompleto` continua uma categoria só**: separar deixaria cada parte com cerca de 10% dos casos, e a resposta é parecida.
4. **Um rótulo principal por comentário**, mais a marcação "mais de um problema", usada para medir a robustez da triagem.
5. **Urgência por regra em código**, não por rótulo humano (guia, seção "Urgência").

Categorias finais: `atraso_entrega`, `nao_recebido`, `produto_errado_ou_incompleto`, `produto_defeituoso_ou_qualidade`, `diferente_do_anuncio`, `atendimento_vendedor`, `cancelamento_ou_cobranca`, `outro`, `sem_problema`.

## Consequências

- Definições e casos de fronteira: `data/labels/guia-de-rotulos.md`. O código está em `src/copiloto/ai/taxonomy.py`.
- `atendimento_vendedor` deve ficar rara. Se tiver menos de cerca de 10 exemplos no ouro, a métrica por categoria será pouco confiável, e isso vai para as limitações.

## Emenda de 2026-11-01: fronteira entre `atraso_entrega` e `nao_recebido`

**Contexto.** Na validação da triagem (Fase 5, 100 itens do ouro), o zero-shot `triage-zs-v1` marcou como `nao_recebido` 6 das 19 reclamações que o Eduardo rotulou como `atraso_entrega`. Nas 6, o cliente diz que o produto ainda não chegou. O prompt seguia o guia ("ainda não chegou e o prazo passou" é `nao_recebido`). Os rótulos humanos seguiam outra leitura, que também era a do conjunto prata (`weak-v2`, ADR 0008).

**Decisão (aprovada pelo Eduardo).** Vale a leitura dos rótulos humanos, e o guia muda:
- `atraso_entrega`: chegou depois do prazo, **ainda não chegou e o cliente está esperando**, ou reclamação de demora ou prazo longo.
- `nao_recebido`: o pedido **consta como entregue** e o cliente diz que não recebeu, ou o produto **se perdeu** (extravio, devolvido ao remetente).
- Urgência: `nao_recebido` passa a ser sempre alta; `atraso_entrega` com mais de 10 dias de atraso também é alta. Assim, o pedido muito atrasado que ainda não chegou continua com urgência alta.

**Por quê.** A nova fronteira é mais fácil de aplicar: depende de o pedido constar como entregue ou perdido, não de quanto o prazo passou. Ela também separa ações diferentes: atraso pede acompanhar a entrega; não recebido pede investigação com a transportadora (política `pedido-nao-recebido`).

**Consequências.**
- Os rótulos do ouro não mudaram. Mudaram o guia, `src/copiloto/ai/taxonomy.py` (descrições e urgência) e os prompts: `triage-zs-v2` e `weak-v3`.
- A decisão foi tomada olhando a validação, o que o ADR 0009 permite. O teste continua fechado.
- O conjunto prata segue em `weak-v2`. Ele já tendia a esta leitura, então não será refeito agora.

## Emenda 2 de 2026-11-01: atraso e não recebido juntos na triagem

**Contexto.** Com o prompt `triage-zs-v2` (regra da emenda 1), o zero-shot passou a errar no sentido contrário: 8 dos 12 `nao_recebido` humanos saíram como `atraso_entrega` (F1 macro 0,505 e acurácia de 70,0%, contra 0,532 e 72,0% da v1). Lendo os erros, textos quase iguais receberam rótulos humanos diferentes: "estou no aguardo do meu produto" e "ainda estou aguardando o produto"; "mais de 40 dias e não foi entregue" e "mais de um mês e não recebi". Pelo texto, quando o produto ainda não chegou, nem o rotulador humano separa os dois de forma consistente. O que separa é um fato que não está no texto: se o pedido consta como entregue.

**Decisão (aprovada pelo Eduardo).**
1. **Na avaliação da triagem**, `atraso_entrega` e `nao_recebido` contam como uma categoria só, `problema_entrega` (8 categorias na métrica). Rótulos humanos e previsões são convertidos por código; ninguém rotula de novo.
2. **No serviço de triagem**, o status do pedido decide: se o pedido ainda está a caminho (`created`, `approved`, `processing`, `invoiced` ou `shipped`), `nao_recebido` vira `atraso_entrega`. Se consta entregue, vale o texto, que aí separa bem "chegou atrasado" de "consta entregue, mas não recebi".
3. As 9 categorias continuam no guia, na ferramenta de rotulagem, no conjunto prata e na API.

**Consequências.**
- Código: `TRIAGE_MERGE`, `triage_eval_key` e `resolve_delivery` em `src/copiloto/ai/taxonomy.py`; métricas em `ai/triage/compare.py`; regra aplicada em `services/triage.py`.
- A divisão final entre atraso e não recebido não é medida no ouro, porque os rótulos humanos dessa fronteira não são consistentes. Fica como limitação no model card.
- Sem número de pedido, o serviço mantém a categoria do texto.
- Decisão tomada na validação, como o ADR 0009 permite. O teste continua fechado.
