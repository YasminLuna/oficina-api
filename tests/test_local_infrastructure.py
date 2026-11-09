"""Unit tests for local outbox publishing and SQS queue provisioning."""
from unittest.mock import MagicMock, patch

from app import local_outbox_dispatcher as outbox
from app import local_sqs_init as init


def test_dispatcher_publishes_and_marks_outbox_rows():
    connection = MagicMock()
    connection.execute.return_value.all.return_value = [
        ("event-1", '{"event_type":"ORDER_CREATED"}'),
        ("event-2", '{"event_type":"ORDER_CREATED"}'),
    ]
    transaction = MagicMock()
    transaction.__enter__.return_value = connection
    with patch.object(outbox.engine, "begin", return_value=transaction), \
         patch.object(outbox.sqs, "get_queue_url", return_value={"QueueUrl": "local-queue"}) as lookup, \
         patch.object(outbox.sqs, "send_message") as send:
        outbox.dispatch_once()
    lookup.assert_called_once_with(QueueName="oficina-orders")
    assert send.call_count == 2
    assert connection.execute.call_count == 3


def test_dispatcher_empty_batch():
    connection = MagicMock()
    connection.execute.return_value.all.return_value = []
    transaction = MagicMock()
    transaction.__enter__.return_value = connection
    with patch.object(outbox.engine, "begin", return_value=transaction), \
         patch.object(outbox.sqs, "get_queue_url", return_value={"QueueUrl": "local-queue"}), \
         patch.object(outbox.sqs, "send_message") as send:
        outbox.dispatch_once()
    send.assert_not_called()


def test_sqs_init_provisions_three_queues_and_dlqs():
    with patch.object(init.client, "list_queues", return_value={}), \
         patch.object(init.client, "create_queue", side_effect=lambda QueueName: {"QueueUrl": QueueName}) as create, \
         patch.object(init.client, "get_queue_attributes", return_value={"Attributes": {"QueueArn": "arn:local:dlq"}}), \
         patch.object(init.client, "set_queue_attributes") as configure:
        init.main()
    assert create.call_count == 6
    assert configure.call_count == 3
    assert all("RedrivePolicy" in call.kwargs["Attributes"] for call in configure.call_args_list)


def test_sqs_init_retries_until_available():
    with patch.object(init.client, "list_queues", side_effect=[RuntimeError("not ready"), {}]) as check, \
         patch.object(init, "time") as clock, \
         patch.object(init.client, "create_queue", side_effect=lambda QueueName: {"QueueUrl": QueueName}), \
         patch.object(init.client, "get_queue_attributes", return_value={"Attributes": {"QueueArn": "arn:local:dlq"}}), \
         patch.object(init.client, "set_queue_attributes"):
        init.main()
    assert check.call_count == 2
    clock.sleep.assert_called_once_with(2)
