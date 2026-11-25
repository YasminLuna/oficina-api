"""Idempotent LocalStack ready hook for Saga queues and DLQs."""
import json
import subprocess

def aws(*args):
    command = ["awslocal", "sqs", *args, "--output", "json"]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout) if result.stdout.strip() else {}

for service in ("orders", "billing", "execution"):
    name = f"oficina-{service}"
    dlq_url = aws("create-queue", "--queue-name", name + "-dlq")["QueueUrl"]
    arn = aws("get-queue-attributes", "--queue-url", dlq_url,
              "--attribute-names", "QueueArn")["Attributes"]["QueueArn"]
    queue_url = aws("create-queue", "--queue-name", name)["QueueUrl"]
    policy = json.dumps({"deadLetterTargetArn": arn, "maxReceiveCount": "3"})
    aws("set-queue-attributes", "--queue-url", queue_url,
        "--attributes", json.dumps({"RedrivePolicy": policy}))
    print(f"READY: {name} -> {name}-dlq", flush=True)
