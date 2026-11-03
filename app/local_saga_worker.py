"""Local Saga orchestrator: SQS inbox, durable PostgreSQL state, compensating actions.

Development-only demonstration. Production needs transactional outbox and stronger recovery.
"""
import json
import logging
import os
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import boto3
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("oficina.saga")
engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
sqs = boto3.client("sqs", endpoint_url=os.environ["SQS_ENDPOINT_URL"], region_name="us-east-1",
                   aws_access_key_id="local", aws_secret_access_key="local")
queue_name = "oficina-orders"


def http(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=8) as response:
            return json.load(response)
    except HTTPError as error:
        detail = error.read().decode()
        raise RuntimeError(f"{method} {url}: HTTP {error.code}: {detail}") from error


def initialize():
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS local_sagas (
                order_id TEXT PRIMARY KEY, state TEXT NOT NULL,
                amount TEXT NOT NULL, error TEXT
            )
        """))


def state(order_id):
    with engine.connect() as connection:
        row = connection.execute(text("SELECT state FROM local_sagas WHERE order_id=:id"), {"id": order_id}).first()
        return row[0] if row else None


def set_state(order_id, amount, status, error=None):
    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO local_sagas(order_id, amount, state, error)
            VALUES (:id, :amount, :state, :error)
            ON CONFLICT (order_id) DO UPDATE SET state=EXCLUDED.state, error=EXCLUDED.error
        """), {"id": order_id, "amount": amount, "state": status, "error": error})


def run_saga(event):
    if event.get("event_type") != "ORDER_CREATED":
        raise ValueError("Unsupported event")
    order_id = str(event["order_id"])
    amount = str(event["amount"])
    current = state(order_id)
    if current == "COMPENSATION_REQUIRED":
        raise RuntimeError(f"Saga {order_id} requires manual compensation")
    if current == "COMPLETED":
        log.info("Skipping terminal saga %s (%s)", order_id, current)
        return
    billing = "http://billing:8080/quotes/" + order_id
    execution = "http://execution:8080/work-items/" + order_id
    try:
        if current is None:
            try:
                http("POST", "http://billing:8080/quotes", {"order_id": order_id, "amount": amount})
            except RuntimeError as exc:
                if "HTTP 409" not in str(exc):
                    raise
            set_state(order_id, amount, "QUOTE_CREATED")
            current = "QUOTE_CREATED"
        if current == "QUOTE_CREATED":
            try:
                http("POST", billing + "/approve")
            except RuntimeError as exc:
                if "HTTP 409" not in str(exc) or http("GET", billing)["state"] != "APPROVED":
                    raise
            set_state(order_id, amount, "QUOTE_APPROVED")
            current = "QUOTE_APPROVED"
        if current == "QUOTE_APPROVED":
            try:
                http("POST", "http://execution:8080/work-items", {"order_id": order_id})
            except RuntimeError as exc:
                if "HTTP 500" not in str(exc) and "HTTP 409" not in str(exc):
                    raise
                if http("GET", execution)["state"] != "QUEUED":
                    raise
            set_state(order_id, amount, "EXECUTION_QUEUED")
            current = "EXECUTION_QUEUED"
        if current == "EXECUTION_QUEUED":
            http("POST", execution + "/start")
            set_state(order_id, amount, "EXECUTION_STARTED")
            current = "EXECUTION_STARTED"
        if current == "EXECUTION_STARTED":
            http("POST", execution + "/complete", {"description": "Serviço concluído pela Saga local"})
            set_state(order_id, amount, "COMPLETED")
            log.info("Saga completed: %s", order_id)
    except Exception as exc:
        log.exception("Saga failed for %s", order_id)
        # Only cancel work that has not started. Approved quotes cannot be rejected
        # using the current Billing contract: record this as manual intervention.
        try:
            work = http("GET", execution)
            if work["state"] == "QUEUED":
                http("POST", execution + "/cancel")
        except Exception:
            log.warning("Execution compensation unavailable for %s", order_id)
        set_state(order_id, amount, "COMPENSATION_REQUIRED", str(exc))
        raise


def main():
    initialize()
    while True:
        try:
            queue_url = sqs.get_queue_url(QueueName=queue_name)["QueueUrl"]
            break
        except Exception:
            log.info("Waiting for SQS queue...")
            time.sleep(3)
    while True:
        try:
            batch = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1,
                                        WaitTimeSeconds=10, VisibilityTimeout=45).get("Messages", [])
            for message in batch:
                try:
                    run_saga(json.loads(message["Body"]))
                    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=message["ReceiptHandle"])
                except Exception:
                    log.exception("Message failed; SQS will retry / move to DLQ")
        except Exception:
            log.exception("SQS polling failed")
            time.sleep(3)


if __name__ == "__main__":
    main()
