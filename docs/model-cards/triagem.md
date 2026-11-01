# Model card: triagem de reclamações

**Resumo:** a triagem lê o texto de uma reclamação e escolhe uma das categorias da taxonomia (ADR 0007). Em produção, um LLM classifica sem treino (zero-shot, prompt `triage-zs-v2`). Se ele falhar, um modelo local de embeddings com regressão logística assume. No teste com 200 reclamações rotuladas à mão, o zero-shot teve F1 macro de 0,738 e acurácia de 83,5%, contra 0,639 e 71,5% do modelo local. Com o limiar de confiança fixado na validação, 75% dos tickets são classificados automaticamente, com 92,0% de acerto. Os outros 25% vão para revisão humana.

Todos os números vêm de `scripts/evaluate_triage.py`. As tabelas completas estão em [`triagem-resultados.md`](triagem-resultados.md) (teste) e [`triagem-validacao.md`](triagem-validacao.md) (validação). Os números brutos estão em `eval/results/triage_comparison_test.json`. O protocolo e a decisão estão no ADR 0009.

## Detalhes do modelo

| Item | Principal | Reserva |
| --- | --- | --- |
| Abordagem | LLM zero-shot (`gemini-3.5-flash-lite`) | Embeddings (`EMBEDDING_MODEL`) + regressão logística |
| Treino | Nenhum. O prompt usa as definições e os casos de fronteira do guia. | 4.000 rótulos do LLM (conjunto prata, `weak-v2`) |
| Saída | Categoria, confiança declarada pelo LLM e "mais de um problema" | Categoria e probabilidade |
| Limiar para classificar sozinho | 0,95 | 0,75 |
| Quando é usado | Sempre | LLM indisponível, cota esgotada ou resposta inválida duas vezes |
| Código | `ai/triage/zero_shot.py` | `ai/triage/embeddings_lr.py`, `ai/triage/fallback.py` |

Depois do modelo, duas regras em código completam a triagem:
- **Status do pedido** (`resolve_delivery`): se o pedido ainda está a caminho, `nao_recebido` vira `atraso_entrega`.
- **Urgência** (`urgency`): calculada por regra, a partir da categoria, de termos como Procon e do atraso.

## Uso pretendido

- **Para que serve:** organizar a fila de atendimento por tipo de problema e urgência, e escolher as políticas que o copiloto consulta.
- **O que não faz:** não responde ao cliente nem decide reembolso ou troca. Ticket com confiança abaixo do limiar vai para uma pessoa.

## Dados de avaliação

- **Conjunto ouro:** 300 reclamações rotuladas pelo Eduardo (rodada 1), sorteadas de forma estratificada de `fct_complaints`. São 100 de validação e 200 de teste.
- **Uso de cada parte:** a validação serviu para corrigir o prompt e escolher limiares. O teste rodou **uma única vez**, depois da decisão de produção.
- **Categorias na métrica:** 8. `atraso_entrega` e `nao_recebido` contam juntas como `problema_entrega` (ADR 0007, emenda 2), porque, pelo texto, nem o rotulador humano as separa de forma consistente.

## Resultados no teste (200 itens)

| Abordagem | F1 macro | Acurácia | Automáticos | Acerto nos automáticos | p50 | p95 | R$ / 1.000 tickets |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Zero-shot** (produção) | **0,738** | **83,5%** | 75% | 92,0% | 1.023 ms | 5.039 ms | R$ 1,64 |
| Embeddings + LR (reserva) | 0,639 | 71,5% | 47% | 86,2% | 26 ms | 37 ms | R$ 0,00 |

- **Custo do zero-shot:** média de 711 tokens de entrada e 36 de saída por ticket, a preço pago de referência (ADR 0001). No plano gratuito, o custo real foi R$ 0.
- **Custo do modelo local:** tempo de CPU vezes uma premissa de R$ 0,50 por hora (ADR 0009). O resultado é próximo de zero.
- **Latência do zero-shot:** o p95 do teste (5,0 s) foi bem maior que o da validação (1,8 s). A causa provável são novas tentativas por limite de taxa durante a execução em lote.

**F1 por categoria (zero-shot):**

| Categoria | F1 | Suporte |
| --- | ---: | ---: |
| problema_entrega | 0,90 | 66 |
| produto_errado_ou_incompleto | 0,92 | 43 |
| produto_defeituoso_ou_qualidade | 0,81 | 33 |
| diferente_do_anuncio | 0,76 | 17 |
| atendimento_vendedor | 0,50 | 6 |
| cancelamento_ou_cobranca | 0,70 | 16 |
| outro | 0,43 | 7 |
| sem_problema | 0,87 | 12 |

**Robustez (zero-shot):**

| Fatia | n | Acurácia |
| --- | ---: | ---: |
| Um problema só | 140 | 90,7% |
| Mais de um problema | 60 | 66,7% |
| Curtos (até 30 caracteres) | 26 | 80,8% |

## Validação e teste

Na validação (100 itens), o zero-shot teve acurácia de 78,0%, e o embeddings, 67,0%. No teste, os dois foram melhores: 83,5% e 71,5%. A ordem entre as abordagens se manteve. Com 100 itens, a validação tem bastante variação: 1 ticket vale 1 ponto percentual. Por isso, o número publicado é o do teste.

## Limitações

- **Atraso × não recebido:** a separação final entre os dois depende do status do pedido e não foi medida no ouro, porque os rótulos humanos dessa fronteira não são consistentes. Sem número de pedido, vale a categoria do texto.
- **Categorias raras:** `atendimento_vendedor` (6 casos) e `outro` (7) têm F1 baixo e intervalo muito largo. O zero-shot confunde atendimento com cancelamento (3 de 6). `atendimento_vendedor` só vale quando o atendimento é o único problema, então ela tende a ser rara.
- **Mais de um problema:** a acurácia cai para 66,7%. O rótulo humano é o problema "principal", que é uma escolha subjetiva.
- **Um rotulador só:** o ouro foi rotulado por uma pessoa. A concordância consigo mesmo (kappa, rodada 2) ainda vai ser medida, na Fase 4.
- **Confiança do LLM:** a confiança é declarada pelo próprio modelo e não é calibrada. O limiar de 0,95 foi escolhido na validação porque é o único que atinge a meta de 85%.
- **Reserva treinada no prata:** o embeddings aprendeu com os rótulos do LLM, inclusive com os erros dele. Sem intervalo de confiança por bootstrap da diferença entre as abordagens, a vantagem de 12 pontos de acurácia em 200 itens pareados deve ser lida como estimativa.
- **BERTimbau:** ficou fora da comparação (ADR 0009).
- **Comentários longos:** não há comentário com mais de 300 caracteres na amostra, então a fatia "longos" não foi medida.
- **Dependência externa:** o zero-shot depende de um provedor de LLM e da cota dele. A reserva cobre a indisponibilidade, mas com qualidade menor.

## Como reproduzir

```
python scripts/train_triage_embeddings.py
python scripts/evaluate_triage.py --split val --approaches zero_shot,embeddings_lr --allow-llm
python scripts/evaluate_triage.py --split test --approaches zero_shot,embeddings_lr --final --allow-llm
```

As previsões ficam em `eval/results/` (o zero-shot tem a versão do prompt no nome), e rodar de novo não chama o LLM para itens já previstos. Os rótulos humanos estão em `data/labels/gold.csv`. Os textos vêm da base Olist, que não é redistribuída.
