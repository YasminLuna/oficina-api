"""Saga orchestration core for the Fase 4 service extraction.

This module is deliberately infrastructure-agnostic. Production adapters must
persist events, enforce idempotency and deliver messages through SQS/outbox.
"""
from dataclasses import dataclass
from enum import Enum


class SagaState(str, Enum):
    OPEN = "OPEN"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    AWAITING_PAYMENT = "AWAITING_PAYMENT"
    READY_FOR_EXECUTION = "READY_FOR_EXECUTION"
    IN_EXECUTION = "IN_EXECUTION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class SagaEvent(str, Enum):
    QUOTE_REQUESTED = "QUOTE_REQUESTED"
    QUOTE_APPROVED = "QUOTE_APPROVED"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED"
    EXECUTION_STARTED = "EXECUTION_STARTED"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED"
    QUOTE_REJECTED = "QUOTE_REJECTED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    EXECUTION_FAILED = "EXECUTION_FAILED"


class InvalidTransition(ValueError):
    pass


TRANSITIONS = {
    (SagaState.OPEN, SagaEvent.QUOTE_REQUESTED): SagaState.AWAITING_APPROVAL,
    (SagaState.AWAITING_APPROVAL, SagaEvent.QUOTE_APPROVED): SagaState.AWAITING_PAYMENT,
    (SagaState.AWAITING_PAYMENT, SagaEvent.PAYMENT_CONFIRMED): SagaState.READY_FOR_EXECUTION,
    (SagaState.READY_FOR_EXECUTION, SagaEvent.EXECUTION_STARTED): SagaState.IN_EXECUTION,
    (SagaState.IN_EXECUTION, SagaEvent.EXECUTION_COMPLETED): SagaState.COMPLETED,
    (SagaState.AWAITING_APPROVAL, SagaEvent.QUOTE_REJECTED): SagaState.CANCELLED,
    (SagaState.AWAITING_PAYMENT, SagaEvent.PAYMENT_FAILED): SagaState.FAILED,
    (SagaState.READY_FOR_EXECUTION, SagaEvent.EXECUTION_FAILED): SagaState.FAILED,
    (SagaState.IN_EXECUTION, SagaEvent.EXECUTION_FAILED): SagaState.FAILED,
}


@dataclass(frozen=True)
class Saga:
    order_id: str
    state: SagaState = SagaState.OPEN

    def apply(self, event: SagaEvent) -> "Saga":
        target = TRANSITIONS.get((self.state, event))
        if target is None:
            raise InvalidTransition(f"Invalid saga transition: {self.state} -> {event}")
        return Saga(order_id=self.order_id, state=target)
