# Teste A/B do contato proativo: desenho

> **Resumo:** para medir se o contato proativo reduz as avaliações negativas em pedidos de alto risco, o teste precisa de **237 pedidos por grupo (cerca de 57 dias)** para detectar uma redução de 20%. Detectar 10%, o mínimo que paga o contato, levaria **221 dias** com o volume histórico. A recomendação é rodar por 57 dias, com análise só no fim.

Este projeto **não roda** o experimento com clientes reais. Ele entrega o desenho, o sorteio e uma simulação que prova que a análise planejada funciona. Números gerados por `scripts/ab_design.py`; tabelas em [`experimento-ab-resultados.md`](experimento-ab-resultados.md).

## Hipótese

Contatar proativamente, no dia da entrega, os pedidos que o modelo de risco marca como alto risco (probabilidade ≥ 0,41) reduz a taxa de avaliação negativa desses pedidos.

## Métricas

- **Principal:** taxa de avaliação negativa (nota 1 ou 2) entre os pedidos elegíveis.
- **De proteção:**
  - custo do contato por pedido;
  - volume de reclamações abertas pelo cliente depois do contato (o contato não pode irritar);
  - taxa de avaliações respondidas (o contato não pode reduzir a resposta só para "esconder" a nota ruim).

## População e sorteio

- **Elegíveis:** pedidos entregues com probabilidade de risco ≥ limiar do modelo.
- **Volume histórico** fora do período de treino do modelo: 1.458 pedidos em 174 dias, ou **8,4 por dia**.
- **Linha de base** no grupo: **63,6%** de negativas (o modelo previa 63,8% em média, o que confirma a calibração).
- **Sorteio 50/50 determinístico** (`assign_group`): hash SHA-256 de `semente:id_do_pedido`. O mesmo pedido cai sempre no mesmo grupo. Com a semente 42, 49,2% dos elegíveis históricos caem no tratamento.
- Os dois grupos são registrados no banco pela API (`POST /risk/batch`, Fase 6), e só o tratamento recebe o contato (fluxo 3 do n8n).

## Tamanho de amostra e duração

Teste bilateral de duas proporções, alfa 5% e poder 80%.

| Redução relativa mínima | Taxa esperada no tratamento | Por grupo | Total | Dias |
| ---: | ---: | ---: | ---: | ---: |
| 10% | 57,2% | 928 | 1.856 | 221 |
| **20%** | **50,9%** | **237** | **474** | **57** |
| 30% | 44,5% | 106 | 212 | 25 |

### Qual efeito mínimo importa?

Com contato a R$ 2 e R$ 30 por negativa evitada, o contato só se paga se evitar pelo menos 2 ÷ (0,636 × 30) ≈ **10,5%** das negativas desse grupo. Abaixo disso, o resultado do teste seria "não vale a pena" de qualquer forma.

O teste ideal detectaria 10%, mas isso leva 221 dias com 8,4 pedidos por dia. **Recomendação:** desenhar para 20% (57 dias), que é a premissa usada no modelo de risco. Se o efeito real for perto de 10%, o teste provavelmente não terá significância, e a conclusão honesta será "efeito pequeno demais para justificar o custo com esse volume".

**Alternativas para encurtar o teste:**
- baixar o limiar de elegibilidade, o que aumenta o volume mas reduz a taxa de base;
- rodar numa loja com mais volume (o volume da Olist em 2018 é pequeno);
- usar sorteio desigual, por exemplo 70/30, o que reduz o custo, mas aumenta a duração.

## Simulação: a análise planejada recupera o efeito?

Usamos os 1.458 pedidos elegíveis históricos. Em cada uma de 500 simulações, sorteamos os grupos de novo, aplicamos um efeito conhecido no tratamento e rodamos a análise planejada.

| Efeito verdadeiro | % significativo | Efeito médio estimado | Cobertura do IC 95% |
| ---: | ---: | ---: | ---: |
| 0% | **4,6%** (falso positivo) | 0,2% | 95,4% |
| 10% | 73,8% | 10,2% | 96,0% |
| 20% | 100% | 20,3% | 95,6% |
| 30% | 100% | 30,2% | 96,0% |

- Sem efeito, só 4,6% das simulações dão "significativo", perto dos 5% esperados.
- Com efeito, a estimativa média acerta o valor verdadeiro (sem viés), e o intervalo de 95% contém o efeito verdadeiro em cerca de 95% das vezes.
- Com 1.458 pedidos (cerca de 174 dias de histórico), um efeito de 10% seria detectado 74% das vezes, coerente com o cálculo de 1.856 pedidos para 80%.

## Análise planejada (definida antes de começar)

1. Teste z de duas proporções, bilateral, com alfa de 5%, comparando a taxa negativa do tratamento e do controle (`copiloto.ds.experiment.analysis.analyze`).
2. Reportar a diferença absoluta, a mudança relativa, o IC 95% e o valor-p.
3. Uma única análise, no fim da duração fixada. Sem olhar o valor-p no meio do caminho.

## Riscos e mitigações

| Risco | O que acontece | Mitigação |
| --- | --- | --- |
| Contaminação | O mesmo cliente tem pedidos nos dois grupos e o contato de um afeta o outro | Numa versão real, sortear por `customer_unique_id`, não por pedido |
| Efeito novidade | O primeiro contato impressiona, os seguintes não | Duração de pelo menos 8 semanas; olhar o efeito por semana no fim |
| Parar cedo demais | Olhar todo dia e parar no primeiro "significativo" infla o falso positivo | Duração fixada antes; análise só no fim |
| Mudança no modelo | Retreinar o modelo durante o teste muda quem é elegível | Congelar o modelo e o limiar durante o teste |
| Viés de resposta | O contato muda quem responde a pesquisa | Métrica de proteção: taxa de resposta por grupo |

## Limitações

- A duração usa o volume histórico da Olist, que tem poucos pedidos no fim do período (set. a out. de 2018). O volume diário real pode ser maior.
- A simulação aplica o efeito de forma uniforme. Na vida real, o efeito pode variar com o tipo de problema, e atraso é diferente de defeito.
