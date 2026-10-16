import pytest

from fase4_staging.billing import Payment, PaymentStatus, Quote, QuoteStatus
from fase4_staging.contracts import IntegrationEvent
from fase4_staging.execution import ExecutionStatus, WorkItem


def test_quote_approval():
    quote = Quote.issue("os-1", "25.50").approve()
    assert quote.status == QuoteStatus.APPROVED
    assert str(quote.amount) == "25.50"


@pytest.mark.parametrize("amount", ["-2", "0", "NaN", "Infinity", "oops"])
def test_invalid_quote_amount(amount):
    with pytest.raises(ValueError):
        Quote.issue("os-1", amount)


def test_quote_cannot_be_approved_twice():
    with pytest.raises(ValueError):
        Quote.issue("os-1", "10").approve().approve()


def test_quote_rejection():
    assert Quote.issue("os-1", "10").reject().status == QuoteStatus.REJECTED


def test_payment_requires_provider_verification():
    with pytest.raises(ValueError):
        Payment("os-1", "mp-123").confirm_from_verified_provider(False)


def test_payment_verified():
    assert Payment("os-1", "mp-123").confirm_from_verified_provider(True).status == PaymentStatus.CONFIRMED


def test_execution_happy_path():
    item = WorkItem("os-1").start().complete("Replaced brake pads")
    assert item.status == ExecutionStatus.DONE


def test_execution_requires_diagnosis():
    with pytest.raises(ValueError):
        WorkItem("os-1").start().complete(" ")


def test_queued_work_can_be_cancelled():
    assert WorkItem("os-1").cancel().status == ExecutionStatus.CANCELLED


def test_completed_work_cannot_be_cancelled():
    with pytest.raises(ValueError):
        WorkItem("os-1").start().complete("Fixed").cancel()


def test_event_contract_contains_traceable_identifiers():
    event = IntegrationEvent.create("PaymentConfirmed", "os-1", {"payment_id": "mp-123"})
    assert event.aggregate_id == "os-1"
    assert event.event_id
    assert event.schema_version == 1
