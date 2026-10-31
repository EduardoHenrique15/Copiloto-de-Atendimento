# Políticas da Loja Exemplo

> **Todas as políticas desta pasta são fictícias, criadas para este projeto de portfólio.** Elas não representam a Olist, nenhum vendedor da base nem qualquer empresa real.

Cada arquivo tem um comentário de metadados na segunda linha:

```
<!-- id: <identificador> | acoes: <ações que a política permite> -->
```

As ações possíveis são `nenhuma`, `cupom`, `troca`, `reembolso` e `escalar`. O guardrail de política (`copiloto.ai.guardrails.policy`) só aceita uma ação sugerida se ela estiver permitida por uma política citada no rascunho. Cada seção `##` vira um trecho indexado para a busca (RAG).
