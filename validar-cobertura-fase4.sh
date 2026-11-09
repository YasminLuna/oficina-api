#!/usr/bin/env bash
# Run from any directory: bash ~/fiap-local/oficina-api/validar-cobertura-fase4.sh
# No Docker volumes, cloud resources or production data are touched.
set -uo pipefail
ROOT="${HOME}/fiap-local"
OUT="${ROOT}/fase4-cobertura"
mkdir -p "$OUT"
overall=0

for repo in oficina-api oficina-billing-service oficina-execution-service; do
  echo ""
  echo "================ ${repo} ================"
  dir="${ROOT}/${repo}"
  if [[ ! -d "$dir/.git" ]]; then
    echo "ERROR: repository not found: $dir"
    overall=1
    continue
  fi
  (
    cd "$dir" || exit 1
    echo "Branch: $(git branch --show-current)"
    echo "Updating from GitHub..."
    git pull --ff-only || exit 1
    if [[ ! -x .venv-fase4/bin/python ]]; then
      python3 -m venv .venv-fase4 || exit 1
    fi
    .venv-fase4/bin/python -m pip install --disable-pip-version-check -q -r requirements-dev.txt || exit 1
    .venv-fase4/bin/python -m pytest tests -q \
      --cov=app --cov-report=term-missing \
      --cov-report="xml:${OUT}/${repo}-coverage.xml" \
      --cov-fail-under=80
  ) 2>&1 | tee "${OUT}/${repo}-test.log"
  status=${PIPESTATUS[0]}
  if [[ "$status" -ne 0 ]]; then
    echo "FAIL: ${repo} (exit code ${status})"
    overall=1
  else
    echo "PASS: ${repo} reached 80% coverage"
  fi
done

echo ""
echo "Coverage evidence and logs: $OUT"
if [[ "$overall" -ne 0 ]]; then
  echo "ATTENTION: one or more repositories failed; inspect the logs above."
else
  echo "PASS: all three repositories passed tests and 80% coverage."
fi
exit "$overall"
