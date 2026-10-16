"""Execution queue domain prototype; external persistence adapter is pending."""
from dataclasses import dataclass, replace
from enum import Enum


class ExecutionStatus(str, Enum):
    QUEUED = "QUEUED"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class WorkItem:
    order_id: str
    status: ExecutionStatus = ExecutionStatus.QUEUED
    diagnosis: str = ""

    def start(self) -> "WorkItem":
        if self.status != ExecutionStatus.QUEUED:
            raise ValueError("Only queued work can start")
        return replace(self, status=ExecutionStatus.IN_PROGRESS)

    def complete(self, diagnosis: str) -> "WorkItem":
        if self.status != ExecutionStatus.IN_PROGRESS or not diagnosis.strip():
            raise ValueError("In-progress work and diagnosis are required")
        return replace(self, status=ExecutionStatus.DONE, diagnosis=diagnosis.strip())

    def cancel(self) -> "WorkItem":
        if self.status != ExecutionStatus.QUEUED:
            raise ValueError("Only queued work can be cancelled")
        return replace(self, status=ExecutionStatus.CANCELLED)
