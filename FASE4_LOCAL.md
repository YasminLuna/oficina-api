# Fase 4 — execução local e Saga

## Arquitetura
- **Oficina API**: FastAPI e PostgreSQL, porta 8000.
- **Billing**: FastAPI e SQLite persistente, porta 8001.
- **Execution**: FastAPI e DynamoDB Local persistente, porta 8002.
- **Saga Worker**: orquestrador Python, fila SQS `oficina-orders`, estado `local_sagas` em PostgreSQL.
- **LocalStack**: SQS local, porta 4566, com filas e DLQs criadas pelo serviço `sqs-init`.
- Não são necessários credenciais ou recursos AWS reais.

## Inicialização
Clone os três repositórios como irmãos em `~/fiap-local`. Na pasta `oficina-api`:

```bash
docker compose -f compose.local.yml --profile emulators up -d --build
docker compose -f compose.local.yml --profile emulators ps
docker compose -f compose.local.yml logs --tail=30 sqs-init saga-worker
```

Não use `down -v`: isso apaga os volumes locais.

## Teste ponta a ponta
```bash
ORDER_ID="os-fiap-$(date +%s)"
docker compose -f compose.local.yml exec -T saga-worker python -m app.local_saga_demo "$ORDER_ID" 150.00
sleep 15
curl -fsS "http://localhost:8001/quotes/$ORDER_ID"
curl -fsS "http://localhost:8002/work-items/$ORDER_ID"
docker compose -f compose.local.yml exec -T postgres-os psql -U oficina -d oficina_os -c "SELECT order_id,state,error FROM local_sagas ORDER BY order_id DESC LIMIT 10;"
```

Resultados esperados: Billing `APPROVED`, Execution `COMPLETED`, Saga `COMPLETED`.

## Testes unitários
```bash
docker compose -f compose.local.yml exec -T saga-worker python -m unittest discover -s tests -p 'test_local_saga.py'
```

## Semântica de compensação
Se ocorrer falha antes do início da execução, o orquestrador tenta cancelar o work-item `QUEUED` e o orçamento `PENDING`/`APPROVED`. Se conseguir, grava `COMPENSATED`. Se a execução já iniciou, ou uma compensação falhar, grava `COMPENSATION_REQUIRED`, exigindo análise operacional. Cancelar o orçamento **não** realiza estorno financeiro. Mensagens de Saga terminal são ignoradas. SQS possui DLQ com três recebimentos máximos.

## Limitações conhecidas
Este ambiente é um protótipo local de integração. O evento `ORDER_CREATED` é publicado automaticamente quando a API recebe uma solicitação de orçamento com valor; criar uma OS sem orçamento não dispara cobrança. Permanecem pendentes: concorrência robusta entre consumidores, testes de caos em containers, Kubernetes local, observabilidade distribuída e conferência das evidências exigidas pelo edital. Não afirmar prontidão de produção.


## Integração real API → Saga (outbox local)
A criação da OS em `POST /api/v1/orders` não informa preço. Por isso a publicação automática ocorre **quando um orçamento com valor é solicitado** via `POST /api/v1/orders/{order_id}/request-quote` (body `{"amount":"150.00"}`, JWT do cliente proprietário). A requisição grava um evento na mesma transação PostgreSQL; `outbox-dispatcher` envia para a fila `oficina-orders`. A Saga realiza Billing e Execution. Pedidos repetidos com mesmo valor reutilizam o evento; outro valor retorna HTTP 409. A entrega é *at least once*, com deduplicação por estado de Saga. Para testar, primeiro crie cliente, obtenha token local conforme o fluxo de autenticação do projeto e crie uma OS.

A inicialização de `order_event_outbox` usa `Base.metadata.create_all` na API local; em produção, substituir por migração versionada Alembic. A transição de estado da OS não está sincronizada automaticamente com o estado da Saga. Não utilizar em produção sem revisão de segurança, recuperação e autorização.


## Teste automatizado da integração API → Outbox → SQS → Saga
Após subir o Compose com `--profile emulators`, execute:

```bash
docker compose -f compose.local.yml --profile emulators exec -T oficina-api python -m app.local_outbox_e2e
```

O teste cria um cliente de teste no banco local, autentica a chamada com JWT local, cria OS via API, solicita orçamento, repete a solicitação para verificar idempotência e aguarda até 90 segundos a publicação e conclusão da Saga. Esperado: `result: PASS`, `outbox: PUBLISHED`, `saga: COMPLETED`, `billing: APPROVED`, `execution: COMPLETED`. O teste não acessa AWS real. Testes de falhas de infraestrutura e os requisitos do enunciado oficial permanecem pendentes de validação.
