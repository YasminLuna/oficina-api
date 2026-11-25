# Fase 4 — núcleo inicial da Saga

Este diretório contém **um protótipo testável da máquina de estados**, não uma Saga distribuída completa.

- `saga.py` define os estados, eventos e transições permitidas para a jornada da OS.
- `tests/test_fase4_saga.py` cobre fluxo feliz, rejeição de orçamento, falha de pagamento, falha de execução e transições inválidas.
- Os estados `CANCELLED` e `FAILED` **não executam compensações externas**. Ainda faltam comandos de compensação reais, idempotência, persistência, outbox, mensageria, retries, DLQ e rastreamento.
- Nenhuma cobrança é efetuada neste código; a integração Mercado Pago depende de credenciais seguras e testes em sandbox.
- Este código fica em staging até a extração para repositórios de serviços independentes e a validação de cobertura por serviço.

Execução local a partir da raiz: `python -m unittest tests/test_fase4_saga.py` (ou `pytest tests/test_fase4_saga.py`, se pytest estiver instalado).
