# n8n: os quatro fluxos do Copiloto

| Arquivo | Fluxo | Gatilho |
| --- | --- | --- |
| `workflows/01-triagem.json` | Triagem: `POST /triage`, card no Trello, aviso urgente no Telegram | Webhook `POST /webhook/triagem` |
| `workflows/02-aprovacao.json` | Aprovação: `POST /draft`, decisão no Telegram, `POST /feedback`, e-mail de teste | Webhook `POST /webhook/aprovacao` (chamado pelo fluxo 1) |
| `workflows/03-proativo.json` | Contato proativo: `POST /risk/batch` e e-mail só para os pedidos com `contact = true` (grupo `treatment`, dentro do limite diário) | Todo dia às 9h |
| `workflows/04-monitoramento.json` | Alertas de custo, latência e guardrails, e relatório semanal | A cada hora; segunda às 8h |

Os fluxos não guardam nenhum segredo:
- As credenciais são referências **por nome**. Você cria as credenciais dentro do n8n com esses nomes exatos.
- Os valores de configuração vêm do `.env`, repassados pelo `docker-compose.yml` como variáveis do n8n (`$env`).
- O teste `tests/unit/test_n8n_exports.py` falha se algum JSON tiver token, senha ou URL com credencial.

Os fluxos foram testados de ponta a ponta no n8n 2.45.7, com uma API falsa e dublês do Telegram, do Trello e do e-mail. Os testes cobriram triagem, aprovação com edição, contato proativo e alerta forçado.

## 1. Valores no `.env`

Preencha no `.env` (o modelo está no `.env.example`). Nenhum destes valores é segredo:

| Variável | Onde achar |
| --- | --- |
| `TELEGRAM_CHAT_ID` | Passo 4 |
| `TRELLO_BOARD_ID` | Na URL do quadro: `trello.com/b/<ESTE CÓDIGO>/copiloto-fila-de-tickets` |
| `TEST_EMAIL_TO` | O seu e-mail. É o **único** destinatário de todos os e-mails do projeto. |
| `RISK_SIM_START_DATE` | Já vem `2018-06-01` |

## 2. Subir tudo pelo Docker Compose

O n8n da Fase 0 rodava num contêiner separado. Pare esse contêiner antes, para liberar a porta 5678. O volume `n8n_data`, com a sua conta, é reaproveitado.

```
docker ps --filter "publish=5678"
docker stop <nome que aparecer na coluna NAMES>
docker compose up -d --build
```

## 3. Credenciais no n8n (`http://localhost:5678` → Credentials → Add credential)

Use **exatamente** estes nomes. Os fluxos encontram as credenciais pelo nome.

| Nome | Tipo no n8n | Campos |
| --- | --- | --- |
| `Copiloto API` | Header Auth | Name: `X-API-Key` · Value: o valor de `API_KEY` do seu `.env` |
| `Telegram Copiloto` | Telegram API | Access Token: o token do @BotFather |
| `Trello Copiloto` | Trello API | API Key e Token: em https://trello.com/power-ups/admin, crie um Power-Up, gere a API key e clique em "Token" |
| `E-mail de teste` | SMTP | Gmail: User = o seu Gmail; Password = uma **senha de app** (https://myaccount.google.com/apppasswords); Host `smtp.gmail.com`; Port `465`; SSL/TLS ligado |

O e-mail sai do `TEST_EMAIL_TO` para o próprio `TEST_EMAIL_TO`. Por isso, use o mesmo Gmail na credencial SMTP.

## 4. `chat_id` do grupo do Telegram

1. Mande uma mensagem qualquer no grupo `Equipe Atendimento`.
2. Abra no navegador `https://api.telegram.org/bot<TOKEN>/getUpdates`, trocando `<TOKEN>` pelo token do bot. Não salve esse link em lugar nenhum.
3. Procure `"chat":{"id":-100...`. Esse número, com o sinal de menos, é o `TELEGRAM_CHAT_ID`.
4. Ponha no `.env` e rode `docker compose up -d` de novo.

## 5. Listas do quadro do Trello

Crie no quadro `Copiloto - Fila de Tickets` sete listas com estes nomes exatos:

`Urgente` · `Entrega` · `Produto` · `Financeiro` · `Atendimento e outros` · `Sem ação` · `Revisar classificação`

## 6. Importar e ativar os fluxos

```
docker compose exec n8n n8n import:workflow --separate --input=/home/node/workflows
docker compose restart n8n
```

No n8n, abra cada um dos 4 fluxos e ative (botão **Publish** ou **Active**).

## 7. Testar

**Triagem e aprovação.** Cada reclamação faz 1 chamada ao LLM na triagem e mais 1 no rascunho. Por isso, este teste precisa de autorização.

```
python scripts/simulate_tickets.py --n 2 --dry-run
python scripts/simulate_tickets.py --n 2 --interval 30
```

1. Os cards aparecem no Trello.
2. Os tickets que podem ter resposta automática chegam no Telegram com o botão **Decidir**.
3. O botão abre o formulário em `localhost:5678`, então clique no PC onde o n8n roda.
4. Escolha Aprovar, Editar ou Recusar.
5. Aprovado ou editado, o e-mail chega no `TEST_EMAIL_TO`.

**Contato proativo.** Abra o fluxo 03 e clique em **Execute workflow**, que dispara pelo nó "Executar agora (teste)". A data simulada só avança nas execuções agendadas.

**Alerta.** Ponha `ALERT_MAX_P95_LATENCY_MS=1` no `.env` e rode `docker compose up -d`. Depois, execute o fluxo 04 manualmente: o alerta chega no Telegram. Volte o valor para `5000` no fim.

## Exportar depois de mudar um fluxo

Se você mudar um fluxo no n8n, exporte de novo (menu do fluxo → Download) para `n8n/workflows/`, com o mesmo nome de arquivo. Depois, rode `pytest tests/unit/test_n8n_exports.py` antes do commit.
