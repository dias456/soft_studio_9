from dataclasses import asdict, dataclass
from datetime import datetime
from threading import Lock
from typing import Dict, List, Set

from events import SeatAvailabilityChanged


@dataclass(frozen=True)
class AuditRecord:
    eventId: str
    eventType: str
    seatId: int
    isAvailable: bool
    occurredAt: datetime


class InMemoryAuditRepository:
    """Stores audit effects and atomically claims each event ID once."""

    def __init__(self):
        self._records = []  # type: List[AuditRecord]
        self._processed_event_ids = set()  # type: Set[str]
        self._lock = Lock()

    def save_once(self, record):
        # type: (AuditRecord) -> bool
        with self._lock:
            if record.eventId in self._processed_event_ids:
                return False

            self._processed_event_ids.add(record.eventId)
            self._records.append(record)
            return True

    def get_all(self):
        # type: () -> List[Dict[str, object]]
        with self._lock:
            return [asdict(record) for record in self._records]

    def processed_count(self):
        # type: () -> int
        with self._lock:
            return len(self._processed_event_ids)


class SeatAvailabilityChangedAuditConsumer:
    """Creates one audit entry for each unique availability-change event."""

    def __init__(self, audit_repository):
        # type: (InMemoryAuditRepository) -> None
        self.audit_repository = audit_repository

    def handle(self, event):
        # type: (SeatAvailabilityChanged) -> None
        self.audit_repository.save_once(
            AuditRecord(
                eventId=event.eventId,
                eventType="SEAT_AVAILABILITY_CHANGED",
                seatId=event.seatId,
                isAvailable=event.isAvailable,
                occurredAt=event.occurredAt,
            )
        )
