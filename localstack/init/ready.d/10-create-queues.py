"""Provision local Saga queues and dead-letter queues when LocalStack is ready."""
import json
import subprocess

def aws(*args):
    result = subprocess.run(["awslocal", "sqs", *args, "--output", "json"], check=True, capture_output=True, text=True)
    return json.loads(result.stdout) if result.stdout.strip() else {}

for service in ("orders", "billing", "execution"):
    dlq = f"oficina-{service}-dlq"
    queue = f"oficina-{service}"
    dlq_url = aws("create-queue", "--queue-name", dlq)["QueueUrl"]
    arn = aws("get-queue-attributes", "--queue-url", dlq_url, "--attribute-names", "QueueArn")["Attributes"]["QueueArn"]
    policy = json.dumps({"deadLetterTargetArn": arn, "maxReceiveCount": "3"})
    aws("create-queue", "--queue-name", queue, "--attributes", f"RedrivePolicy={policy}")
    print(f"SQS ready: {queue} -> {dlq}", flush=True)
