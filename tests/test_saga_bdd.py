"""Executable Gherkin scenarios for Saga compensation, using isolated mocks."""
import importlib
import sys

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../features/saga_compensation.feature")


@pytest.fixture
def context(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("SQS_ENDPOINT_URL", "http://localhost:4566")
    sys.modules.pop("app.local_saga_worker", None)
    saga = importlib.import_module("app.local_saga_worker")
    recorded = {"calls": [], "states": {}}
    saga.state = lambda order_id: recorded["states"].get(order_id)

    def set_state(order_id, amount, status, error=None):
        recorded["states"][order_id] = status

    saga.set_state = set_state
    yield saga, recorded
    sys.modules.pop("app.local_saga_worker", None)


@given("uma ordem de teste sem Saga registrada")
def new_order(context):
    assert context[0].state("bdd-order-001") is None


@given("o Billing aprova o orcamento e o Execution falha antes de criar o item")
def services(context):
    saga, recorded = context

    def http(method, url, body=None):
        recorded["calls"].append((method, url))
        if method == "POST" and url == "http://execution:8080/work-items":
            raise RuntimeError("HTTP 503: controlled failure")
        if method == "GET" and "/work-items/" in url:
            raise RuntimeError("HTTP 404")
        if method == "GET" and "/quotes/" in url:
            return {"state": "APPROVED"}
        return {"state": "OK"}

    saga.http = http


@when("o evento ORDER_CREATED e processado")
def process(context):
    saga, _ = context
    saga.run_saga({"event_type": "ORDER_CREATED", "order_id": "bdd-order-001", "amount": "150.00"})


@then("a Saga termina no estado COMPENSATED")
def compensated(context):
    assert context[1]["states"]["bdd-order-001"] == "COMPENSATED"


@then("o Billing recebe a solicitacao de cancelamento")
def billing_cancelled(context):
    assert ("POST", "http://billing:8080/quotes/bdd-order-001/cancel") in context[1]["calls"]


@then("o Execution nao recebe solicitacao para iniciar o servico")
def execution_not_started(context):
    assert ("POST", "http://execution:8080/work-items/bdd-order-001/start") not in context[1]["calls"]
