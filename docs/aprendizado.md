# Aprendizado: decisões explicadas

Este arquivo explica, em linguagem simples, o porquê de cada decisão do projeto, para servir de preparação para entrevistas.

## Fase 0: contas e ambiente

**Por que separar a configuração do ambiente do código?**
Numa empresa, ninguém começa a programar antes de ter acesso aos dados, às chaves e às ferramentas. Registrar isso em `docs/setup-verificacao.md` permite que outra pessoa reproduza o ambiente e mostra que nenhum segredo foi parar no repositório.

**Por que o Gemini 3.5 Flash Lite, e não o modelo mais novo?**
O mais novo (3.8 Flash) permite só 20 chamadas por dia no plano gratuito. O Flash Lite permite 500. A escolha veio da restrição real de cota, não da preferência pelo modelo "melhor". Em entrevista: "escolhi o modelo que cabia no orçamento e deixei o provedor trocável por configuração; o Groq fica como plano B".

**Por que deixar o provedor trocável?**
Todos os provedores usados falam o mesmo formato de API (compatível com OpenAI). Trocar de provedor é mudar duas linhas no `.env`, sem tocar no código. Isso reduz o risco de ficar preso a um fornecedor ou parar o projeto quando a cota acaba.

**Por que Telegram e Trello?**
Foram os que exigiam menos configuração de segurança: o bot do Telegram sai do @BotFather em um minuto, e os botões de aprovação funcionam em `localhost`, sem túnel. O Trello mostra as filas de forma visual, o que ajuda no vídeo. Slack e Google Sheets exigiriam OAuth e endpoints públicos.

**Por que nenhuma chave está no repositório?**
O `.env` está no `.gitignore` desde antes de ser criado. Os tokens do Telegram e do Trello vão ficar só dentro do n8n. Se um segredo vaza no histórico do git, apagar o arquivo não resolve: é preciso revogar a chave.

## Fase 1: fundação e dados

**Por que staging, intermediate e marts?**
Cada camada tem uma responsabilidade. Staging só corrige tipos e nomes, uma tabela por CSV. Intermediate junta e agrega (itens por pedido, pagamentos por pedido, coordenadas por CEP). Marts são as tabelas que os modelos usam. Quando algo dá errado, fica fácil saber em qual camada procurar.

**Por que ler tudo como texto primeiro?**
O CEP `01001` viraria o número `1001` se o DuckDB adivinhasse o tipo. Lendo como texto e convertendo à mão, o tipo de cada coluna fica explícito e revisável.

**O que é "as-of" e por que importa?**
O histórico do vendedor (nota média, taxa de atraso, volume) é calculado só com o que já se sabia no momento da compra. Exemplo: se a avaliação de um pedido anterior foi criada depois da compra atual, ela não entra. Sem isso, o modelo "veria o futuro" no treino e pareceria melhor do que é em produção. Isso é vazamento de dados. Um teste do dbt recalcula o histórico de forma independente, e um teste em Python confere os valores na amostra fictícia.

**Por que uma avaliação por pedido?**
Alguns pedidos têm mais de uma avaliação. Para o alvo do modelo, ficamos com a mais recente, que representa a opinião final do cliente.

**Por que descartar coordenadas fora do Brasil?**
A tabela de geolocalização tem pontos com latitude e longitude fora do país. Na média por CEP, um único ponto errado desloca a coordenada em milhares de quilômetros. O filtro é feito antes da média.

**Por que uma amostra fictícia nos testes?**
A licença da Olist não permite redistribuir os dados, então o CI não tem a base real. A amostra tem 7 pedidos pensados para cobrir os casos difíceis: pedido com dois vendedores, pedido cancelado, avaliação repetida, comentário com quebra de linha e ponto fora do Brasil. Os resultados esperados foram calculados à mão e estão comentados no teste.

**Avaliação antes da entrega?**
Na Olist, a pesquisa de satisfação é enviada perto da data estimada. Pedidos atrasados podem ser avaliados antes de chegar. Por isso o teste "avaliação depois da entrega" é só um aviso, e a quantidade de casos fica registrada no resumo.

**Números reais da base** (fonte: `docs/eda-resumo.md`, gerado por `scripts/eda_resumo.py`):

- 99.441 pedidos, com compras de 04/09/2016 a 17/10/2018. Desses, 96.470 foram entregues.
- 99.224 avaliações, das quais 40.968 têm comentário (58,71% sem comentário). A especificação estimava "cerca de 40 mil comentários": confirmado.
- 547 pedidos têm mais de uma avaliação. Para eles, usamos a mais recente.
- `fct_orders_risk` tem 95.824 pedidos entregues e avaliados.
- **Taxa de nota negativa (1 ou 2): 12,81%.** O alvo é desbalanceado, por isso a Fase 2 prioriza PR-AUC, e não acurácia.
- **7,99% dos pedidos atrasam.** Entre os atrasados, 54,05% dão nota negativa. Entre os entregues no prazo, 9,22%. A nota média cai de 4,29 para 2,57.
- A taxa negativa sobe com o atraso: 9% quando chega 10 ou mais dias adiantado, 19% com 1 a 3 dias de atraso, 67% com 4 a 10 dias e 79% com mais de 10 dias.
- 14.447 reclamações com texto (nota até 3) em `fct_complaints`. É a base da triagem.
- 476 pedidos sem distância, porque o CEP não tem coordenada. O modelo de risco vai tratar esse valor ausente.
- 4.967 avaliações (cerca de 5%) foram criadas antes da entrega. Isso confirma que a pesquisa sai perto da data estimada, e não depois da entrega.
- Nenhum pedido tem entrega antes da compra.

**Cuidado ao contar essa história:** "atrasados têm 54% de notas negativas contra 9%" é correlação. Pedidos atrasados tendem a ser de regiões distantes e de certos vendedores, que já teriam notas piores. Quanto do efeito é causado pelo atraso fica para a Fase 3.

## Fase 2: modelo de risco

**Qual é a pergunta?**
No dia da entrega, quais pedidos têm mais chance de receber nota 1 ou 2? Com essa lista, o atendimento pode agir antes da avaliação.

**Por que três modelos?**
- **Regra simples** ("negativo se atrasou"): é o que qualquer pessoa faria sem modelo. Se o modelo não superar a regra, não vale a complexidade.
- **Regressão logística:** interpretável e rápida. Mostra quanto um modelo linear consegue.
- **LightGBM:** captura relações não lineares (por exemplo, o risco que dispara a partir de alguns dias de atraso) e interações.

**Por que PR-AUC, e não acurácia?**
Só cerca de 13% dos pedidos são negativos. Um modelo que diz "nunca negativo" acerta 87% e não serve para nada. A PR-AUC mede o quanto o modelo encontra os negativos (recall) sem encher a lista de falsos alarmes (precisão). A referência de um modelo aleatório é a taxa base, cerca de 0,13.

**Por que a divisão é temporal?**
Em produção, o modelo treina com o passado e prevê o futuro. Uma divisão aleatória mistura meses e deixa o modelo "ver" padrões do futuro, o que infla as métricas. Aqui: os primeiros 70% (pela data de entrega) treinam, os 15% seguintes validam e os últimos 15% testam. Além disso, um pedido só entra no treino se a avaliação dele já existia no início da validação, porque quem treina o modelo naquele dia não conhece avaliações futuras.

**O que é calibração e por que importa?**
Calibrado quer dizer: entre os pedidos com probabilidade 30%, cerca de 30% são de fato negativos. O LightGBM ordena bem os pedidos, mas suas probabilidades podem ficar distorcidas. Como o limiar usa a probabilidade para calcular dinheiro, ela precisa ser confiável. Comparamos três opções (sem calibração, isotônica e Platt) numa metade da validação que o calibrador não viu, e o teste nunca é usado nessa escolha. O Brier score e o ECE medem a calibração.

**Por que o limiar não é 0,5?**
Contatar custa R$ 2. Evitar uma nota negativa vale R$ 30, mas o contato só evita 20% delas. Então contatar compensa quando p × 0,2 × 30 > 2, ou seja, p > 0,33. O limiar escolhido é o que maximiza o valor líquido na validação. A curva de valor e a tabela de sensibilidade mostram o que acontece se as premissas mudarem.

**O que o SHAP mostra?**
Quanto cada feature empurrou a probabilidade de um pedido para cima ou para baixo. O SHAP global mostra quais features mais importam no geral. Os três exemplos (risco alto, médio e baixo) mostram os motivos de pedidos específicos. São esses motivos que o atendente vai ver na Fase 6.

**Como o vazamento é evitado?**
1. A lista de features é verificada: nenhuma coluna da avaliação nem o alvo.
2. Toda data usada é anterior ou igual à entrega.
3. O histórico do vendedor é calculado só com o passado (Fase 1, testado no dbt).
4. A divisão é temporal, com a regra de rótulo disponível.
Cada item tem teste automatizado.

**Resultados reais e como contar em entrevista**
- "O LightGBM teve PR-AUC de 0,343 no teste temporal, contra 0,156 da regra 'negativo se atrasou' e 0,099 de um sorteio. O intervalo de confiança da diferença (bootstrap) ficou entre +0,17 e +0,21, então o ganho não é sorte."
- "No limiar de 0,41, escolhido por custo, o modelo contatou 549 clientes com 60% de precisão. A regra de contatar todo atrasado precisou de 1.017 contatos para alcançar quase as mesmas negativas (342 contra 329)."
- "O valor em reais depende de premissas. Com contato a R$ 5 e efeito de 20%, não vale contatar ninguém. Por isso o próximo passo é medir o efeito com um teste A/B."
- **Por que o LightGBM venceu a logística?** O risco não cresce em linha reta com o atraso. Ele fica baixo até o prazo e dispara a partir de alguns dias de atraso (Fase 1: 19% com 1 a 3 dias, 67% com 4 a 10 dias). Árvores capturam esse "degrau" naturalmente.
- **Por que a calibração mudou pouco?** O LightGBM já saiu quase calibrado. Platt ganhou por pouco na validação. O ECE caiu à metade, mas o Brier quase não mudou. Isso é dito no model card em vez de vender a calibração como grande ganho.
- **Mudança de distribuição:** a taxa negativa caiu de 13,5% (treino) para 9,9% (teste). Em produção, isso pede monitoramento da taxa base e retreino periódico.

## Fase 3: análise causal e desenho do A/B

**Por que a correlação não basta?**
Na Fase 1, atrasados deram 54% de notas negativas, contra 9% dos entregues no prazo. Mas os atrasados não são pedidos "iguais com atraso": eles vêm mais de longe, de certas categorias e de vendedores com histórico pior, e esses fatores já pioram a nota mesmo sem atraso. Esses fatores são os **confundidores**. A diferença ingênua mistura o efeito do atraso com o efeito deles.

**O que é o escore de propensão?**
É a probabilidade de um pedido atrasar dados os confundidores (distância, prazo prometido, categoria, estados, vendedor, frete, mês da compra). Dois pedidos com a mesma propensão são comparáveis: um atrasou e o outro não, mas tinham a mesma chance de atrasar.

**IPW (ponderação pelo inverso da propensão)**
Dá peso aos pedidos entregues no prazo para que, juntos, se pareçam com os atrasados. Um pedido no prazo com propensão alta ("tinha tudo para atrasar") pesa mais. Depois, compara as médias ponderadas.

**Pareamento**
Para cada pedido atrasado, encontra o pedido no prazo com propensão mais parecida e compara os pares. Pares muito diferentes (além do caliper) são descartados. Dois métodos com premissas diferentes chegando a números parecidos dão mais confiança.

**ATT ou ATE?**
- **ATT:** o efeito nos pedidos que de fato atrasaram. Responde "quanto o atraso custou de verdade".
- **ATE:** o efeito se qualquer pedido atrasasse.
A pergunta de negócio ("cada 1.000 atrasados geram quantas negativas a mais?") é ATT.

**Sobreposição e balanceamento**
- **Sobreposição:** só dá para comparar se existirem pedidos no prazo com propensões parecidas às dos atrasados. O histograma de propensão mostra isso.
- **Balanceamento:** depois de ponderar, as médias dos confundidores precisam ficar parecidas entre os grupos. A medida é a diferença média padronizada (SMD), e |SMD| < 0,1 é o critério usual.

**Bootstrap**
Reamostra os pedidos 200 vezes e refaz tudo, inclusive a propensão. A variação das estimativas dá o intervalo de confiança.

**E-value**
Mede quão forte um confundidor **não observado** (por exemplo, a qualidade da embalagem) precisaria ser para explicar todo o efeito. E-value alto significa que só um confundidor muito forte anularia o resultado. Ele não prova causalidade: mostra o quão robusta é a conclusão.

**Por que implementar IPW e pareamento à mão?**
São poucas linhas e ficam totalmente transparentes e testáveis. Os testes usam dados sintéticos com efeito conhecido (25 pontos percentuais): a diferença ingênua erra para cima, e IPW e pareamento acertam.

### Desenho do A/B

**Por que um teste A/B?**
O valor do contato proativo depende do efeito do contato, que hoje é uma premissa (20%). Só um experimento mede esse efeito.

**Como funciona o sorteio?**
Um hash do id do pedido com uma semente decide o grupo. O mesmo pedido cai sempre no mesmo grupo, sem precisar guardar estado, e trocar a semente gera um sorteio novo e independente.

**Tamanho de amostra**
Depende de três coisas: a taxa negativa no grupo de alto risco (linha de base), o menor efeito que vale a pena detectar e o poder desejado (80%, com 5% de chance de falso positivo). Efeitos menores exigem amostras muito maiores.

**Simulação**
Aplicamos um efeito conhecido nos dados históricos, sorteamos os grupos de novo várias vezes e rodamos a análise planejada. Com efeito zero, cerca de 5% das simulações dão "significativo": é o falso positivo esperado. Com efeito real, a fração significativa é o poder com o volume disponível.

**Riscos do experimento**
- **Contaminação:** o mesmo cliente com pedidos nos dois grupos. Mitigação: sortear por cliente numa versão real.
- **Efeito novidade:** o primeiro contato surpreende, e os seguintes, menos.
- **Parar cedo demais:** olhar o valor-p todo dia e parar quando ficar "significativo" infla o falso positivo. Mitigação: duração fixada antes e análise só no fim.

### Resultados reais e como contar em entrevista

- "Atraso aumenta em 45 pontos percentuais a chance de nota negativa nos pedidos atrasados: de 8,8% para 54%. São 453 avaliações negativas a mais a cada 1.000 atrasos."
- **"Mas isso não é só correlação?"** "Controlei 99 covariáveis com propensão, IPW e pareamento. O balanceamento ficou bom (todas com |SMD| abaixo de 0,1) e os dois métodos deram o mesmo número. O E-value de 11,8 diz que um confundidor não medido precisaria multiplicar por 10 a chance de atraso e de nota ruim para anular o efeito."
- **Resultado surpreendente:** o ajuste quase não mudou a diferença ingênua (44,8 contra 45,3). Eu esperava que mudasse. Isso mostra que os fatores observados (distância, categoria, vendedor) explicam pouco da nota. O atraso domina. Os testes com dados sintéticos provam que o método corrige o viés quando ele existe, então o resultado não vem de um método quebrado.
- **A/B:** "O contato só se paga se evitar pelo menos 10,5% das negativas. Com 8 pedidos de alto risco por dia, detectar 10% levaria 221 dias. Recomendei desenhar para 20% (57 dias), deixando claro que um efeito perto do mínimo não seria detectado." Isso mostra que o tamanho do teste vem de uma decisão de negócio, não de um número mágico.
- **Por que simular?** Para provar, antes de gastar com clientes reais, que a análise planejada tem cerca de 5% de falso positivo e que o intervalo de confiança cobre o efeito verdadeiro cerca de 95% das vezes.

## Fase 4: taxonomia e rotulagem humana

**Por que ler 100 comentários antes de rotular?**
Categorias inventadas na mesa não batem com o que os clientes escrevem. A leitura mostrou três coisas que a lista inicial não previa: muita gente "não recebeu" mesmo com status "entregue"; vários comentários de nota 3 são elogios; cancelamento e falta de estoque não tinham lugar. Ajustar a taxonomia antes de rotular evita refazer o trabalho.

**Por que rótulos humanos?**
Eles são a verdade usada para medir tudo: a triagem (Fase 5) e o LLM como juiz (Fase 7). Se o LLM gerasse os rótulos "humanos", estaríamos medindo o LLM contra ele mesmo. O conjunto ouro tem 300 comentários: 100 de validação (para ajustar limiares) e 200 de teste (só olhados na comparação final).

**Por que rotular 50 de novo uma semana depois?**
Para medir a consistência do próprio rotulador (kappa de Cohen). Se eu mesmo discordo de mim em 20% dos casos, nenhum modelo pode passar muito disso, e esse é o teto realista. A semana de intervalo evita lembrar da resposta.

**O que é o kappa?**
É a concordância descontada do acaso. Concordar 80% parece bom, mas, se quase tudo fosse de uma categoria só, até respostas aleatórias concordariam muito. Kappa 1 é concordância perfeita; 0 é o que o acaso daria. Acima de 0,6 costuma ser considerado bom; acima de 0,8, muito bom.

**Por que a urgência é por regra, e não rotulada?**
A urgência depende de política da empresa ("dinheiro do cliente envolvido é sempre alta"), não do gosto de quem rotula. Uma regra em código é explicável, testável e muda num lugar só.

**Por que um rótulo principal mais a marcação "mais de um problema"?**
Multirrótulo deixaria a rotulagem mais lenta e as métricas mais difíceis de explicar. A marcação permite medir, na Fase 5, se a triagem erra mais nesses casos, que é a análise de robustez pedida.

**Rotulagem fraca (conjunto prata)**
- **Para que serve:** treinar a triagem precisa de milhares de exemplos, e rotular tudo à mão não é viável. O LLM rotula cerca de 4.000 reclamações para treino. Esses rótulos têm erros, por isso o nome "fraca" ou "prata", e **nunca** são usados para medir qualidade. A medida vem só do ouro humano.
- **Por que excluir o ouro e a amostra da taxonomia?** Se o LLM rotulasse os mesmos textos do teste, o modelo treinado com esses rótulos teria "visto a prova".
- **Por que 20 comentários por chamada?** O plano gratuito permite 500 chamadas por dia. Um por chamada levaria 8 dias; em lotes de 20, cerca de 200 chamadas cabem num dia só. O risco é o LLM se confundir com lotes grandes, por isso cada resposta é validada (um item para cada comentário, categoria da lista) e o lote é refeito uma vez se vier errado.
- **Por que cache em disco?** A mesma entrada devolve a mesma resposta gravada. Se o script cair no meio, ele retoma sem pagar de novo pelo que já foi feito.
- **Texto do cliente é dado, não instrução:** os comentários vão entre marcas `<comentario>` e o prompt manda ignorar instruções dentro deles. É a primeira defesa contra prompt injection, reforçada pelos guardrails da Fase 6.

## Fase 5: triagem

**Por que comparar três abordagens?**
Cada uma tem um custo diferente:
- O **LLM zero-shot** não precisa de treino e entende nuances, mas paga por chamada e responde em segundos.
- **Embeddings + regressão logística** rodam localmente em milissegundos e de graça, mas precisam de exemplos rotulados e entendem menos nuance.
- O **BERTimbau ajustado** costuma ser o mais preciso entre os modelos locais, mas precisa de GPU para treinar e é mais pesado para servir.
A escolha certa depende dos números, não da moda.

**Por que treinar no prata e avaliar no ouro?**
O prata (rótulos do LLM) é barato e grande, bom para treino. O ouro (rótulos humanos) é caro e pequeno, mas é a verdade. Avaliar no prata mediria só "o quanto o modelo imita o LLM", com os erros do LLM incluídos.

**Por que o teste só roda uma vez?**
Se eu olho o teste, ajusto algo e olho de novo, o teste vira validação, e o número publicado fica otimista. Por isso o script exige `--final`, e todas as decisões (prompt, limiar) são tomadas na validação.

**F1 macro**
É a média do F1 de cada categoria, com peso igual para todas. A acurácia sozinha esconderia um modelo que acerta as categorias grandes e erra sempre as raras, como `atendimento_vendedor`.

**Roteamento por confiança**
Não é preciso classificar tudo automaticamente. Se o modelo tem pouca certeza, o ticket vai para uma pessoa. O limiar é escolhido para que os tickets automáticos tenham pelo menos 85% de acerto, e o relatório mostra quantos ficam automáticos (cobertura).

**Custo de modelos locais**
"De graça" não existe: o modelo local ocupa uma máquina. Para comparar com o LLM, o tempo de CPU por ticket é multiplicado por uma premissa de preço-hora (R$ 0,50 por hora), registrada no ADR 0009.
