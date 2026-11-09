# FIAP Tech Challenge - Fase 4 | Guia de entrega e evidencias

> Ambiente demonstrado: Kubernetes local (kind), LocalStack SQS, PostgreSQL, SQLite persistente no Billing e DynamoDB Local no Execution. Nenhum recurso AWS pago e necessario para reproduzir a demonstracao local.

## Repositorios e branches

| Componente | Repositorio | Branch |
|---|---|---|
| API / Outbox / Saga | https://github.com/YasminLuna/oficina-api | feature/fase4-microservices |
| Billing | https://github.com/YasminLuna/oficina-billing-service | feature/fase4-service |
| Execution | https://github.com/YasminLuna/oficina-execution-service | feature/fase4-service |

## Arquitetura demonstrada

```mermaid
flowchart LR
    Client[Cliente REST] --> API[Oficina API]
    API --> PG[(PostgreSQL: pedidos / outbox / Saga)]
    Dispatcher[Outbox Dispatcher] --> SQS[LocalStack SQS]
    PG --> Dispatcher
    SQS --> Saga[Saga Worker]
    Saga --> Billing[Billing REST]
    Saga --> Execution[Execution REST]
    Billing --> SQLite[(SQLite + PVC)]
    Execution --> Dynamo[(DynamoDB Local + PVC)]
    Saga --> PG
```

O orquestrador e o dispatcher sao processos independentes da API, mas utilizam codigo do repositorio da API. A persistencia dos servicos e separada no ambiente local.

## Evidencias de testes observadas

- Fluxo de sucesso no kind: `order_id=5a22ff00-c441-4235-b6c9-4351b80c2a43`, outbox `PUBLISHED`, Saga `COMPLETED`, Billing `APPROVED`, Execution `COMPLETED`, evento duplicado `DEDUPLICATED`.
- Compensacao integrada: `order_id=c159a9ee-5ec2-4a63-b005-eab017a86327`, Billing `APPROVED -> CANCELLED`, falha de Execution simulada `HTTP 503`, item `NOT_CREATED`, Saga `COMPENSATED`.
- Testes unitarios de compensacao: 3 aprovados em Docker local, com 1 aviso de deprecacao de dependencia.
- GitHub Actions `Phase 4 - Saga compensation tests`: execucao #1 aprovada no commit `6cb2c0c` (evidencia visual fornecida).
- Workflows `phase4-quality.yml` dos tres repositorios possuem limite `--cov-fail-under=80`, Ruff e build Docker; verificar resultado recente de cada workflow antes da submissao.

**Limite da evidencia:** o teste integrado injeta a falha na chamada HTTP do orquestrador, sem indisponibilizar o Deployment de Execution. Isso prova a compensacao com Billing e PostgreSQL reais, nao um teste de queda fisica de pod.

## Comandos de demonstracao (sem destruir dados)

```bash
kubectl --context kind-fiap-fase4 -n fiap-fase4 get deployments,pvc
kubectl --context kind-fiap-fase4 -n fiap-fase4 exec deployment/oficina-api -- python -m app.local_outbox_e2e
kubectl --context kind-fiap-fase4 -n fiap-fase4 exec deployment/oficina-saga-worker -- python -m app.local_saga_compensation_e2e
kubectl --context kind-fiap-fase4 -n fiap-fase4 logs deployment/oficina-saga-worker --tail=100
```

Cada teste E2E cria registros de teste adicionais. Nao executar em producao.

## Checklist antes da entrega

- [x] Tres repositorios independentes, com codigo dos microsservicos
- [x] Persistencia relacional e NoSQL demonstradas no ambiente local
- [x] REST, mensageria SQS local, outbox, Saga e compensacao demonstrados
- [x] Testes unitarios e E2E de sucesso/compensacao executados
- [x] CI de compensacao aprovado
- [ ] Confirmar execucao recente verde dos tres quality gates de 80% + lint + build
- [ ] Confirmar BDD executavel e guardar saida/capturas
- [ ] Confirmar endpoint Swagger/OpenAPI de cada servico e registrar capturas
- [ ] Consolidar observabilidade (logs, metricas, traces) com evidencias
- [ ] Gravar video de demonstracao de ate 15 minutos
- [ ] Conferir rubric/edital oficial e formatar PDF final com evidencias e links

## Roteiro sugerido para video (ate 15 minutos)

1. 0:00-1:30: objetivo e separacao dos tres repositorios.
2. 1:30-4:00: arquitetura, bases independentes e mensageria.
3. 4:00-7:00: demonstracao E2E de sucesso e deduplicacao.
4. 7:00-9:30: demonstracao da compensacao.
5. 9:30-12:00: Kubernetes, Deployments, PVCs, healthchecks e logs.
6. 12:00-14:00: GitHub Actions, cobertura, qualidade e Swagger.
7. 14:00-15:00: conclusoes e links de entrega.

## Seguranca operacional

Nao executar `kubectl delete pvc`, `kind delete cluster` ou `docker volume prune`. Nao habilitar `ENABLE_DEPLOY` nem provisionar AWS para demonstracao local.
