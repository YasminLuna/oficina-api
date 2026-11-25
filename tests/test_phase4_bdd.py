"""Executable BDD scenarios for the Phase 4 Saga.

Run: python -m pytest tests/test_phase4_bdd.py -v
These scenarios isolate HTTP/SQS and do not require cloud credentials.
"""
from unittest.mock import patch

import pytest

from app import local_saga_worker as saga


def event():
    return {"event_type": "ORDER_CREATED", "order_id": "bdd-order", "amount": "100.00"}


def test_given_new_order_when_services_succeed_then_saga_completes():
    """Given a new order, when all services succeed, then the Saga completes."""
    states = []
    calls = []

    def fake_http(method, url, body=None):
        calls.append((method, url))
        return {"state": "APPROVED"}

    with patch.object(saga, "state", return_value=None), \
         patch.object(saga, "set_state", side_effect=lambda *args: states.append(args[2])), \
         patch.object(saga, "http", side_effect=fake_http):
        saga.run_saga(event())

    assert states == ["QUOTE_CREATED", "QUOTE_APPROVED", "EXECUTION_QUEUED",
                      "EXECUTION_STARTED", "COMPLETED"]
    assert any(url.endswith("/complete") for _, url in calls)


def test_given_queued_execution_when_start_fails_then_saga_compensates():
    """Given queued execution, when start fails, then cancel execution and quote."""
    states = []
    calls = []

    def fake_http(method, url, body=None):
        calls.append((method, url))
        if method == "POST" and url.endswith("/start"):
            raise RuntimeError("Injected failure")
        if method == "GET" and "/work-items/" in url:
            return {"state": "QUEUED"}
        if method == "GET" and "/quotes/" in url:
            return {"state": "APPROVED"}
        return {}

    with patch.object(saga, "state", return_value="EXECUTION_QUEUED"), \
         patch.object(saga, "set_state", side_effect=lambda *args: states.append(args[2])), \
         patch.object(saga, "http", side_effect=fake_http):
        saga.run_saga(event())

    assert states == ["COMPENSATED"]
    assert any(url.endswith("/cancel") and "/work-items/" in url for _, url in calls)
    assert any(url.endswith("/cancel") and "/quotes/" in url for _, url in calls)


@pytest.mark.parametrize("terminal", ["COMPLETED", "COMPENSATED"])
def test_given_terminal_saga_when_duplicate_arrives_then_no_side_effects(terminal):
    """Given a terminal Saga, when the same event is delivered, then ignore it."""
    with patch.object(saga, "state", return_value=terminal), \
         patch.object(saga, "http") as http, \
         patch.object(saga, "set_state") as persist:
        saga.run_saga(event())
    http.assert_not_called()
    persist.assert_not_called()


def test_given_running_execution_when_failure_then_manual_compensation():
    """Given running work, when completion fails, then flag manual intervention."""
    states = []

    def fake_http(method, url, body=None):
        if method == "POST":
            raise RuntimeError("Injected completion failure")
        if "/work-items/" in url:
            return {"state": "IN_PROGRESS"}
        return {"state": "APPROVED"}

    with patch.object(saga, "state", return_value="EXECUTION_STARTED"), \
         patch.object(saga, "set_state", side_effect=lambda *args: states.append(args[2])), \
         patch.object(saga, "http", side_effect=fake_http):
        with pytest.raises(RuntimeError, match="needs intervention"):
            saga.run_saga(event())
    assert states == ["COMPENSATION_REQUIRED"]


def test_given_manual_compensation_when_redelivered_then_block():
    with patch.object(saga, "state", return_value="COMPENSATION_REQUIRED"), \
         patch.object(saga, "http") as http:
        with pytest.raises(RuntimeError, match="requires manual compensation"):
            saga.run_saga(event())
    http.assert_not_called()


def test_given_unsupported_event_when_processed_then_reject():
    with pytest.raises(ValueError, match="Unsupported event"):
        saga.run_saga({"event_type": "UNKNOWN"})
