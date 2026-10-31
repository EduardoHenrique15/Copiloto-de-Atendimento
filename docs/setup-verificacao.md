# Verificação do ambiente (Fase 0)

Registro do que foi configurado e verificado antes de começar o código. Nenhum segredo aparece aqui: só nomes de variáveis, serviços e resultados dos testes.

Data da verificação: 2026-10-31.

## 1. Dados: base Olist (Kaggle)

- Fonte: [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), licença CC BY-NC-SA 4.0.
- Local: `data/raw/` (fora do git).
- Arquivos verificados (tamanho em bytes):

| Arquivo | Tamanho |
| --- | ---: |
| `olist_customers_dataset.csv` | 9.033.957 |
| `olist_geolocation_dataset.csv` | 61.273.883 |
| `olist_orders_dataset.csv` | 17.654.914 |
| `olist_order_items_dataset.csv` | 15.438.671 |
| `olist_order_payments_dataset.csv` | 5.777.138 |
| `olist_order_reviews_dataset.csv` | 14.451.670 |
| `olist_products_dataset.csv` | 2.379.446 |
| `olist_sellers_dataset.csv` | 174.703 |
| `product_category_name_translation.csv` | 2.613 |

## 2. LLM

- Provedor principal: Google Gemini, pelo endpoint compatível com OpenAI.
- `LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/`
- `LLM_MODEL=gemini-3.5-flash-lite`
- Limites do nível gratuito, vistos no AI Studio em 2026-10-31:

| Modelo | RPM | TPM | RPD |
| --- | ---: | ---: | ---: |
| `gemini-3.5-flash-lite` | 15 | 250K | 500 |
| `gemini-3.8-flash` | 5 | 250K | 20 |

- Chamada de teste autorizada: 1 requisição, com resposta em JSON (`response_format = json_object`) válida. Uso: 26 tokens de entrada, 22 de saída.
- Saída estruturada: funciona.
- Provedor reserva: Groq (`https://api.groq.com/openai/v1`), com chave criada e guardada no `.env` como `GROQ_API_KEY`. Ainda não testada.
- Decisão registrada em `docs/decisoes/0001-provedor-e-modelo-llm.md`.

## 3. Docker e n8n

- Docker: `Docker version 29.7.2, build a7dcaa6`, com `hello-world` funcionando.
- n8n: versão 2.45.7 (imagem `docker.n8n.io/n8nio/n8n`), abrindo em `http://localhost:5678`, com conta de dono local criada.
- Volume `n8n_data` no Docker, fora do repositório.
- Assistente de IA do n8n: não ativado (o n8n não chama LLM; veja a seção 3 do CLAUDE.md).
- Avisos do n8n que não afetam o projeto:
  - "Python 3 is missing": só afeta o nó Code em Python, que não será usado.
  - Variáveis depreciadas (`N8N_RUNNERS_MODE`, `N8N_RUNNERS_TASK_TIMEOUT` etc.): serão fixadas no `docker-compose.yml` da Fase 8.

## 4. Canal da equipe e fila de tickets

- Canal: Telegram.
  - Bot: `@copiloto_atendimento_bot`.
  - Grupo: `Equipe Atendimento`, com o bot como membro.
  - O token do bot fica fora do repositório. Ele será cadastrado só nas Credentials do n8n, na Fase 8.
- Fila: Trello.
  - Quadro: `Copiloto - Fila de Tickets`.
  - Listas iniciais: `Revisar classificação`, `Urgente`, `Fila geral`.
  - As listas por categoria serão criadas depois da taxonomia (Fase 4).
  - A API key e o token do Trello serão criados na Fase 8.
- Decisão registrada em `docs/decisoes/0002-canal-e-fila.md`.

## 5. Google Colab

- Acesso confirmado, com GPU T4 disponível no plano gratuito. Será usada só na Fase 5 (BERTimbau).

## Pendências para fases futuras

- Definir `TEST_EMAIL_TO` e a credencial de e-mail no n8n (Fase 8).
- Descobrir o `chat_id` do grupo do Telegram (Fase 8).
- Criar a API key e o token do Trello (Fase 8).
- Recomendação: mover o projeto para fora do OneDrive (ex.: `C:\projetos\`), para evitar sincronizar `data/`, `.venv/` e `models/`.
