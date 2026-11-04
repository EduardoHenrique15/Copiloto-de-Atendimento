# Segurança

## Segredos

- **Nenhuma chave no repositório.**
  - O `.env` e o `kaggle.json` estão no `.gitignore` desde o primeiro commit.
  - O `.env.example` só tem nomes de variáveis.
  - Um teste confere que cada variável aparece uma vez, sem valor secreto.
- **Credenciais do n8n** (Telegram, Trello, e-mail e chave da API): ficam só dentro do n8n, no volume `n8n_data`. Os fluxos em JSON só citam o nome da credencial, e `tests/unit/test_n8n_exports.py` procura padrões de token e de senha a cada execução do CI.
- **O n8n não recebe as chaves do LLM.** O `docker-compose.yml` repassa a ele só as variáveis de que os fluxos precisam.
- **Na configuração, os segredos usam `SecretStr`.** Eles não aparecem em logs nem em mensagens de erro.
- **Conferência do histórico:** nenhum token, `.env` ou dado bruto em todo o histórico do git (revisão de 2026-11-01).

## API

- **Chave obrigatória** no cabeçalho `X-API-Key`, comparada em tempo constante.
- **Entradas validadas** por Pydantic, com campos extras recusados e tamanho máximo de texto.
- **Erros sem traceback** e sem o texto do cliente.
- **Correlation id** em cada resposta e em cada chamada ao LLM.

## Dados pessoais

- **Máscara de CPF, e-mail, telefone e CEP** antes do texto ir ao LLM, antes de gravar no banco e de novo na resposta gerada.
- **Eventos de guardrail** são gravados sem o texto completo do cliente.
- **Nenhuma tentativa de reidentificar clientes** da base. Os ids da Olist já são anônimos.
- **E-mails só vão para `TEST_EMAIL_TO`,** o único destinatário configurável, e um teste confere isso nos fluxos.

## LLM

- **O texto do cliente é dado, não instrução.** Ele vai delimitado no prompt, com a regra explícita de ignorar instruções dentro dele.
- **Detector de prompt injection por padrões,** que marca o caso para revisão humana.
- **Guardrails em código** depois do LLM:
  - citação só de trechos recuperados;
  - ação permitida pela política;
  - valores, prazos e porcentagens só se estiverem nas políticas ou nos dados do pedido;
  - termos proibidos;
  - tamanho máximo.
- **Aprovação humana** antes de qualquer resposta chegar ao cliente.
- **Chamadas reais ao LLM só com autorização explícita,** com estimativa de custo antes. Os testes usam sempre um LLM falso.

## Limites conhecidos

O detector de injection por padrões é contornável (5 de 10 tentativas passaram sem ser marcadas na avaliação). A defesa principal é a combinação de três coisas: texto delimitado, guardrails de saída e aprovação humana. Detalhes em `docs/model-cards/copiloto.md`.
