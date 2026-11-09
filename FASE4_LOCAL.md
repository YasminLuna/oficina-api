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
Este ambiente é um protótipo local de integração. A publicação de `ORDER_CREATED` é disparada pelo comando de demonstração, não automaticamente pela criação de OS na API principal. O domínio atual não define valor de orçamento ao criar a OS, portanto não é correto inventar o valor para disparar cobrança. Faltam integração transacional por outbox, concorrência robusta entre consumidores, testes de caos em containers, Kubernetes local, observabilidade distribuída e evidências exigidas pelo edital. Não afirmar prontidão de produção.
