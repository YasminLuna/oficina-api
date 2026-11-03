# Observabilidade e evidências

## Telemetria implementada

A aplicação expõe `/metrics` em formato Prometheus e envia logs JSON e traces ao Datadog Agent.

Métricas principais:

| Indicador | Métrica |
|---|---|
| Requisições HTTP | `oficina_http_requests_total` |
| Latência | `oficina_http_latency_seconds` |
| OS criadas | `oficina_orders_created_total` |
| Falhas de processamento | `oficina_order_failures_total` |
| Erros de integração | `oficina_integration_errors_total` |
| Tempo por status | `oficina_order_status_duration_seconds` |
| Transições de status | `oficina_order_status_changes_total` |

## Dashboard mínimo da Fase 3

Criar um dashboard `FIAP - Oficina Fase 3` com os seguintes widgets:

1. **Latência da API** — p95 por endpoint usando APM ou a métrica `oficina_http_latency_seconds`.
2. **Tráfego HTTP** — requisições por status code.
3. **CPU Kubernetes** — uso de CPU dos pods `oficina-api` no namespace `oficina`.
4. **Memória Kubernetes** — uso de memória dos pods `oficina-api`.
5. **Health / uptime** — monitor HTTP para `/health` e `/ready`.
6. **Volume diário de OS** — delta/contagem de `oficina_orders_created_total` por dia.
7. **Tempo médio por status** — média da métrica `oficina_order_status_duration_seconds` agrupada por `status`.
8. **Erros de integração** — soma de `oficina_integration_errors_total` agrupada por `integration` e `operation`.
9. **Logs da aplicação** — filtro `service:oficina-api`, exibindo `correlation_id`, `path`, `status_code` e `duration_ms`.
10. **Traces** — serviço `oficina-api`, recurso FastAPI, com latência e erros.

## Evidências recomendadas para o vídeo

- abrir o dashboard com dados chegando em tempo real;
- executar uma chamada `/health` e localizar o log correspondente;
- executar autenticação e chamada protegida;
- copiar o `x-correlation-id` da resposta e pesquisar esse mesmo valor nos logs;
- mostrar um trace de uma requisição da API;
- mostrar CPU/memória do pod e o objeto HPA;
- mostrar contagem de OS e duração de uma mudança de status.

## Alertas

Configurar monitores para:

- `/health` indisponível por 2 minutos;
- taxa de 5xx maior que 5% por 5 minutos;
- p95 de latência acima de 1 segundo por 5 minutos;
- pod indisponível/CrashLoopBackOff;
- CPU acima de 80% ou memória acima de 85% por 10 minutos.
