import unittest

from fase4_staging.saga import InvalidTransition, Saga, SagaEvent, SagaState


class SagaTests(unittest.TestCase):
    def test_happy_path(self):
        saga = Saga("os-001")
        for event in (
            SagaEvent.QUOTE_REQUESTED,
            SagaEvent.QUOTE_APPROVED,
            SagaEvent.PAYMENT_CONFIRMED,
            SagaEvent.EXECUTION_STARTED,
            SagaEvent.EXECUTION_COMPLETED,
        ):
            saga = saga.apply(event)
        self.assertEqual(saga.state, SagaState.COMPLETED)

    def test_rejected_quote_compensates_by_cancelling_order(self):
        saga = Saga("os-002").apply(SagaEvent.QUOTE_REQUESTED)
        self.assertEqual(saga.apply(SagaEvent.QUOTE_REJECTED).state, SagaState.CANCELLED)

    def test_failed_payment_does_not_release_execution(self):
        saga = Saga("os-003").apply(SagaEvent.QUOTE_REQUESTED).apply(SagaEvent.QUOTE_APPROVED)
        self.assertEqual(saga.apply(SagaEvent.PAYMENT_FAILED).state, SagaState.FAILED)

    def test_execution_failure_requires_recovery(self):
        saga = Saga("os-004")
        for event in (SagaEvent.QUOTE_REQUESTED, SagaEvent.QUOTE_APPROVED,
                      SagaEvent.PAYMENT_CONFIRMED, SagaEvent.EXECUTION_STARTED):
            saga = saga.apply(event)
        self.assertEqual(saga.apply(SagaEvent.EXECUTION_FAILED).state, SagaState.FAILED)

    def test_cannot_execute_without_payment(self):
        with self.assertRaises(InvalidTransition):
            Saga("os-005").apply(SagaEvent.EXECUTION_STARTED)

    def test_terminal_state_rejects_duplicate_event(self):
        saga = Saga("os-006").apply(SagaEvent.QUOTE_REQUESTED).apply(SagaEvent.QUOTE_REJECTED)
        with self.assertRaises(InvalidTransition):
            saga.apply(SagaEvent.QUOTE_REJECTED)


if __name__ == "__main__":
    unittest.main()
