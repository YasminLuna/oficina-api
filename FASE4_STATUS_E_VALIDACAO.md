# Fase 4 — entrega técnica e validação (sem AWS paga)

## Arquitetura implementada

- **API**: FastAPI, PostgreSQL para ordens e Outbox, métricas Prometheus em `/metrics`.
- **Billing**: FastAPI persistente em SQLite, pagamento simulado por padrão; container inicia `app.persistent_api:app`.
- **Execution**: FastAPI persistente com DynamoDB Local.
- **Saga**: consumidor SQS emulador local, estados persistidos em PostgreSQL, compensação de orçamento e execução antes do início, intervenção manual após início.
- **Outbox**: publicação at-least-once; consumidor deduplica estados terminais.

**Limites conhecidos:** SQLite é apropriado à demonstração local, não à alta disponibilidade; o orquestrador e o dispatcher locais não são serviços Kubernetes de produção. O mock de pagamento não liquida transações. Não existe deploy automático em cluster configurado por estes commits.

## Único procedimento local

No Mac, com os três repositórios em `~/fiap-local`:

```bash
cd ~/fiap-local/oficina-api
git pull --ff-only
FASE4_BUILD_IMAGES=1 bash validar-cobertura-fase4.sh
```

O procedimento atualiza os três repositórios por fast-forward, instala dependências em venvs isoladas, executa Ruff e pytest com `--cov-fail-under=80` individualmente, gera XML/logs em `~/fiap-local/fase4-cobertura` e compila três imagens Docker **sem publicar**. Se o Docker não estiver disponível, use `bash validar-cobertura-fase4.sh` para validar apenas código e testes.

**Segurança:** o script não invoca AWS, não executa `docker compose down`, não apaga volumes, não faz deploy e não configura credenciais de pagamento. Os manifests em `k8s/local-service.yaml` são locais e requerem dependências de banco e segredos configurados separadamente; não aplique-os em um cluster de produção.

## Verificação complementar de integração

Com a stack local já iniciada, executar o E2E existente de Saga/Outbox e o E2E de pagamento mock, seguindo os comandos documentados no repositório. Guardar saída com `result: PASS` e `real_charge: false`.

## Evidências para entrega

1. Logs dos três testes com `TOTAL >= 80%` e relatórios XML.
2. Três workflows GitHub Actions aprovados, incluindo lint, testes e build.
3. Docker build local aprovado das três imagens.
4. Capturas dos endpoints `/health`, `/docs`, métricas da API e testes de Saga.
5. Diagrama de arquitetura, README, PDF e vídeo com demonstração.

## Pendências que exigem comprovação adicional

- **CI/CD**: builds e testes configurados; implantação Kubernetes automatizada não foi implementada porque não há destino/credenciais de cluster definidos.
- **Kubernetes**: manifests locais foram criados, mas não executados em cluster nesta sessão.
- **Observabilidade**: API expõe métricas Prometheus; métricas e tracing completos dos demais serviços não foram comprovados.
- **Cobertura**: percentuais definitivos dependem de nova execução; última medição enviada da API foi 58,95% antes dos commits recentes.
- **Mercado Pago**: sandbox real depende de conta e credenciais, não é bloqueio para testes mock.

## Estado de Kubernetes e CI (09/11/2026)

- Cada repositório contém `k8s/local-service.yaml` e o workflow executa uma verificação sintática offline.
- O script `validar-cobertura-fase4.sh` agora também verifica as relações entre Deployment, Service, portas, probes e imagens nos três manifests.
- **Atenção:** estes manifests não constituem um cluster completo. O banco PostgreSQL, DynamoDB Local, SQS LocalStack, inicializadores, dispatcher e Saga worker ainda precisam ser disponibilizados no cluster ou conectados de forma segura a serviços locais. O secret `oficina-api-config` não é criado automaticamente.
- Não aplicar em produção. Não há publicação de imagem, acesso à AWS nem exclusão de volumes.
- A verificação estática não substitui um teste de rollout com `kubectl rollout status`, readiness e Saga ponta a ponta.
- A aprovação de GitHub Actions precisa ser observada na aba Actions; o resultado de pytest executado no Mac não equivale à aprovação do pipeline remoto.

## Próxima evidência

Executar novamente `FASE4_BUILD_IMAGES=1 bash validar-cobertura-fase4.sh`, guardar logs, e confirmar os três workflows na aba Actions. Depois configurar um ambiente Kubernetes local isolado e validar a integração; não há necessidade de alterar ou remover os volumes existentes do Docker Compose.
