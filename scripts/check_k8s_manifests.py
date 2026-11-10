"""Static, offline Kubernetes manifest checks for the three local microservices.

This is a structural check, not evidence of a working Kubernetes deployment.
"""
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]
SERVICES = {
    "oficina-api": 8000,
    "oficina-billing-service": 8080,
    "oficina-execution-service": 8080,
}

def main():
    for name, port in SERVICES.items():
        manifest = ROOT / name / "k8s" / "local-service.yaml"
        docs = [d for d in yaml.safe_load_all(manifest.read_text()) if d]
        deployment = next((d for d in docs if d.get("kind") == "Deployment"), None)
        service = next((d for d in docs if d.get("kind") == "Service"), None)
        assert deployment and service, f"{name}: Deployment/Service missing"
        assert deployment["metadata"]["name"] == name
        assert service["metadata"]["name"] == name
        spec = deployment["spec"]["template"]["spec"]
        container = spec["containers"][0]
        assert container["image"] == f"{name}:local"
        assert container["imagePullPolicy"] == "Never"
        assert container["ports"][0]["containerPort"] == port
        assert service["spec"]["ports"][0]["targetPort"] == port
        assert container.get("livenessProbe") and container.get("readinessProbe")
        assert container["resources"]["requests"] and container["resources"]["limits"]
        print(f"PASS: {name} manifest structure")
    print("PASS: three Kubernetes manifest checks (static only)")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise
