# FIAP Tech Challenge — Fase 4: auditoria de entrega

Referência: enunciado "SOAT - Fase 4 - Tech challenge.pdf", localizado na biblioteca do projeto.

## Estado confirmado (execução local em 09/11/2026)

- Três repositórios independentes: `oficina-api`, `oficina-billing-service`, `oficina-execution-service`.
- Bancos isolados: PostgreSQL (OS), SQLite (Billing), DynamoDB Local (Execution).
- LocalStack SQS e DLQ, Saga orquestrada, outbox e idempotência.
- Teste real `python -m app.local_outbox_e2e`: PASS; outbox PUBLISHED, Saga COMPLETED, Billing APPROVED, Execution COMPLETED, evento duplicado DEDUPLICATED.
- Testes unitários de compensação no orquestrador, incluindo COMPENSATED e COMPENSATION_REQUIRED.
- OpenAPI automático disponível nos três serviços em `/docs`.

## Lacunas obrigatórias do edital — não declarar concluídas

| Requisito | Situação |
| --- | --- |
| Mercado Pago: integração de pagamentos | Não implementada no fluxo local de Billing; requer credenciais sandbox e testes de webhook, assinatura e estados de pagamento |
| Saga: aprovação humana e pagamento | Fluxo atual aprova orçamento automaticamente; deve ser adaptado ao domínio exigido |
| BDD com fluxo completo | Cenários Gherkin em `features/saga.feature`; falta runner BDD executável e relatório |
| Cobertura >=80% em CADA serviço | Ainda sem relatórios de cobertura comprovando o limiar |
| Qualidade no CI (SonarQube ou similar) | Não comprovada para todos os serviços |
| CI/CD independente + deploy Kubernetes | Oficina API possui pipeline EKS condicionado; Billing e Execution possuem CI, sem deploy confirmado |
| Manifestos Kubernetes dos três serviços | Confirmado apenas o deployment da Oficina API nesta revisão; auditar os demais |
| Proteção main / PR obrigatório | Configuração GitHub ainda não verificada |
| Observabilidade distribuída | API tem logs, métricas e Datadog; falta demonstração de rastreamento distribuído entre os três |
| Vídeo até 15 minutos | Depende de gravação e publicação pela equipe |
| PDF final com identificação, URLs e diagrama | Depende de dados dos participantes, URL do vídeo e evidências verificadas |

## Como repetir as validações sem custo de AWS

```bash
cd ~/fiap-local/oficina-api
docker compose -f compose.local.yml --profile emulators up -d --build
docker compose -f compose.local.yml --profile emulators exec -T saga-worker python -m unittest discover -s tests -p 'test_local_saga.py' -v
docker compose -f compose.local.yml --profile emulators exec -T oficina-api python -m app.local_outbox_e2e
```

Não executar `docker compose down -v`: remove dados persistidos. Os deploys AWS dos workflows devem permanecer desabilitados sem autorização explícita; deploy local Kubernetes é alternativa para evidências.

## Roteiro sugerido de vídeo (até 15 minutos)

1. (0–2 min) Arquitetura, separação dos três repositórios e bancos.
2. (2–5 min) Swagger da Oficina API, criação de OS e solicitação de orçamento.
3. (5–8 min) Outbox, SQS e estado COMPLETED da Saga; Billing e Execution.
4. (8–10 min) Falha injetada e compensação, com logs e estados persistidos.
5. (10–12 min) Pipeline independente com cobertura, qualidade e deploy Kubernetes.
6. (12–14 min) Métricas, logs e rastreamento distribuído.
7. (14–15 min) Conclusão, URLs dos repositórios e evidências.

Não apresentar etapas ainda não implementadas como concluídas.
