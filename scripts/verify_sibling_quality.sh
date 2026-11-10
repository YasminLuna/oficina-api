#!/usr/bin/env bash
# Read-only quality gates for the two sibling repositories. No AWS or Kubernetes operations.
set -euo pipefail
ROOT="${1:-$HOME/fiap-local}"
for service in oficina-billing-service oficina-execution-service; do
  path="$ROOT/$service"
  if [[ ! -f "$path/requirements-dev.txt" ]]; then
    echo "Missing repository: $path" >&2
    exit 1
  fi
  echo "=== $service: lint, tests, coverage >= 80% ==="
  docker run --rm --user 0 --entrypoint sh \
    -v "$path:/workspace:ro" -w /workspace \
    -e PYTHONDONTWRITEBYTECODE=1 \
    -e PYTHONPATH=/workspace \
    -e COVERAGE_FILE=/tmp/.coverage \
    -e AWS_EC2_METADATA_DISABLED=true \
    -e AWS_ACCESS_KEY_ID=local \
    -e AWS_SECRET_ACCESS_KEY=local \
    -e AWS_DEFAULT_REGION=us-east-1 \
    python:3.13-slim \
    -c 'set -eu; python -m pip install --no-cache-dir --quiet -r requirements-dev.txt ruff==0.13.0 PyYAML==6.0.2; ruff check --select E4,E7,E9,F app tests; python -m pytest -p no:cacheprovider -q --cov=app --cov-report=term-missing --cov-fail-under=80; python -c '\''import yaml; docs=list(yaml.safe_load_all(open("k8s/local-service.yaml"))); assert {"Deployment","Service"} <= {d["kind"] for d in docs if d}; print("Kubernetes YAML valid")'\'''
done
echo "Both service quality gates passed."
