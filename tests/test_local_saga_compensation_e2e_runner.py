"""Isolated tests of the local integration runner; never contact a cluster."""
import importlib
import json
import sys
from unittest.mock import Mock

import pytest


@pytest.fixture
def runner(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("SQS_ENDPOINT_URL", "http://localstack:4566")
    sys.modules.pop("app.local_saga_worker", None)
    sys.modules.pop("app.local_saga_compensation_e2e", None)
    module = importlib.import_module("app.local_saga_compensation_e2e")
    yield module
    sys.modules.pop("app.local_saga_compensation_e2e", None)
    sys.modules.pop("app.local_saga_worker", None)


def test_runner_refuses_nonlocal_environment(runner, monkeypatch):
    monkeypatch.setenv("SQS_ENDPOINT_URL", "https://sqs.us-east-1.amazonaws.com")
    with pytest.raises(RuntimeError, match="Refusing"):
        runner.main()


def test_runner_verifies_realistic_compensation_protocol(runner, monkeypatch, capsys):
    monkeypatch.setattr(runner.uuid, "uuid4", lambda: "e2e-mock-001")
    order_id = "e2e-mock-001"
    quote_url = f"http://billing:8080/quotes/{order_id}"
    execution_url = f"http://execution:8080/work-items/{order_id}"
    quote = {"state": "PENDING"}
    status = {"state": None}
    requests = []

    def fake_http(method, url, body=None):
        requests.append((method, url))
        if method == "POST" and url == "http://billing:8080/quotes":
            assert body == {"order_id": order_id, "amount": "150.00"}
            return quote
        if method == "POST" and url == quote_url + "/approve":
            quote["state"] = "APPROVED"
            return quote
        if method == "POST" and url == quote_url + "/cancel":
            quote["state"] = "CANCELLED"
            return quote
        if method == "GET" and url == quote_url:
            return dict(quote)
        if method == "GET" and url == execution_url:
            raise RuntimeError("HTTP 404")
        raise AssertionError(f"Unexpected HTTP: {method} {url}")

    runner.saga.http = fake_http
    runner.saga.initialize = Mock()
    runner.saga.state = lambda _: status["state"]

    def run_saga(event):
        assert event["order_id"] == order_id
        runner.saga.http("POST", "http://billing:8080/quotes", {"order_id": order_id, "amount": "150.00"})
        runner.saga.http("POST", quote_url + "/approve")
        with pytest.raises(RuntimeError, match="HTTP 503"):
            runner.saga.http("POST", "http://execution:8080/work-items", {"order_id": order_id})
        runner.saga.http("POST", quote_url + "/cancel")
        status["state"] = "COMPENSATED"

    runner.saga.run_saga = run_saga
    runner.main()
    report = json.loads(capsys.readouterr().out)
    assert report["result"] == "PASS"
    assert report["billing_after_compensation"] == "CANCELLED"
    assert report["execution"] == "NOT_CREATED"
    assert report["saga"] == "COMPENSATED"
    assert ("POST", quote_url + "/cancel") in requests
    runner.saga.initialize.assert_called_once()
