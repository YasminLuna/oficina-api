# FIAP — Tech Challenge Fase 3

## Repositórios

1. Autenticação serverless: https://github.com/YasminLuna/oficina-auth-serverless
2. Infraestrutura Kubernetes: https://github.com/YasminLuna/oficina-k8s-infra
3. Infraestrutura de banco de dados: https://github.com/YasminLuna/oficina-db-infra
4. Aplicação principal: https://github.com/YasminLuna/oficina-api

## Documentação

- [Arquitetura e diagramas](docs/ARQUITETURA.md)
- [RFC — Arquitetura Cloud](docs/RFC-001-ARQUITETURA-CLOUD.md)
- [RFC — Modelo de dados](docs/RFC-002-MODELO-DADOS.md)
- [ADR — HPA](docs/ADR-001-HPA.md)
- [ADR — Observabilidade](docs/ADR-002-OBSERVABILIDADE.md)
- [Observabilidade e dashboard](docs/OBSERVABILIDADE.md)
- [Roteiro do vídeo](docs/VIDEO-ROTEIRO.md)

## Endpoints de homologação

Preencher após o deploy final:

- API Gateway: `PREENCHER_APIGATEWAY_URL`
- Auth: `PREENCHER_AUTH_URL`
- Swagger: `PREENCHER_SWAGGER_URL`
- Health: `PREENCHER_HEALTH_URL`

## Vídeo

`PREENCHER_URL_VIDEO_PUBLICO_OU_NAO_LISTADO`

## Checklist final

- [ ] Os quatro repositórios estão acessíveis para avaliação.
- [ ] `main` está protegida e alterações exigem Pull Request.
- [ ] Usuário/equipe `soat-architecture` possui acesso aos quatro repositórios.
- [ ] CI/CD está verde nos quatro repositórios.
- [ ] EKS, RDS, Lambda e API Gateway estão ativos para a demonstração.
- [ ] Autenticação por CPF retorna JWT válido.
- [ ] Rota protegida rejeita chamada sem JWT e aceita JWT válido.
- [ ] HPA, health e readiness estão demonstráveis.
- [ ] Datadog recebe métricas, logs e traces.
- [ ] Dashboard contém os indicadores solicitados.
- [ ] Vídeo possui no máximo 15 minutos.
- [ ] PDF final contém os quatro links, vídeo e documentação.
