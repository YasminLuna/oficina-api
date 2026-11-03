"""Billing domain prototype. No external charge or payment confirmation is made."""
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from enum import Enum


class QuoteStatus(str, Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class Quote:
    order_id: str
    amount: Decimal
    status: QuoteStatus = QuoteStatus.DRAFT

    @classmethod
    def issue(cls, order_id: str, amount: str) -> "Quote":
        try:
            value = Decimal(amount)
        except (InvalidOperation, TypeError) as exc:
            raise ValueError("Invalid monetary amount") from exc
        if not order_id or not value.is_finite() or value <= 0:
            raise ValueError("Order ID and positive finite amount are required")
        return cls(order_id=order_id, amount=value.quantize(Decimal("0.01")))

    def approve(self) -> "Quote":
        if self.status != QuoteStatus.DRAFT:
            raise ValueError("Quote already resolved")
        return replace(self, status=QuoteStatus.APPROVED)

    def reject(self) -> "Quote":
        if self.status != QuoteStatus.DRAFT:
            raise ValueError("Quote already resolved")
        return replace(self, status=QuoteStatus.REJECTED)


@dataclass(frozen=True)
class Payment:
    order_id: str
    provider_reference: str
    status: PaymentStatus = PaymentStatus.PENDING

    def confirm_from_verified_provider(self, verified: bool) -> "Payment":
        if self.status != PaymentStatus.PENDING:
            raise ValueError("Payment already resolved")
        if not verified or not self.provider_reference:
            raise ValueError("Provider payment verification required")
        return replace(self, status=PaymentStatus.CONFIRMED)
