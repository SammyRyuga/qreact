"""Structured event log replacing the original plain List[str] log. The API
still exposes a human-readable `log` field derived from these events (see
execution/experiment.py), so existing frontend code keeps working
unchanged; `events` is the new, richer, structured view."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class EventType(str, Enum):
    CALIBRATION_SNAPSHOT = "CALIBRATION_SNAPSHOT"
    DRIFT_DETECTED = "DRIFT_DETECTED"
    REGION_BUILT = "REGION_BUILT"
    CANDIDATE_GENERATED = "CANDIDATE_GENERATED"
    CANDIDATE_REJECTED = "CANDIDATE_REJECTED"
    CANDIDATE_VERIFIED = "CANDIDATE_VERIFIED"
    LOCAL_PATCH_ACCEPTED = "LOCAL_PATCH_ACCEPTED"
    FALLBACK_TRIGGERED = "FALLBACK_TRIGGERED"
    FULL_RECOMPILE = "FULL_RECOMPILE"
    EXPERIMENT_STEP = "EXPERIMENT_STEP"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"


@dataclass
class Event:
    event_type: EventType
    message: str
    step: int | None = None
    severity: str = "info"
    region_id: str | None = None
    candidate_id: str | None = None
    reason: str | None = None

    def as_dict(self) -> dict:
        return {
            "event_type": self.event_type.value, "message": self.message, "step": self.step,
            "severity": self.severity, "region_id": self.region_id,
            "candidate_id": self.candidate_id, "reason": self.reason,
        }


@dataclass
class EventLog:
    events: list = field(default_factory=list)

    def add(self, event_type: EventType, message: str, **kwargs):
        self.events.append(Event(event_type=event_type, message=message, **kwargs))

    def as_list(self) -> list:
        return [e.as_dict() for e in self.events]

    def messages(self) -> list:
        return [e.message for e in self.events]
