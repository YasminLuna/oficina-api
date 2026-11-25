# Oficina API — FIAP Tech Challenge Fase 4

Serviço de ordens de serviço e coordenação transacional da oficina. Esta branch contém a evolução distribuída da Fase 4; a documentação histórica da Fase 3 continua relevante para a infraestrutura cloud.

## Arquitetura e responsabilidades

- **Oficina API:** recebe requisições REST, mantém dados de ordens e registra eventos em PostgreSQL (transactional outbox).
- **Outbox Dispatcher:** publica eventos no SQS emulado pelo LocalStack.
- **Saga Worker:** consome eventos e orquestra chamadas REST para Billing e Execution, persistindo o estado da Saga em PostgreSQL.
- **Billing:** serviço independente, com SQLite persistente e adaptador de pagamento Mercado Pago.
- **Execution:** serviço independente, com DynamoDB Local.

A escolha foi **Saga orquestrada**: centraliza a sequência e o estado das etapas de uma OS, facilita rastreabilidade e implementa compensação quando uma etapa posterior falha. O padrão outbox reduz a janela entre persistência e publicação; eventos duplicados são tratados por deduplicação. Os serviços comunicam-se por REST e mensageria; não acessam diretamente os bancos uns dos outros.

## Repositórios

- API: https://github.com/YasminLuna/oficina-api
- Billing: https://github.com/YasminLuna/oficina-billing-service
- Execution: https://github.com/YasminLuna/oficina-execution-service

## Evidências e execução

Relatório técnico, diagrama Mermaid, comandos de demonstração e limitações: [docs/FASE4_ENTREGA.md](docs/FASE4_ENTREGA.md).

Em 09/11/2026, o ambiente local kind `fiap-fase4` apresentou 8/8 Deployments disponíveis e 3/3 PVCs Bound. Testes E2E de sucesso, deduplicação e compensação passaram; a falha HTTP 503 de Execution foi **injetada no cliente HTTP da Saga**, não houve queda física de pod.

**Qualidade local:** 54 testes aprovados, cobertura **83,47%**. **CI:** [API Phase 4 - quality and image #33](https://github.com/YasminLuna/oficina-api/actions/workflows/phase4-quality.yml) aprovado no commit `7c2f71d`; workflow de BDD/Saga também aprovado. O workflow da API valida Ruff, cobertura >=80% e build Docker sem publicação.

```bash
kubectl --context kind-fiap-fase4 -n fiap-fase4 get deployments,pvc
kubectl --context kind-fiap-fase4 -n fiap-fase4 exec deployment/oficina-api -- python -m app.local_outbox_e2e
kubectl --context kind-fiap-fase4 -n fiap-fase4 exec deployment/oficina-saga-worker -- python -m app.local_saga_compensation_e2e
```

Esses testes criam registros adicionais: executar somente no ambiente de demonstração. Não apagar PVCs ou volumes para repetir o teste.

## API e observabilidade

No ambiente local, `/health`, `/openapi.json` e `/metrics` foram verificados. A disponibilidade de `/metrics` não prova coleta externa nem tracing distribuído.

## Pendências de aderência ao edital

O [enunciado oficial da Fase 4](docs/FASE4_ENTREGA.md) exige deploy **automatizado em Kubernetes** por serviço, proteção de `main` com PR e checagens, evidências de observabilidade e vídeo. O workflow `phase4-quality.yml` atual **não faz deploy**; não declarar esse requisito como concluído. Não habilitar AWS paga sem autorização.
