# Arquitetura — Tech Challenge Fase 3

## Visão de componentes

```mermaid
flowchart LR
    U[Cliente / Postman] --> G[Amazon API Gateway HTTP API]
    G -->|POST /auth/token| L[AWS Lambda Auth CPF]
    L --> R[(Amazon RDS PostgreSQL)]
    G -->|demais rotas| LB[AWS Load Balancer]
    LB --> EKS[Amazon EKS]
    EKS --> API[FastAPI Oficina]
    API --> R
    EKS --> DD[Datadog Agent]
    API --> DD
    DD --> DDC[Datadog Cloud]
    GH[GitHub Actions] --> TF[Terraform]
    TF --> EKS
    TF --> R
    GH --> ECR[Amazon ECR]
    ECR --> EKS
```

## Fluxo de autenticação por CPF

```mermaid
sequenceDiagram
    actor C as Cliente
    participant G as API Gateway
    participant L as Lambda Auth
    participant DB as PostgreSQL RDS

    C->>G: POST /auth/token {cpf}
    G->>L: Evento HTTP
    L->>L: Normaliza e valida CPF
    L->>DB: Busca cliente por document
    DB-->>L: Cliente + status ativo
    alt cliente existente e ativo
        L->>L: Gera JWT HS256 (60 min)
        L-->>G: 200 + access_token
        G-->>C: JWT
    else CPF inválido/inexistente/inativo
        L-->>G: 401/403
        G-->>C: Erro de autenticação
    end
```

## Fluxo de abertura de Ordem de Serviço

```mermaid
sequenceDiagram
    actor C as Cliente
    participant G as API Gateway
    participant A as FastAPI no EKS
    participant DB as PostgreSQL RDS
    participant DD as Datadog

    C->>G: POST /api/v1/orders + Bearer JWT
    G->>A: Proxy HTTP
    A->>A: Valida assinatura/issuer JWT
    A->>DB: Confirma cliente ativo
    DB-->>A: Cliente
    A->>DB: Cria service_order
    A->>DB: Cria status_history = Recebida
    A->>DD: Trace + métricas + log JSON
    A-->>G: 200/201 + OS
    G-->>C: Resposta
```

## Decisões principais

- API Gateway é o ponto de entrada público e separa o fluxo serverless de autenticação do backend Kubernetes.
- A Lambda valida CPF, existência e situação do cliente e emite JWT.
- A aplicação FastAPI valida o JWT novamente nas rotas sensíveis.
- PostgreSQL é privado na VPC; Lambda e workloads do EKS acessam o banco pela rede da VPC.
- EKS executa a aplicação com requests/limits, probes e HPA.
- Logs são JSON e carregam `x-correlation-id`; métricas e traces são enviados ao Datadog.
- Terraform mantém infraestrutura reprodutível e o state é persistido em S3 versionado e criptografado.
