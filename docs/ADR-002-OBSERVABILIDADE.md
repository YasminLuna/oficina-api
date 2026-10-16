# ADR-002 — Observabilidade com Datadog

## Status
Aceita.

## Contexto
A Fase 3 exige acompanhar latência da API, CPU/memória Kubernetes, health/uptime, logs estruturados, traces, alertas e indicadores de Ordens de Serviço.

## Decisão
Adotar Datadog com Agent no EKS e instrumentação APM da aplicação.

A aplicação fornece:

- logs JSON em stdout;
- `x-correlation-id` propagado na resposta e presente nos logs;
- traces FastAPI via `ddtrace`;
- endpoint Prometheus `/metrics` coletado pelo Agent via OpenMetrics;
- métricas de requisição/latência;
- contador de OS criadas;
- erros de integração;
- mudanças de status;
- duração das OS em cada status.

O Kubernetes fornece métricas de CPU/memória, estado de pods, deployments e HPA por meio do Agent, Cluster Agent e kube-state-metrics core.

## Alertas
A configuração de observabilidade deve possuir pelo menos:

1. API indisponível / healthcheck falhando;
2. taxa elevada de respostas 5xx;
3. latência acima do limite esperado;
4. pod em CrashLoopBackOff ou indisponível;
5. CPU ou memória sustentada em nível alto.

## Consequências
Métricas, traces e logs podem ser correlacionados por serviço, ambiente e correlation ID, reduzindo tempo de diagnóstico e permitindo demonstração visual dos requisitos da fase.
