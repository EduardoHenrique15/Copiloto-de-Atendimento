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

## Resultado do juiz no draft-v1 (2026-11-03)

- Juiz `judge-v1` nos 60 rascunhos: 78,3% aprovados nos 5 critérios. Houve 3 erros 503 temporários do provedor, e o cliente repetiu as chamadas.
- Concordância com a avaliação dos 40 rascunhos: 82,5%, com **kappa de 0,15**. A regra pedia kappa de pelo menos 0,40, então **o juiz não foi aceito**.
- O juiz aprova quase tudo: 92,5% em ação, contra 65,0% na avaliação. Por critério, o kappa ficou entre 0,00 e 0,13, exceto em tom, que deu 1,00.
- **A avaliação dos 40 rascunhos foi feita com apoio de outra IA (ADR 0013).** Então essa concordância não é juiz contra humano. De qualquer forma, os números do juiz **não** são usados como medida de qualidade. A qualidade do copiloto é descrita pelas verificações automáticas.
- O juiz não vai ser rodado no `draft-v2`, porque não foi validado.

## Resultado do draft-v2 (2026-11-03) e correção no draft-v3

60 rascunhos, verificações automáticas (relatórios em `docs/model-cards/copiloto-avaliacao-<versão>.md`):

| Verificação | draft-v1 | draft-v2 |
| --- | ---: | ---: |
| Citação de uma política esperada | 81,7% | 98,3% |
| Ação entre as aceitas | 88,3% | 93,3% |
| Envio para humano como esperado (18 casos) | 83,3% | 88,9% |
| Injection detectada pelo guardrail (10 casos) | 50,0% | 50,0% |
| Resposta trocada pelo texto padrão | 0,0% | 10,0% |

- **A busca híbrida resolveu a citação.** A ação também melhorou, com `investigar` usada em 7 rascunhos.
- **Bug encontrado com o draft-v2:** os 6 bloqueios por promessa sem base foram falsos positivos, todos na política de atraso.
  - O rascunho repetia a regra ("atraso de 4 dias ou mais"), e o número estava só no **título** da seção, que o guardrail não lia.
  - No draft-v1 quase não aparecia, porque essa política raramente era recuperada.
  - O **draft-v3** passa o título da seção ao guardrail, com o caso de regressão `r09`.
- **Ainda alto:** 51 de 60 rascunhos vão para revisão humana (47 no draft-v1), em geral porque o próprio LLM pede.
- **Latência do draft-v2:** p50 de 18,8 s, contra 1,4 s no draft-v1. O provedor estava instável na execução (erros 503 repetidos), e a medida inclui as novas tentativas. Não houve mudança de código que explique isso.
- Medir o draft-v3 exige mais 60 chamadas, com autorização.

## Resultado do draft-v3 (2026-11-03)

- Citação de 98,3%, ação de 98,3%, envio para humano como esperado em 88,9% dos casos e injection detectada em 50%. Nenhuma resposta foi trocada pelo texto padrão.
- As 60 respostas do LLM vieram do cache em disco do draft-v2, porque o prompt é idêntico. A comparação v2 → v3 isola o efeito da correção do guardrail. Com isso, a latência do v3 não é representativa.
- Versão de produção: `draft-v3`. Resumo em `docs/model-cards/copiloto.md`.
