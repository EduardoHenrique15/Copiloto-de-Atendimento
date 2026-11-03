# ADR 0012: como os fluxos do n8n foram montados

- Status: aceita
- Data: 2026-11-01

## Contexto

A seção 10 pede quatro fluxos no n8n, versionados em JSON e sem segredos, com Telegram e Trello (ADR 0002). A lógica de negócio fica na API. O n8n só orquestra.

## Decisão

1. **Configuração por variável de ambiente.**
   - O `docker-compose.yml` repassa ao n8n só as variáveis de que os fluxos precisam: endereço da API, `chat_id`, quadro do Trello, `TEST_EMAIL_TO`, data simulada e limites de alerta. Os fluxos leem com `$env`.
   - As chaves do LLM nunca entram no n8n.
2. **Credenciais por nome.**
   - Os JSON só referenciam as credenciais pelo nome: `Copiloto API`, `Telegram Copiloto`, `Trello Copiloto` e `E-mail de teste`. O Eduardo cria as quatro dentro do n8n.
   - No teste, o n8n 2.45.7 achou a credencial pelo nome mesmo com outro id, então não é preciso religar nó por nó depois de importar.
3. **Regras em nós de código, chamadas em HTTP.**
   - Escolha da fila, montagem da decisão e conferência dos limites ficam em nós Code curtos e comentados.
   - O Trello é chamado pela API HTTP com a credencial do Trello: listar as listas do quadro e criar o card.
   - O Telegram e o e-mail usam os nós próprios do n8n.
4. **Filas do Trello por tipo de ação, não por categoria.**
   - São 7 listas: Urgente, Entrega, Produto, Financeiro, Atendimento e outros, Sem ação e Revisar classificação.
   - A regra: revisão humana tem prioridade, depois urgência alta, depois a categoria.
5. **Aprovação pelo "enviar e esperar" do Telegram**, com formulário: Aprovar, Editar (com o texto final) ou Recusar.
   - O formulário abre em `localhost:5678`, então a decisão é tomada no PC do n8n, sem túnel (ADR 0002).
   - A mensagem escapa os caracteres do Markdown do Telegram (`_`, `*`, `` ` ``, `[`), porque as categorias têm `_`.
6. **Quem vai para aprovação:** ticket sem revisão humana, sem urgência alta e com problema relatado (não `sem_problema`). Ticket urgente vai para uma pessoa direto, com aviso no Telegram.
7. **Data simulada no fluxo proativo:** a base é histórica. A data fica nos dados estáticos do fluxo e avança um dia por execução agendada.
8. **Relatório semanal em texto gerado pela API** (`GET /metrics/report`), sem LLM. O fluxo só repassa o texto.
9. **A resposta da triagem passou a incluir `text_masked`**, para o atendente ver a reclamação no Telegram sem dados pessoais. O snapshot do contrato foi atualizado.

## Como foi testado

- Os JSON foram importados num n8n 2.45.7 local, com a API rodando sobre o container de teste (LLM falso) e dublês HTTP e SMTP do Telegram, do Trello e do e-mail.
- Os 4 fluxos rodaram de ponta a ponta:
  - card na fila certa e aviso urgente;
  - rascunho, formulário enviado, decisão gravada e e-mail;
  - lote de risco com e-mail só para o tratamento;
  - alerta disparado com o limite forçado.
- No CI, `tests/unit/test_n8n_exports.py` confere que não há segredos nos JSON.

## Consequências

- Mudar um fluxo exige exportar de novo e rodar o teste de segredos.
- Aprovar pelo celular fora de casa exigiria um túnel (`cloudflared`), fora do escopo.
