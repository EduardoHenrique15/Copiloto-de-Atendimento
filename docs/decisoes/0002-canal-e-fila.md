# ADR 0002: canal da equipe (Telegram) e fila de tickets (Trello)

- Status: aceita
- Data: 2026-10-31

## Contexto

Os fluxos do n8n precisam de um canal para avisos e aprovação humana, e de uma fila para os tickets triados. A especificação deixa a escolha aberta: Slack, Discord ou Telegram, e Trello, Notion ou Google Sheets.

## Decisão

- **Canal: Telegram.** O bot é criado pelo @BotFather, sem console nem OAuth. O nó "Send and Wait for Response" do n8n envia o rascunho com botões de aprovação. Como o atendente (o Eduardo) clica no próprio PC, o link para `localhost` funciona sem túnel. Slack e Discord exigem criar um app e expor um endpoint público para os botões.
- **Fila: Trello.** Uma lista por categoria fica visual no vídeo. A credencial é só uma API key e um token. O Google Sheets exige criar um cliente OAuth no Google Cloud Console.

## Consequências

- Se for preciso aprovar pelo celular fora de casa, vai ser necessário um túnel (`cloudflared`), documentado na Fase 8.
- O teste gratuito do Trello Premium expira, mas o projeto só usa recursos do plano gratuito.

## Correção de 2026-11-03

A premissa de que o botão do Telegram podia apontar para `localhost` estava errada. Na primeira execução real, o Telegram recusou a mensagem com "inline keyboard button URL ... is invalid: Wrong HTTP URL": ele não aceita botão com link para `localhost`. Os testes com dublês não pegaram isso, porque o dublê aceitava qualquer botão.

Correção (ADR 0012): o fluxo 2 manda o rascunho como mensagem comum, com o link do formulário de decisão **no texto**, e espera a resposta num nó "Wait" do tipo formulário. Continua sem túnel: o atendente copia ou clica no link no PC onde o n8n roda.
