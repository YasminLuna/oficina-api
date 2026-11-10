"""Create SQS queues and dead-letter queues for the local emulator."""
import json
import os
import time
import boto3

client = boto3.client(
    "sqs", endpoint_url=os.environ["SQS_ENDPOINT_URL"],
    region_name="us-east-1", aws_access_key_id="local", aws_secret_access_key="local",
)

def main():
    for attempt in range(30):
        try:
            client.list_queues()
            break
        except Exception:
            if attempt == 29:
                raise
            time.sleep(2)
    for service in ("orders", "billing", "execution"):
        name = "oficina-" + service
        dlq_url = client.create_queue(QueueName=name + "-dlq")["QueueUrl"]
        arn = client.get_queue_attributes(QueueUrl=dlq_url, AttributeNames=["QueueArn"])["Attributes"]["QueueArn"]
        queue_url = client.create_queue(QueueName=name)["QueueUrl"]
        client.set_queue_attributes(
            QueueUrl=queue_url,
            Attributes={"RedrivePolicy": json.dumps({"deadLetterTargetArn": arn, "maxReceiveCount": "3"})},
        )
        print("Ready:", name, "->", name + "-dlq", flush=True)

if __name__ == "__main__":
    main()
