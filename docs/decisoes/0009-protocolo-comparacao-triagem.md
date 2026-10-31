# ADR 0009: protocolo da comparação das abordagens de triagem

- Status: aceita (protocolo). A escolha da abordagem de produção será registrada neste ADR com os números reais.
- Data: 2026-10-31

## Contexto

A especificação pede comparar três abordagens de triagem (zero-shot com LLM, embeddings + regressão logística e BERTimbau ajustado) por qualidade, custo, latência e robustez, e escolher a de produção com justificativa. O protocolo precisa ser definido **antes** de olhar os resultados, para a escolha não ser ajustada ao teste.

## Protocolo

1. **Treino:** embeddings + LR e BERTimbau treinam no conjunto prata (4.000 rótulos do LLM, ADR 0008). O zero-shot não treina.
2. **Validação (ouro, 100 itens):** usada para ajustar o limiar de confiança e corrigir problemas de prompt. Pode ser rodada mais de uma vez.
3. **Teste (ouro, 200 itens):** rodado **uma única vez**, com `--final`, depois de todas as decisões. O script recusa o teste sem essa opção.
4. **Rótulos humanos nunca saem do PC:** o BERTimbau roda no Colab só com os textos e devolve previsões. A avaliação é feita localmente.
5. **Qualidade:** F1 macro (principal, porque as categorias são desbalanceadas), acurácia, métricas por categoria e matriz de confusão.
6. **Latência:** p50 e p95 por ticket, um ticket por vez. O BERTimbau é medido em CPU, para comparar com as outras abordagens.
7. **Custo por 1.000 tickets:**
   - **LLM:** tokens medidos × preço do nível pago (`LLM_PRICE_*`, cotado em 30/10/2026, com USD_BRL 5,444). O plano gratuito custa R$ 0, mas o preço pago é a referência para produção.
   - **Locais:** tempo de CPU medido × **R$ 0,50 por hora** (premissa: máquina de 2 vCPUs em nuvem). É uma premissa, registrada aqui, para comparar ordens de grandeza.
8. **Robustez:** acurácia em comentários curtos (até 30 caracteres), longos (mais de 300) e com mais de um problema (marcação humana). Erros de digitação não têm fatia própria, porque não há como detectá-los de forma confiável sem rotular. Fica como limitação.
9. **Roteamento por confiança:** na validação, escolhe-se o menor limiar de confiança cuja acurácia, entre os tickets classificados automaticamente, chegue a **85%**. Abaixo do limiar, o ticket vai para revisão humana. O limiar é aplicado sem mudança no teste.
10. **Concordância LLM × humano:** o zero-shot no ouro também mede a qualidade do conjunto prata, incluindo a confusão `atraso_entrega` × `nao_recebido` observada no ADR 0008.

## Consequências

- Se a validação mostrar um problema de prompt, o zero-shot pode ganhar uma nova versão **antes** do teste. Cada versão é registrada.
- O BERTimbau é desejável, não obrigatório (seção 15 da especificação). Se o Colab não estiver disponível, a comparação fica com duas abordagens, e isso vai para as limitações.
