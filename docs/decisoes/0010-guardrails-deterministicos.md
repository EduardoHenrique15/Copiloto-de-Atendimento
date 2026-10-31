# ADR 0010: guardrails determinísticos em código

- Status: aceita
- Data: 2026-10-31

## Contexto

O copiloto gera rascunhos de resposta a clientes com um LLM. Os riscos são: vazar dados pessoais para o provedor, obedecer instruções escondidas no texto do cliente (prompt injection), prometer valores, prazos ou benefícios que a loja não oferece, sugerir ações sem base na política e escrever fora do tom.

## Opções

1. **Só instruções no prompt.** Barato, mas o LLM pode desobedecer, e não há como testar.
2. **Um segundo LLM como moderador.** Pega casos sutis, mas custa uma chamada a mais, é lento e também falha.
3. **Regras determinísticas em código, antes e depois do LLM**, mais aprovação humana.

## Decisão

Opção 3, com os 6 guardrails da especificação em `src/copiloto/ai/guardrails/`:

| # | Guardrail | Quando | Efeito |
| --- | --- | --- | --- |
| 1 | Dados pessoais | antes e depois | mascara CPF, e-mail, telefone e CEP |
| 2 | Prompt injection | antes | marca o caso e exige humano; o texto segue como dado delimitado |
| 3 | Ação permitida | depois | ação não permitida pelas políticas citadas vira `escalar` |
| 4 | Promessas | depois | valor, porcentagem ou prazo sem base: resposta trocada por encaminhamento |
| 5 | Citação obrigatória | depois | citação inventada é removida; sem citação válida, exige humano |
| 6 | Tamanho e tom | depois | acima de 1.200 caracteres ou com termo proibido, exige humano |

Todo disparo gera um evento `guardrail_triggered` com o tipo e um detalhe **sem o texto do cliente**. Nenhum rascunho é enviado sem aprovação humana (fluxo 2 do n8n).

## Consequências

- Regras simples deixam passar casos sutis (por exemplo, uma promessa sem número, como "vamos resolver hoje"). Isso fica nas limitações e é medido na avaliação da Fase 7.
- A detecção de injection por padrões gera falsos negativos para ataques criativos. A defesa principal continua sendo a delimitação do texto e a revisão humana.
- O mascaramento de telefone pode capturar outras sequências de 8 ou 9 dígitos. O custo de mascarar a mais é baixo.
