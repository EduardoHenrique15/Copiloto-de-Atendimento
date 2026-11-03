# ADR 0011: avaliação do copiloto e validação do juiz LLM

- Status: aceita (protocolo). Os resultados serão registrados aqui.
- Data: 2026-11-01

## Contexto

A seção 8.5 da especificação pede 60 casos de avaliação do copiloto, um LLM como juiz com rubrica fixa, a validação do juiz com 40 rascunhos avaliados pelo Eduardo e testes de regressão no CI. O protocolo é definido **antes** de rodar, para a regra de aceitação do juiz não ser ajustada aos resultados.

## Decisão

1. **Casos fictícios** (`eval/copilot_cases.yaml`):
   - 60 casos, escritos para o projeto e inspirados no tipo de reclamação da base. Nenhum texto da Olist é copiado, porque a licença não permite redistribuir.
   - Cobrem as 9 categorias, 7 casos sem política aplicável e 10 tentativas de prompt injection. Três casos têm dados pessoais inventados.
   - Cada caso diz quais políticas podem ser citadas, quais ações são aceitas e se precisa ir para humano.
2. **O copiloto recebe a categoria certa**, sem passar pela triagem. Assim, a avaliação mede só o rascunho; o erro da triagem já foi medido na Fase 5. A busca de políticas é a real (embeddings e ChromaDB).
3. **Verificações automáticas, sem LLM:**
   - cita uma política esperada;
   - a ação final está entre as aceitas;
   - o envio para humano bate com o esperado;
   - a injection foi detectada pelo guardrail.
4. **Juiz LLM** (`judge-v1`, `src/copiloto/ai/eval/judge.py`):
   - Uma chamada por rascunho, com 5 critérios de aprovado ou reprovado: fidelidade, ação, citação, tom e sem promessa indevida.
   - O juiz vê as mesmas políticas que o redator recebeu. É o mesmo modelo do redator, o que é uma limitação: ele pode ser indulgente com o próprio estilo.
5. **Avaliação humana às cegas:**
   - O Eduardo avalia 40 dos 60 rascunhos, com a mesma rubrica, numa ferramenta que não mostra o juiz nem as verificações (`src/copiloto/dashboard/copilot_eval_app.py`).
   - Os 40 são sorteados com semente fixa, mantendo a proporção de injection (7 de 40).
   - **A avaliação humana é feita antes de rodar o juiz**, para nenhum resultado do juiz influenciar.
6. **Regra de aceitação do juiz:**
   - Ela é definida aqui, antes dos resultados: concordância geral (5 critérios × 40 rascunhos) de **pelo menos 80%** e kappa geral de **pelo menos 0,40**.
   - Por que as duas medidas: a concordância sozinha engana quando quase tudo é aprovado; o kappa desconta a concordância por acaso.
   - Se o juiz não passar, os números dele não entram no README como medida de qualidade, e a qualidade fica descrita pelas verificações automáticas e pela avaliação humana.
7. **Regressão no CI:**
   - `eval/regression_cases.yaml` traz 8 casos com a resposta do LLM gravada e os trechos de política fixos.
   - `tests/unit/test_copilot_regression.py` verifica ação, envio para humano, eventos de guardrail, troca pela resposta padrão e citações.
   - Mudança de prompt exige rodar a avaliação real de novo (com autorização) e registrar antes e depois.

## Custo e cota

- **Rascunhos:** 60 chamadas.
- **Juiz:** 60 chamadas.
- **Total:** 120 chamadas, R$ 0 no plano gratuito. O preço pago de referência sai da estimativa do script.

## Consequências

- **Resultados:**
  - `eval/results/copilot_drafts_<versão>.jsonl`, `copilot_judge_<versão>.jsonl` e `copilot_eval_<versão>.json`;
  - relatório em `docs/model-cards/copiloto-avaliacao-<versão>.md`;
  - avaliação humana em `eval/human/copilot_human.csv`.
- **Os casos são fictícios e escritos por quem fez o sistema.** Eles podem ser mais fáceis que reclamações reais. Isso vai para as limitações.

## Atualização de 2026-11-01 (revisão): draft-v2

A leitura dos rascunhos do `draft-v1` e das observações da avaliação humana mostrou dois problemas de desenho, não de prompt:

1. **Busca de políticas.**
   - A busca só vetorial trouxe ao menos uma política esperada em 47 de 53 casos (os 7 sem política ficam fora da conta).
   - Em 4 dos 8 casos de atraso, a política "Atraso na entrega" nem chegou ao redator. Sem ela, o rascunho não tinha como oferecer o cupom nem citar a regra.
   - O `draft-v2` usa busca híbrida: os trechos da política principal da categoria sempre entram (`CATEGORY_POLICIES` em `ai/copilot/retrieve.py`), mais 4 da busca vetorial.
   - Com os trechos que o `draft-v1` recuperou, a busca híbrida teria acertado 52 de 53. A estimativa é offline e vem do campo `retrieved` dos rascunhos.
2. **Ação "investigar".**
   - Abrir investigação com a transportadora é o que a política de pedido não recebido manda fazer, mas não existia essa ação. O redator escolhia "escalar" ou "nenhuma", e a avaliação humana reprovou a ação em 6 casos por isso.
   - `investigar` entrou na lista de ações, permitida pelas políticas de pedido não recebido e de atraso.

**Versões e arquivos.** Cada versão tem os seus arquivos (`copilot_*_<versão>`), para comparar antes e depois. A avaliação humana vale para o `draft-v1`. Por isso, o juiz é validado no `draft-v1` (`--version draft-v1`) e, se for aceito, mede também o `draft-v2`. Rodar o `draft-v2` exige nova autorização: 60 chamadas para os rascunhos e 60 para o juiz.
