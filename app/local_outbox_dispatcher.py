"""Local transactional-outbox dispatcher: at-least-once delivery to SQS.

Only run against local emulator. Safe to restart; duplicates are handled by Saga.
"""
import os
import time
import logging
import boto3
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("oficina.outbox")
engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
sqs = boto3.client("sqs", endpoint_url=os.environ["SQS_ENDPOINT_URL"],
                   region_name="us-east-1", aws_access_key_id="local",
                   aws_secret_access_key="local")

def dispatch_once():
    queue = sqs.get_queue_url(QueueName="oficina-orders")["QueueUrl"]
    with engine.begin() as connection:
        # Transaction lock prevents concurrent dispatcher instances claiming the same row.
        rows = connection.execute(text("""
            SELECT id, payload FROM order_event_outbox
            WHERE published_at IS NULL ORDER BY created_at LIMIT 20
            FOR UPDATE SKIP LOCKED
        """)).all()
        for event_id, payload in rows:
            sqs.send_message(QueueUrl=queue, MessageBody=payload)
            connection.execute(text("""
                UPDATE order_event_outbox SET published_at=NOW()
                WHERE id=:id
            """), {"id": event_id})
            log.info("Published order event %s", event_id)

def main():
    while True:
        try:
            dispatch_once()
        except Exception:
            log.exception("Outbox delivery failed; retrying")
        time.sleep(2)

if __name__ == "__main__":
    main()
