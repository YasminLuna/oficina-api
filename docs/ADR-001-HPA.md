# ADR-001 — Horizontal Pod Autoscaler

## Status
Aceita.

## Contexto
A API deve permanecer responsiva sob variação de carga e demonstrar capacidade de escala no Kubernetes.

## Decisão
Utilizar HPA `autoscaling/v2` com CPU e memória:

- mínimo: 1 réplica;
- máximo: 3 réplicas;
- alvo de CPU: 60%;
- alvo de memória: 70%;
- janela de estabilização de scale-down: 120 segundos.

O Deployment define requests de 100m CPU/128Mi e limits de 500m CPU/512Mi. O cluster instala `metrics-server` para fornecer métricas de recursos ao HPA.

## Consequências
O workload consegue reagir a pressão de CPU/memória e o comportamento é reproduzível no ambiente acadêmico. A escala máxima foi limitada para controlar custo e capacidade do node group.
