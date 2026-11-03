#!/bin/bash
# Runs after LocalStack is ready. Idempotent queue provisioning for local Saga.
set -euo pipefail
export AWS_DEFAULT_REGION=us-east-1

create_queue() {
  local name="$1"
  awslocal sqs create-queue --queue-name "$name" >/dev/null
  echo "SQS ready: $name"
}
for name in oficina-orders-dlq oficina-billing-dlq oficina-execution-dlq; do
  create_queue "$name"
done
for pair in "oficina-orders:oficina-orders-dlq" "oficina-billing:oficina-billing-dlq" "oficina-execution:oficina-execution-dlq"; do
  name="${pair%%:*}"
  dlq="${pair##*:}"
  arn="$(awslocal sqs get-queue-attributes --queue-url "http://localhost:4566/000000000000/$dlq" --attribute-names QueueArn --query 'Attributes.QueueArn' --output text)"
  policy="{\"deadLetterTargetArn\":\"$arn\",\"maxReceiveCount\":\"3\"}"
  awslocal sqs create-queue --queue-name "$name" --attributes "RedrivePolicy=$policy" >/dev/null
  echo "SQS ready: $name -> $dlq"
done
