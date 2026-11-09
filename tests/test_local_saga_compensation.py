"""Deterministic Saga compensation tests; no Kubernetes/AWS resources required."""
import importlib
import sys
from unittest.mock import Mock

import pytest


@pytest.fixture
def saga(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("SQS_ENDPOINT_URL", "http://localhost:4566")
    sys.modules.pop("app.local_saga_worker", None)
    module = importlib.import_module("app.local_saga_worker")
    states = {}
    module.state = lambda order_id: states.get(order_id, (None, None))[0]

    def save(order_id, amount, status, error=None):
        states[order_id] = (status, error)

    module.set_state = save
    yield module, states
    sys.modules.pop("app.local_saga_worker", None)


def test_execution_failure_compensates_approved_quote(saga):
    module, states = saga
    calls = []

    def fake_http(method, url, body=None):
        calls.append((method, url))
        if method == "POST" and url.endswith("/work-items"):
            raise RuntimeError("POST execution: HTTP 503")
        if method == "GET" and "/work-items/" in url:
            raise RuntimeError("GET execution: HTTP 404")
        if method == "GET" and "/quotes/" in url:
            return {"state": "APPROVED"}
        return {"state": "OK"}

    module.http = fake_http
    module.run_saga({"event_type": "ORDER_CREATED", "order_id": "comp-test-001", "amount": "150.00"})

    assert states["comp-test-001"][0] == "COMPENSATED"
    assert ("POST", "http://billing:8080/quotes/comp-test-001/cancel") in calls
    assert ("POST", "http://execution:8080/work-items/comp-test-001/start") not in calls


def test_failed_compensation_requires_manual_intervention(saga):
    module, states = saga

    def fake_http(method, url, body=None):
        if method == "POST" and url.endswith("/work-items"):
            raise RuntimeError("POST execution: HTTP 503")
        if method == "GET" and "/work-items/" in url:
            raise RuntimeError("GET execution: HTTP 500")
        return {"state": "APPROVED"}

    module.http = fake_http
    with pytest.raises(RuntimeError, match="needs intervention"):
        module.run_saga({"event_type": "ORDER_CREATED", "order_id": "comp-test-002", "amount": "150.00"})
    assert states["comp-test-002"][0] == "COMPENSATION_REQUIRED"
    assert "HTTP 500" in states["comp-test-002"][1]


def test_compensated_saga_ignores_duplicate_event(saga):
    module, states = saga
    states["comp-test-003"] = ("COMPENSATED", None)
    module.http = Mock(side_effect=AssertionError("Unexpected HTTP call"))
    module.run_saga({"event_type": "ORDER_CREATED", "order_id": "comp-test-003", "amount": "150.00"})
    module.http.assert_not_called()
