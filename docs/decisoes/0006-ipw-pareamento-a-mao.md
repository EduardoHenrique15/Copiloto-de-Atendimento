# ADR 0006: IPW e pareamento implementados à mão

- Status: aceita
- Data: 2026-10-31

## Contexto

A Fase 3 estima o efeito causal do atraso na nota, controlando confundidores observados. Existem bibliotecas prontas (DoWhy, EconML, causalml), mas elas trazem muitas dependências e escondem detalhes que precisam ser explicados numa entrevista.

## Decisão

- Propensão com regressão logística do scikit-learn, com propensões limitadas a [0,01; 0,99].
- IPW normalizado (Hájek) para ATT e ATE, em poucas linhas (`estimators.py`).
- Pareamento 1:1 com reposição pelo vizinho mais próximo no logit da propensão, com caliper de 0,2 desvio-padrão.
- Balanceamento por SMD, bootstrap com reajuste da propensão e E-value, todos implementados no projeto.
- Validação com dados sintéticos de efeito conhecido (`tests/fakes/causal_data.py`).

## Consequências

- Controle total e código curto, fácil de explicar.
- Sem estimadores duplamente robustos (AIPW) nem modelos de efeito heterogêneo. Ficam como melhoria futura.
- O bootstrap reajusta a propensão 200 vezes, o que leva alguns minutos.
