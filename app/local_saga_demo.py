"""Publish a local ORDER_CREATED event to the Saga queue (demo only).

Run inside the saga-worker container:
  python -m app.local_saga_demo os-demo-001 150.00
"""
import json
import os
import sys
import uuid

import boto3

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python -m app.local_saga_demo ORDER_ID AMOUNT")
    order_id, amount = sys.argv[1:]
    client = boto3.client("sqs", endpoint_url=os.environ["SQS_ENDPOINT_URL"],
                          region_name="us-east-1", aws_access_key_id="local", aws_secret_access_key="local")
    url = client.get_queue_url(QueueName="oficina-orders")["QueueUrl"]
    payload = {"event_id": str(uuid.uuid4()), "event_type": "ORDER_CREATED",
               "order_id": order_id, "amount": amount}
    result = client.send_message(QueueUrl=url, MessageBody=json.dumps(payload))
    print(json.dumps({"message_id": result["MessageId"], "event": payload}, indent=2))
