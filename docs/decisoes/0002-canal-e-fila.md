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
