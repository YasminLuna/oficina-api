# Oficina API — FIAP Tech Challenge Fase 3

Aplicação principal em FastAPI executada no Amazon EKS. Consome JWT emitido pela Lambda de autenticação por CPF, persiste dados no PostgreSQL RDS e envia logs, métricas e traces ao Datadog.

## Stack

> Atualização operacional: deploy de homologação acionado após habilitação de `ENABLE_DEPLOY` no GitHub Actions.

<!-- deploy-trigger: 2026-09-16 -->
