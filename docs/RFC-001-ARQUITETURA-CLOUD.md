# RFC-001 — Arquitetura Cloud da Oficina

## Status
Aceita.

## Contexto
A Fase 3 exige API Gateway, função serverless para autenticação, banco gerenciado, cluster Kubernetes escalável, infraestrutura como código e CI/CD independente por repositório.

## Decisão
Adotar AWS como provedor principal, com os seguintes serviços:

- Amazon API Gateway HTTP API para entrada pública.
- AWS Lambda para autenticação por CPF e emissão de JWT.
- Amazon EKS para execução da API principal.
- Amazon RDS for PostgreSQL para persistência relacional.
- Amazon ECR para imagens da aplicação.
- AWS Secrets Manager para credenciais de banco e segredo JWT.
- Amazon S3 para o state remoto do Terraform.
- Datadog para logs, métricas, APM e dashboards.

## Consequências
A solução fica aderente aos requisitos da fase e demonstra integração entre serverless, Kubernetes e serviços gerenciados. O principal trade-off é custo operacional do EKS; por isso o ambiente acadêmico usa um node `t3.medium`, HPA e não utiliza NAT Gateway.

## Alternativas avaliadas
Kong/Traefik poderiam cumprir o papel de gateway e um PostgreSQL no próprio cluster reduziria serviços AWS, porém diminuiria a aderência ao requisito de banco gerenciado e aumentaria a responsabilidade operacional da solução.
