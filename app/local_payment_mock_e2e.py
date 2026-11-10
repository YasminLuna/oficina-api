"""Credential-free end-to-end validation of Billing mock payment initiation.

Run inside the oficina-api container after docker compose --profile emulators up.
This test never requests a real payment or changes a payment to approved.
"""
import json
import uuid
from urllib.request import Request, urlopen

BASE = "http://billing:8080"


def call(method, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request(BASE + path, data=data, method=method,
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=10) as response:
        return response.status, json.load(response)


def main():
    order_id = "fiap-payment-mock-" + uuid.uuid4().hex
    status, quote = call("POST", "/quotes", {"order_id": order_id, "amount": "150.00"})
    assert status == 201 and quote["state"] == "PENDING", quote
    status, approved = call("POST", "/quotes/" + order_id + "/approve")
    assert status == 200 and approved["state"] == "APPROVED", approved
    status, payment = call("POST", "/quotes/" + order_id + "/payments", {})
    assert status == 202 and payment["provider"] == "mock", payment
    assert payment["status"] == "pending" and payment["simulated"] is True, payment
    assert payment["external_reference"] == order_id, payment
    print(json.dumps({"result": "PASS", "order_id": order_id,
                      "quote": approved["state"], "payment": payment["status"],
                      "provider": payment["provider"], "real_charge": False}, indent=2))


if __name__ == "__main__":
    main()
