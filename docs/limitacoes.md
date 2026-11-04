# Limitações e melhorias futuras

Lista consolidada. Cada item aponta para onde o assunto está detalhado.

## Dados

- **Base histórica e pública** (Olist, 2016 a 2018). Não há tempo de atendimento, custo real de uma avaliação negativa nem efeito real de um contato. Esses valores são **premissas** (`docs/relatorio-impacto.md`).
- **Período de teste com volume baixo** no fim da base (setembro e outubro de 2018). Isso afeta o volume diário do A/B (`docs/experimento-ab.md`).
- **Os textos dos clientes não são redistribuídos** (licença). O CI roda sobre uma amostra fictícia.

## Rótulos e avaliação

- **O conjunto ouro e a avaliação dos 40 rascunhos foram feitos com apoio de outra IA** (ADR 0013). Os números da triagem medem a concordância com esses rótulos de referência, e não com um humano independente.
- **O kappa do rotulador consigo mesmo não foi medido.** A rodada 2 não foi feita.
- **Na fronteira entre atraso e não recebido, os rótulos são inconsistentes.** A métrica junta as duas categorias, e a separação depende do status do pedido, sem medição no ouro (ADR 0007).
- **O juiz LLM não foi validado** (kappa de 0,15). Ele não é usado como medida de qualidade.
- **Os casos do copiloto são fictícios** e foram escritos por quem fez o sistema, então podem ser mais fáceis que os reais.

## Modelos

- **Risco:** o ganho em reais depende do efeito do contato (premissa de 20%). Não há análise de equidade por estado (`docs/model-cards/risco.md`).
- **Causal:**
  - controla só os confundidores observados;
  - o E-value de 11,8 indica que um confundidor oculto precisaria ser muito forte para explicar o efeito.
- **Triagem:**
  - acurácia de 66,7% quando a reclamação tem mais de um problema;
  - as categorias raras (atendimento, outro) têm métricas instáveis;
  - a confiança do LLM não é calibrada;
  - o BERTimbau ficou fora da comparação.
- **Copiloto:**
  - 50 de 60 rascunhos vão para revisão humana, porque o próprio LLM pede;
  - o detector de injection pegou 5 das 10 tentativas, embora nenhum rascunho tenha obedecido;
  - promessas sem número ("já estamos investigando") não são detectadas.

## Operação

- **A aprovação pelo Telegram funciona só no PC onde o n8n roda.** O link do formulário é `localhost`, e o Telegram não aceita botão para `localhost` (ADR 0002). Para aprovar pelo celular, seria preciso um túnel ou uma URL pública.
- **Sem deploy em nuvem e sem alta disponibilidade:** tudo roda no Docker local.
- **O A/B sorteia por pedido, e não por cliente.** O mesmo cliente pode cair nos dois grupos (contaminação).

## Melhorias futuras

1. Rodar o A/B real e substituir a premissa de 20% pelo efeito medido.
2. Rotular 100 itens do teste sem apoio de IA e medir o kappa contra os rótulos atuais e contra o zero-shot.
3. Sortear o A/B por `customer_unique_id`.
4. Calibrar a confiança da triagem (por exemplo, com a frequência de acerto por faixa de confiança na validação).
5. Ampliar o detector de injection com casos novos, não os do teste.
6. Retreinar a triagem com as decisões dos atendentes.
7. Fazer deploy em nuvem, com URL pública e aprovação pelo celular.
