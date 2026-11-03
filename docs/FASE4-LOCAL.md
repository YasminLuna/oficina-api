# FIAP Fase 4 — execução local sem AWS

## Pré-requisitos
Docker Desktop com Compose v2 e Git. No Mac Apple Silicon, habilite o Docker Desktop.

Clone os três repositórios como diretórios irmãos:
```sh
mkdir -p fiap-local && cd fiap-local
git clone -b feature/fase4-microservices https://github.com/YasminLuna/oficina-api.git
git clone -b feature/fase4-service https://github.com/YasminLuna/oficina-billing-service.git
git clone -b feature/fase4-service https://github.com/YasminLuna/oficina-execution-service.git
cd oficina-api
docker compose -f compose.local.yml up --build -d
docker compose -f compose.local.yml ps
curl -f http://localhost:8000/health
curl -f http://localhost:8001/health
curl -f http://localhost:8002/health
```

Swagger: OS http://localhost:8000/docs ; Billing http://localhost:8001/docs ; Execution http://localhost:8002/docs.

Para incluir emuladores locais (ainda **não integrados** às APIs):
```sh
docker compose -f compose.local.yml --profile emulators up --build -d
```

Parar sem apagar os dados PostgreSQL:
```sh
docker compose -f compose.local.yml down
```

Apagar o banco local (irreversível):
```sh
docker compose -f compose.local.yml down -v
```

## Estado real e limitações
- Oficina API: PostgreSQL persistente em volume Docker, autenticação JWT ainda depende de um emissor de token compatível. O serviço Auth Lambda da AWS **não é executado** aqui.
- Billing: API atual mantém orçamentos **em memória**. Adaptador SQL é experimental e não está ligado às rotas.
- Execution: API padrão mantém fila **em memória**. Adaptador DynamoDB e API persistente são experimentais, não ligados ao compose.
- LocalStack emula SQS, mas ainda não há integração ponta a ponta com Saga e compensações.
- Não há Kubernetes local nem observabilidade integrada neste primeiro incremento.
- Imagens Docker são baixadas da internet, mas nenhuma conta ou recurso AWS é utilizado.
- Senhas e portas deste compose são **exclusivas para desenvolvimento local**.

## Próximos incrementos
1. Persistência SQL própria do Billing e DynamoDB Local para Execution.
2. Mensageria SQS emulada, consumidores, idempotência e Saga com compensações.
3. Autenticação local, testes BDD e cobertura >=80% por serviço.
4. Manifests para kind, métricas, tracing e dashboards locais.

Nenhum `terraform apply` ou deploy AWS deve ser executado.
