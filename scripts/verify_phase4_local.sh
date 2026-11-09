#!/usr/bin/env bash
# Read-only Phase 4 Kubernetes verification. Does not mutate resources.
set -euo pipefail
CTX=kind-fiap-fase4
NS=fiap-fase4
K=(kubectl --context "$CTX" -n "$NS")
echo "=== Deployments and persistent claims ==="
"${K[@]}" get deployments,pvc
echo "=== API health, OpenAPI and Prometheus ==="
"${K[@]}" exec deployment/oficina-api -- python -c '
import json
from urllib.request import urlopen
for path in ("/health", "/openapi.json", "/metrics"):
    with urlopen("http://127.0.0.1:8000"+path, timeout=8) as response:
        body=response.read().decode()
        assert response.status==200, path
        if path=="/openapi.json":
            doc=json.loads(body)
            assert doc.get("paths"), "OpenAPI missing paths"
            print(path, "PASS", len(doc["paths"]), "documented paths")
        elif path=="/metrics":
            assert "# HELP" in body or "# TYPE" in body, "Prometheus exposition missing"
            print(path, "PASS", len(body), "bytes")
        else:
            print(path, "PASS", body[:120])
'
echo "=== Billing and Execution health and OpenAPI ==="
for deployment in oficina-billing-service oficina-execution-service; do
  "${K[@]}" exec "deployment/$deployment" -- python -c '
import json
from urllib.request import urlopen
for path in ("/health", "/openapi.json"):
    with urlopen("http://127.0.0.1:8080"+path, timeout=8) as response:
        data=json.load(response)
        assert response.status==200
        if path=="/openapi.json":
            assert data.get("paths")
            print(path, "PASS", len(data["paths"]), "documented paths")
        else:
            print(path, "PASS", data)
'
done
echo "=== Saga logs ==="
"${K[@]}" logs deployment/oficina-saga-worker --tail=30
echo "Verification finished; no resources modified."
