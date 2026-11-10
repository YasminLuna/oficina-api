"""Unit tests for local Saga compensation and duplicate deliveries.

Run: python -m unittest discover -s tests -p 'test_local_saga.py'
"""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SQS_ENDPOINT_URL", "http://localhost:4566")
from app import local_saga_worker as saga


class SagaTests(unittest.TestCase):
    def test_completed_is_idempotent(self):
        with patch.object(saga, "state", return_value="COMPLETED"), patch.object(saga, "http") as request:
            saga.run_saga({"event_type": "ORDER_CREATED", "order_id": "a", "amount": "10"})
            request.assert_not_called()

    def test_compensated_is_idempotent(self):
        with patch.object(saga, "state", return_value="COMPENSATED"), patch.object(saga, "http") as request:
            saga.run_saga({"event_type": "ORDER_CREATED", "order_id": "a", "amount": "10"})
            request.assert_not_called()

    def test_failure_cancels_queued_execution_and_quote(self):
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
             patch.object(saga, "http", side_effect=fake_http), \
             patch.object(saga, "set_state") as persist:
            saga.run_saga({"event_type": "ORDER_CREATED", "order_id": "a", "amount": "10"})
            self.assertIn(("POST", "http://execution:8080/work-items/a/cancel"), calls)
            self.assertIn(("POST", "http://billing:8080/quotes/a/cancel"), calls)
            self.assertEqual(persist.call_args.args[2], "COMPENSATED")

    def test_started_execution_requires_intervention(self):
        def fake_http(method, url, body=None):
            if method == "POST":
                raise RuntimeError("Injected failure")
            if "/work-items/" in url:
                return {"state": "IN_PROGRESS"}
            return {"state": "APPROVED"}
        with patch.object(saga, "state", return_value="EXECUTION_STARTED"), \
             patch.object(saga, "http", side_effect=fake_http), \
             patch.object(saga, "set_state") as persist:
            with self.assertRaises(RuntimeError):
                saga.run_saga({"event_type": "ORDER_CREATED", "order_id": "a", "amount": "10"})
            self.assertEqual(persist.call_args.args[2], "COMPENSATION_REQUIRED")


if __name__ == "__main__":
    unittest.main()
