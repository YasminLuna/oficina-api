"""End-to-end API -> transactional outbox -> SQS -> Saga test.

Run inside the oficina-api container:
    python -m app.local_outbox_e2e
Uses local-only JWT secret and services. Creates isolated test records.
"""
import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import jwt
from sqlalchemy import text
from .db import SessionLocal
from .models import Customer

BASE = "http://127.0.0.1:8000"


def call(method, url, payload=None, token=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = Request(url, data=json.dumps(payload).encode() if payload is not None else None,
                  method=method, headers=headers)
    try:
        with urlopen(req, timeout=8) as response:
            return response.status, json.load(response)
    except HTTPError as error:
        raise AssertionError(f"{method} {url}: HTTP {error.code}: {error.read().decode()}") from error


def main():
    marker = uuid.uuid4().hex[:12]
    with SessionLocal() as db:
        customer = Customer(document="test" + marker, name="Teste integrado local")
        db.add(customer)
        db.commit()
        customer_id = customer.id

    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub": customer_id, "iss": "oficina-auth",
                        "iat": now, "exp": now + timedelta(minutes=10)},
                       os.environ["JWT_SECRET"], algorithm="HS256")
    status, order = call("POST", BASE + "/api/v1/orders",
                         {"vehicle_plate": "FIAP123"}, token)
    assert status == 200, (status, order)
    order_id = order["id"]
    status, quote = call("POST", BASE + f"/api/v1/orders/{order_id}/request-quote",
                         {"amount": "150.00"}, token)
    assert status == 202 and quote["status"] in ("PENDING", "PUBLISHED"), quote
    status, duplicate = call("POST", BASE + f"/api/v1/orders/{order_id}/request-quote",
                             {"amount": "150.00"}, token)
    assert duplicate["event_id"] == quote["event_id"], "Outbox idempotency failure"

    for attempt in range(45):
        with SessionLocal() as db:
            row = db.execute(text("""
                SELECT o.published_at, s.state FROM order_event_outbox o
                LEFT JOIN local_sagas s ON s.order_id=o.order_id
                WHERE o.order_id=:id
            """), {"id": order_id}).first()
        if row and row[0] is not None and row[1] == "COMPLETED":
            break
        time.sleep(2)
    else:
        raise AssertionError(f"Timed out waiting for outbox/Saga: {row}")

    _, billing = call("GET", "http://billing:8080/quotes/" + order_id)
    _, execution = call("GET", "http://execution:8080/work-items/" + order_id)
    assert billing["state"] == "APPROVED", billing
    assert execution["state"] == "COMPLETED", execution
    print(json.dumps({"result": "PASS", "order_id": order_id,
                      "outbox": "PUBLISHED", "saga": "COMPLETED",
                      "billing": billing["state"], "execution": execution["state"],
                      "duplicate_event": "DEDUPLICATED"}, indent=2))


if __name__ == "__main__":
    main()
