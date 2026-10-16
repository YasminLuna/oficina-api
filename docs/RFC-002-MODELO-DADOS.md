# RFC-002 — Evolução do modelo de dados

## Status
Aceita.

## Problema
Somente o status atual da Ordem de Serviço não permite responder quanto tempo uma OS permaneceu em cada etapa. Esse dado é necessário para identificar gargalos e alimentar o dashboard de tempo médio por status.

## Decisão
Manter o modelo relacional PostgreSQL e adicionar a entidade `order_status_history`.

```mermaid
erDiagram
    CUSTOMERS ||--o{ SERVICE_ORDERS : possui
    SERVICE_ORDERS ||--o{ ORDER_STATUS_HISTORY : registra

    CUSTOMERS {
      string id PK
      string document UK
      string name
      boolean active
    }

    SERVICE_ORDERS {
      string id PK
      string customer_id FK
      string vehicle_plate
      enum status
      datetime created_at
    }

    ORDER_STATUS_HISTORY {
      string id PK
      string order_id FK
      enum status
      datetime entered_at
      datetime exited_at
    }
```

## Justificativa
`service_orders.status` continua sendo a leitura rápida do estado corrente. `order_status_history` preserva cada transição, permitindo calcular duração por etapa sem sobrecarregar o registro principal da OS.

A duração de uma etapa concluída é `exited_at - entered_at`. A etapa corrente mantém `exited_at = NULL`.

## Consequências
O modelo passa a suportar análise operacional, tempo médio por status, investigação de gargalos e auditoria da evolução da OS. A aplicação atualiza o registro corrente e o histórico dentro da mesma transação.
