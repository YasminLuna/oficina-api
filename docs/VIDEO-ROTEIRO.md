# Roteiro do vídeo — Fase 3

Objetivo: vídeo público ou não listado, com duração máxima de 15 minutos.

## 0:00–1:00 — Contexto e arquitetura

Mostrar rapidamente o diagrama de componentes e explicar:

- API Gateway como entrada;
- Lambda para autenticação por CPF;
- EKS para a aplicação;
- RDS PostgreSQL privado;
- Datadog para observabilidade;
- quatro repositórios e deploy independente.

## 1:00–3:30 — CI/CD e infraestrutura

Mostrar os quatro repositórios e uma execução verde dos pipelines. No repositório Kubernetes, mostrar Terraform e o cluster EKS. No repositório de banco, mostrar RDS e Secrets Manager.

## 3:30–6:00 — Autenticação CPF/JWT

1. Fazer `POST /auth/token` pelo API Gateway com um CPF cadastrado.
2. Mostrar o JWT retornado.
3. Tentar uma rota protegida sem token e mostrar `401`.
4. Repetir com `Authorization: Bearer <token>` e mostrar sucesso.

## 6:00–8:30 — Fluxo de Ordem de Serviço

1. Criar uma OS.
2. Listar OS em andamento.
3. Alterar o status ao menos duas vezes.
4. Explicar que cada transição grava `order_status_history` e alimenta a métrica de duração por status.

## 8:30–11:30 — Kubernetes e escala

Mostrar:

- pods do namespace `oficina`;
- Deployment;
- requests/limits;
- probes `/health` e `/ready`;
- HPA com CPU/memória;
- Service LoadBalancer.

## 11:30–14:00 — Datadog

Mostrar dashboard ao vivo com:

- latência;
- volume de requisições;
- CPU/memória;
- health/uptime;
- volume diário de OS;
- tempo médio por status;
- erros de integração.

Abrir um log JSON, pegar o `correlation_id` e localizar o trace/requisição correspondente.

## 14:00–15:00 — Fechamento

Mostrar rapidamente RFCs, ADRs, ER e o PDF final com os quatro links. Confirmar que `main` está protegida e que `soat-architecture` foi adicionado aos quatro repositórios.
