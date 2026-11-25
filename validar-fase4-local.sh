#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
COMPOSE=(docker compose -f compose.local.yml --profile emulators)

echo "[1/5] Validating Docker Compose..."
"${COMPOSE[@]}" config --quiet

echo "[2/5] Starting local stack (no AWS)..."
"${COMPOSE[@]}" up -d --build

echo "[3/5] Testing complete API -> outbox -> SQS -> Saga..."
"${COMPOSE[@]}" exec -T oficina-api python -m app.local_outbox_e2e

echo "[4/5] Testing mock payment through HTTP..."
"${COMPOSE[@]}" exec -T oficina-api python -m app.local_payment_mock_e2e

echo "[5/5] Checking service health..."
for port in 8000 8001 8002; do
  curl -fsS "http://127.0.0.1:${port}/health" >/dev/null
  echo "Port ${port}: healthy"
done

echo "PASS: local Saga + mock payments + service health."
echo "NOTE: no real Mercado Pago payment, CI coverage or Kubernetes deploy was verified."
