"""Isolated FastAPI integration tests using an ephemeral SQLite database."""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base, get_db
from app.core.security import current_customer
from app.main import app
from app.models import Customer, OrderEventOutbox, OrderStatus


@pytest.fixture
def context(tmp_path):
    engine = create_engine("sqlite:///" + str(tmp_path / "orders.db"),
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        owner = Customer(document="52998224725", name="Owner", active=True)
        other = Customer(document="12345678901", name="Other", active=True)
        db.add_all([owner, other])
        db.commit()
        db.refresh(owner)
        db.refresh(other)
        ids = {"owner": owner.id, "other": other.id}
    identity = {"sub": ids["owner"]}

    def db_override():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = db_override
    app.dependency_overrides[current_customer] = lambda: dict(identity)
    try:
        with TestClient(app) as client:
            yield client, ids, identity, engine
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def create(client):
    response = client.post("/api/v1/orders", json={"vehicle_plate": "abc1234"})
    assert response.status_code == 200, response.text
    return response.json()["id"]


def test_health_ready_and_metrics(context):
    client, _, _, _ = context
    assert client.get("/health").status_code == 200
    assert client.get("/ready").json() == {"status": "ready"}
    assert client.get("/metrics").status_code == 200


def test_customer_creation_idempotency(context):
    client, _, _, _ = context
    data = {"document": "987.654.321-00", "name": "New"}
    first = client.post("/internal/customers", json=data)
    assert first.status_code == 200
    assert client.post("/internal/customers", json=data).json()["id"] == first.json()["id"]


def test_order_lifecycle_and_ownership(context):
    client, ids, identity, _ = context
    order = create(client)
    assert client.get("/api/v1/orders").json()[0]["vehicle_plate"] == "ABC1234"
    assert client.patch(f"/api/v1/orders/{order}/status", params={"status": "Diagnóstico"}).status_code == 200
    identity["sub"] = ids["other"]
    assert client.get("/api/v1/orders").json() == []
    assert client.patch(f"/api/v1/orders/{order}/status", params={"status": "Recebida"}).status_code == 403
    assert client.post(f"/api/v1/orders/{order}/request-quote", json={"amount": "10"}).status_code == 403


def test_quote_outbox_idempotency_and_conflict(context):
    client, _, _, engine = context
    order = create(client)
    path = f"/api/v1/orders/{order}/request-quote"
    first = client.post(path, json={"amount": "12.345"})
    assert first.status_code == 202, first.text
    assert client.post(path, json={"amount": "12.35"}).status_code == 202
    assert client.post(path, json={"amount": "99"}).status_code == 409
    with Session(engine) as db:
        event = db.query(OrderEventOutbox).filter_by(order_id=order).one()
        assert event.amount == "12.35"
        assert "ORDER_CREATED" in event.payload


@pytest.mark.parametrize("amount", ["0", "-1", "NaN", "Infinity", "oops"])
def test_quote_invalid_amount(context, amount):
    client, _, _, _ = context
    order = create(client)
    assert client.post(f"/api/v1/orders/{order}/request-quote",
                       json={"amount": amount}).status_code == 422


def test_missing_order_and_inactive_customer(context):
    client, ids, _, engine = context
    missing = str(uuid.uuid4())
    assert client.post(f"/api/v1/orders/{missing}/request-quote",
                       json={"amount": "10"}).status_code == 404
    assert client.patch(f"/api/v1/orders/{missing}/status",
                        params={"status": "Recebida"}).status_code == 404
    with Session(engine) as db:
        customer = db.get(Customer, ids["owner"])
        customer.active = False
        db.commit()
    assert client.post("/api/v1/orders", json={"vehicle_plate": "abc1234"}).status_code == 403
