# ADR 0005: limiar do modelo de risco escolhido por custo

- Status: aceita
- Data: 2026-10-31

## Contexto

O modelo de risco devolve uma probabilidade de avaliação negativa. O atendimento precisa de uma regra de decisão: contatar ou não contatar o cliente antes da avaliação. O limiar padrão de 0,5 não tem relação com o negócio. Contatar tem custo, e o valor de evitar uma nota ruim é outro.

## Decisão

1. **Premissas explícitas e configuráveis** (`.env`): custo do contato (`RISK_CONTACT_COST_BRL`, padrão R$ 2), valor de evitar uma avaliação negativa (`RISK_NEGATIVE_REVIEW_COST_BRL`, padrão R$ 30) e fração de negativas que o contato evita (`RISK_ASSUMED_CONTACT_EFFECT`, padrão 20%). O efeito do contato é uma **premissa**: só o teste A/B da Fase 3 pode medi-lo.
2. **Valor líquido** de um limiar = efeito × valor × negativas alcançadas − custo × contatos.
3. O limiar é o de **maior valor na validação**, depois aplicado sem mudança no teste.
4. O relatório mostra também o **ponto de equilíbrio teórico** (custo ÷ (efeito × valor) = 0,333 com as premissas padrão). Ele só vale se a probabilidade estiver calibrada. Por isso o modelo é calibrado antes da escolha do limiar.
5. O relatório inclui a **sensibilidade**: o melhor limiar e o valor para 27 combinações de premissas.

## Alternativas descartadas

- **Limiar 0,5:** ignora custos.
- **Maximizar F1:** trata falso positivo e falso negativo como igualmente caros, o que não é verdade aqui.
- **Top-N por dia:** útil quando a equipe tem capacidade fixa. Fica como limite operacional no fluxo do n8n (`PROACTIVE_MAX_PER_DAY`), não como critério do modelo.

## Consequências

- O mesmo limiar é usado pela API (`/risk/batch`, Fase 6).
- Se as premissas mudarem, basta rodar `scripts/train_risk.py` de novo.
- O valor em reais depende de premissas não medidas. Todo número de valor publicado vem acompanhado delas.
