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
