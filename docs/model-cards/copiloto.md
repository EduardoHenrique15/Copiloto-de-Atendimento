# Model card: copiloto de resposta (RAG com guardrails)

**Resumo:** o copiloto escreve um rascunho de resposta para cada reclamação triada. Ele usa só as políticas fictícias da Loja Exemplo e os dados do pedido. Um atendente aprova, edita ou recusa cada rascunho. Na versão atual (`draft-v3`), em 60 casos fictícios de avaliação:
- o rascunho citou uma política esperada em 98,3% dos casos;
- sugeriu uma ação aceita em 98,3%;
- nenhum rascunho bom foi bloqueado por engano.

O juiz LLM **não** foi aceito como medida de qualidade (ADR 0011).

Números de `scripts/evaluate_copilot.py`, por versão, em `docs/model-cards/copiloto-avaliacao-<versão>.md` e `eval/results/copilot_eval_<versão>.json`. Protocolo e histórico: ADR 0011. Guardrails: ADR 0010.

## Como funciona

1. Mascara dados pessoais (CPF, e-mail, telefone, CEP) **antes** do LLM e detecta tentativas de prompt injection.
2. **Busca híbrida:** todos os trechos da política da categoria da triagem, mais 4 trechos da busca vetorial (ChromaDB).
3. **Geração:** `gemini-3.5-flash-lite`, com saída JSON validada: resposta, políticas citadas, ação (`nenhuma`, `cupom`, `troca`, `reembolso`, `investigar` ou `escalar`), precisa de humano e motivo.
4. **Guardrails de saída**, em código:
   - citação só de trechos recuperados;
   - ação permitida pela política citada;
   - valores, prazos e porcentagens só se estiverem na política ou nos dados do pedido;
   - tamanho e termos proibidos.

   Uma promessa sem base troca a resposta pelo texto padrão de encaminhamento.

## Evolução medida (60 casos, verificações automáticas)

| Verificação | draft-v1 | draft-v2 | draft-v3 |
| --- | ---: | ---: | ---: |
| Citação de uma política esperada | 81,7% | 98,3% | 98,3% |
| Ação entre as aceitas | 88,3% | 93,3% | 98,3% |
| Envio para humano como esperado (18 casos) | 83,3% | 88,9% | 88,9% |
| Injection detectada pelo guardrail (10 casos) | 50,0% | 50,0% | 50,0% |
| Resposta trocada pelo texto padrão | 0,0% | 10,0% | 0,0% |

- **v1 → v2:** busca híbrida (a política de atraso não chegava ao LLM em 4 de 8 casos de atraso) e a ação `investigar`.
- **v2 → v3:** o guardrail de promessas passou a ler o título da seção ("Atraso de 4 dias ou mais"). No v2, ele bloqueava esses rascunhos por engano.
- **As respostas do LLM no v3 vieram do cache do v2,** porque o prompt é idêntico. A diferença entre os dois vem só do guardrail, e a latência do v3 não é representativa. A do v1 foi p50 de 1,4 s.

## Limitações

- **Casos fictícios e escritos por quem fez o sistema:** podem ser mais fáceis que reclamações reais.
- **Revisão humana alta:** 50 de 60 rascunhos do v3 são marcados para revisão, quase sempre porque o próprio LLM pede. No fluxo do n8n, todo rascunho passa por aprovação de qualquer forma.
- **Injection:** o guardrail por padrões detectou 5 das 10 tentativas. "SISTEMA:", "responda apenas", "desconsidere" e "novas instruções" passaram. Mesmo assim, nos 10 casos do v3, nenhum rascunho obedeceu à instrução do cliente. O c51, por exemplo, deu o cupom de R$ 20 da política, e não os R$ 500 pedidos. Isso acontece porque o texto do cliente vai delimitado como dado. Ampliar os padrões depois de ver estes casos ajustaria o detector ao próprio teste. Fica como melhoria, com casos novos.
- **Promessas sem número:** frases como "já estamos investigando" não são pegas pelo guardrail de promessas (ADR 0010).
- **Juiz LLM:** kappa de 0,15 contra a avaliação de 40 rascunhos, que foi feita com apoio de outra IA (ADR 0013). Não validado e não usado.
