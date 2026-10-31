# ADR 0008: rotulagem fraca com LLM em lotes

- Status: aceita
- Data: 2026-10-31

## Contexto

A triagem por embeddings + regressão logística (e o BERTimbau) precisa de alguns milhares de exemplos rotulados para treino. O conjunto ouro humano tem 300 e é reservado para avaliação. O LLM gratuito (`gemini-3.5-flash-lite`) permite 15 chamadas por minuto e 500 por dia.

## Decisão

1. **Conjunto prata de 4.000 reclamações**, amostra estratificada por nota e semestre (semente 99), **excluindo** as 300 do ouro e as 100 lidas para a taxonomia.
2. **Lotes de 20 comentários por chamada**: cerca de 200 chamadas, que cabem num dia e a 12 chamadas por minuto, abaixo do limite de 15.
3. **Saída JSON validada por Pydantic**: exatamente um item por comentário, categoria da taxonomia. Lote inválido é refeito uma vez e, se falhar de novo, é registrado e pulado.
4. **Cache em disco** por conteúdo da chamada e **gravação incremental** em `data/labels/silver.csv` (só ids e rótulos). O script retoma de onde parou.
5. **Estimativa antes de rodar** (`--estimate`) e **piloto de 1 chamada** antes do lote completo, com autorização do Eduardo em cada etapa.
6. O prompt usa as definições de `copiloto.ai.taxonomy` (as mesmas do guia) e tem versão (`weak-v1`) registrada em cada rótulo.

## Alternativas

- **Um comentário por chamada:** mais fiel, mas leva 8 dias de cota.
- **Lotes de 50 ou mais:** menos chamadas, mais risco de o modelo pular ou trocar itens.

## Consequências

- A qualidade do prata é medida indiretamente: a triagem treinada com ele é avaliada no ouro (Fase 5). Se a concordância do zero-shot com o ouro for baixa, o prata também será suspeito.
- O efeito do lote na qualidade não é medido separadamente. Fica como limitação.

## Piloto (2026-10-31)

Uma chamada autorizada com 20 comentários (`weak-v1`). Funcionou sem lote inválido e usou 1.476 tokens de entrada e 793 de saída (a estimativa previa cerca de 240 de saída, provavelmente por tokens de raciocínio do modelo). Na revisão manual, o LLM marcou "um dos produtos não veio, consta entregue" como `nao_recebido`, quando o guia indica `produto_errado_ou_incompleto`.

Ajustes antes do lote completo:
- regra de fronteira para item faltando no prompt (`weak-v2`) e no guia;
- estimativa de saída de 40 tokens por item;
- os 20 rótulos do piloto (`weak-v1`) foram descartados, para o conjunto prata ter uma única versão de prompt.

## Execução do lote completo (2026-10-31, `weak-v2`)

- 4.000 de 4.000 reclamações rotuladas, sem nenhum lote inválido.
- A primeira execução parou em 1.300 por um erro 503 (servidor sobrecarregado) que o cliente ainda não repetia. O cliente passou a repetir erros 5xx, e a segunda execução retomou do 1.301 sem refazer nada (gravação incremental).
- Uso registrado (só a segunda execução, 135 chamadas): 192.704 tokens de entrada e 105.555 de saída. Os tokens das 65 chamadas da primeira execução não foram registrados, porque o relatório só é gravado no fim do script. Melhoria futura: registrar o uso a cada chamada (tabela `llm_calls`, Fase 6).
- Custo real: R$ 0 (plano gratuito). Distribuição dos rótulos e taxa de "mais de um problema" (27,0%) em `eval/results/weak_label_run.json`.
- `atendimento_vendedor` ficou com 74 exemplos (1,9%), a categoria mais rara, como previsto no ADR 0007.

## Revisão manual de 40 rótulos do lote (`weak-v2`)

- A regra do item faltando funcionou (o caso do piloto agora sai `produto_errado_ou_incompleto`).
- Erro sistemático encontrado: quando o produto **ainda não chegou e o prazo já passou** ("consta em trânsito há 19 dias", "a previsão era dia 23, hoje é 29 e nada"), o LLM tende a marcar `atraso_entrega`, enquanto o guia indica `nao_recebido`. Foram 2 casos claros e 1 ambíguo em 40.
- Decisão: não rotular de novo agora. A confusão `atraso_entrega` × `nao_recebido` será medida contra o ouro humano na Fase 5. Se ela for relevante, um prompt `weak-v3` com essa regra explícita refaz o conjunto prata (cerca de 200 chamadas, com nova autorização).
