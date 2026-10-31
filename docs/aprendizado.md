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
