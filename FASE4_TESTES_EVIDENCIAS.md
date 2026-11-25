# Etapa 1 — Testes, cobertura e BDD

## Escopo

O objetivo é comprovar **80% de cobertura por microsserviço**, e não apenas executar testes isolados. Os três repositórios usam `pytest-cov`, com `--cov=app --cov-fail-under=80`.

- `oficina-api`: testes de autorização, ordens, Outbox e Saga; BDD executável em `tests/test_phase4_bdd.py`.
- `oficina-billing-service`: testes da API SQLite e do adaptador de pagamento mock.
- `oficina-execution-service`: testes da API DynamoDB, repositório e fluxos de execução.

## Validação local — um comando

```bash
cd ~/fiap-local/oficina-api
git pull --ff-only
bash validar-cobertura-fase4.sh
```

O script atualiza os três repositórios, cria `.venv-fase4` em cada um, executa os testes e salva logs e relatórios XML em `~/fiap-local/fase4-cobertura/`.

**Atenção:** os commits e os testes foram preparados remotamente. Os percentuais de cobertura e o status PASS só podem ser declarados após executar a suíte; um commit não é prova de 80%.

## Evidências exigidas

Para cada serviço, guardar:
1. Log do pytest com `TOTAL` e percentual de cobertura.
2. Arquivo `*-coverage.xml`.
3. URL do GitHub Actions com checks aprovados.
4. Testes BDD com nomes Given/When/Then, incluindo sucesso, compensação e deduplicação.

## Limites

- Os testes BDD usam doubles/mocks para demonstrar a lógica de orquestração; o teste `app.local_outbox_e2e` verifica a integração local real com SQS e bancos.
- O mock de Mercado Pago não comprova liquidação financeira.
- A validação local não substitui comprovação de deploy Kubernetes nem de execução do CI/CD.
- Não executar `docker compose down -v`; não é necessário limpar volumes para esses testes.
