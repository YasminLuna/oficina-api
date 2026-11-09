"""Local Kubernetes integration test for Saga compensation.

Runs in the saga-worker container, with real PostgreSQL and Billing HTTP.
Only the Execution creation request is replaced with a deterministic failure.
Never run against production services.
"""
import json
import os
import uuid

from . import local_saga_worker as saga


def main():
    endpoint = os.environ.get("SQS_ENDPOINT_URL", "")
    if not endpoint.startswith("http://localstack:4566"):
        raise RuntimeError("Refusing to run outside the local Kubernetes environment")

    order_id = str(uuid.uuid4())
    amount = "150.00"
    billing_url = "http://billing:8080/quotes/" + order_id
    execution_url = "http://execution:8080/work-items/" + order_id
    original_http = saga.http
    observed = {"billing_approved_before_failure": False, "injected_failure": False}

    def controlled_http(method, url, body=None):
        if method == "POST" and url == "http://execution:8080/work-items":
            _, quote_id = url, body["order_id"]
            if quote_id == order_id:
                quote = original_http("GET", billing_url)
                assert quote["state"] == "APPROVED", quote
                observed["billing_approved_before_failure"] = True
                observed["injected_failure"] = True
                raise RuntimeError("POST execution: HTTP 503: controlled integration-test failure")
        return original_http(method, url, body)

    saga.initialize()
    saga.http = controlled_http
    try:
        saga.run_saga({"event_type": "ORDER_CREATED", "order_id": order_id, "amount": amount})
    finally:
        saga.http = original_http

    final_state = saga.state(order_id)
    quote = original_http("GET", billing_url)
    try:
        original_http("GET", execution_url)
    except RuntimeError as exc:
        assert "HTTP 404" in str(exc), str(exc)
        execution_state = "NOT_CREATED"
    else:
        raise AssertionError("Execution work item unexpectedly exists")

    assert observed["billing_approved_before_failure"]
    assert observed["injected_failure"]
    assert final_state == "COMPENSATED", final_state
    assert quote["state"] == "CANCELLED", quote

    print(json.dumps({
        "result": "PASS",
        "order_id": order_id,
        "billing_before_failure": "APPROVED",
        "injected_execution_failure": "HTTP 503",
        "billing_after_compensation": quote["state"],
        "execution": execution_state,
        "saga": final_state,
    }, indent=2))


if __name__ == "__main__":
    main()
