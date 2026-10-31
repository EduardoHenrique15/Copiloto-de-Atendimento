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
