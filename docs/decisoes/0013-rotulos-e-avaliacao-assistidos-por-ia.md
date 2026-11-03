# ADR 0013: o conjunto ouro e a avaliação dos rascunhos foram feitos com ajuda de IA

- Status: aceita (registro de fato)
- Data: 2026-11-03

## O que aconteceu

Na revisão completa do projeto (2026-11-01), algumas observações da avaliação dos rascunhos traziam sinais de terem sido escritas por outra IA: menção a "imagem" e instruções dirigidas a quem avalia ("se essa política não existir, marque Reprovado em..."). Perguntado, o Eduardo confirmou:

- **Conjunto ouro (300 reclamações, Fase 4):** as categorias foram decididas com a ajuda de outra IA.
- **Avaliação dos 40 rascunhos (Fase 7):** as respostas também foram decididas com a ajuda de outra IA, a partir de prints.

A especificação do projeto pede rótulos e avaliação feitos à mão. Este ADR registra que isso não aconteceu, para nenhum número publicado ser lido como validação humana pura.

## O que muda na leitura dos resultados

1. **Ouro = "rótulos de referência decididos pelo Eduardo com apoio de IA".** Ele não é uma medida independente de qualidade humana.
2. **Triagem (Fase 5).**
   - Os números do teste (zero-shot com acurácia de 83,5%, embeddings com 71,5%) medem a concordância com esses rótulos de referência.
   - Se a IA usada for parecida com o LLM da triagem, a vantagem do zero-shot pode estar inflada: um LLM tende a concordar com rótulos sugeridos por outro LLM.
   - A ordem entre as abordagens e as decisões de produção continuam razoáveis, mas a diferença de 12 pontos deve ser lida com cautela.
3. **Inconsistência entre atraso e não recebido** (ADR 0007, emenda 2): continua valendo como achado sobre o texto. Textos quase iguais receberam rótulos diferentes, viessem de onde viessem.
4. **Juiz LLM (Fase 7).**
   - A concordância medida (82,5%, kappa 0,15) é entre o juiz e uma avaliação assistida por outra IA. Ela **não** valida o juiz contra um humano.
   - Como o juiz também não passou na regra do ADR 0011, a conclusão é a mesma: os números do juiz não são usados como medida de qualidade.
5. **Verificações automáticas** (citação, ação, envio para humano, injection): não dependem de rótulo humano nem de juiz. São a medida principal da qualidade do copiloto.

## Consequências

- Os model cards, o ADR 0009, o ADR 0011 e o `progresso.md` trazem esta ressalva.
- O README (Fase 9) vai descrever o ouro como "rótulos de referência com apoio de IA".
- **Para tornar o ouro independente no futuro:** uma pessoa rotula de novo uma amostra (por exemplo, 100 itens do teste) sem nenhuma ajuda. Depois, mede-se o kappa contra os rótulos atuais e contra o zero-shot. Os scripts existentes já fazem isso (`scripts/labeler_agreement.py`).
