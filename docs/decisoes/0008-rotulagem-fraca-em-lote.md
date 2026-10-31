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
