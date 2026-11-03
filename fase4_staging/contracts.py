"""Versioned integration contracts for asynchronous service communication."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class IntegrationEvent:
    event_id: str
    event_type: str
    aggregate_id: str
    occurred_at: str
    payload: dict[str, Any]
    schema_version: int = 1

    @classmethod
    def create(cls, event_type: str, aggregate_id: str, payload: dict[str, Any]):
        if not event_type or not aggregate_id:
            raise ValueError("event_type and aggregate_id are required")
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            aggregate_id=aggregate_id,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            payload=payload,
        )
