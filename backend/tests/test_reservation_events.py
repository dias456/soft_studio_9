from datetime import datetime, timezone

from audit import InMemoryAuditRepository, ReservationCreatedAuditConsumer
from events import InProcessEventBus, ReservationCreated
from services import ReservationService


class FakeRepository:
    def __init__(self):
        self.reservations = []

    def get_all(self):
        return self.reservations

    def save(self, reservation):
        saved = reservation.copy()
        saved["id"] = len(self.reservations) + 1
        self.reservations.append(saved)
        return saved


def build_event_system():
    event_bus = InProcessEventBus()
    audit_repository = InMemoryAuditRepository()
    consumer = ReservationCreatedAuditConsumer(audit_repository)
    event_bus.subscribe(ReservationCreated, consumer.handle)
    return event_bus, audit_repository


def test_successful_reservation_publishes_event_and_creates_audit_record():
    event_bus, audit_repository = build_event_system()
    service = ReservationService(
        FakeRepository(),
        event_bus,
        event_id_factory=lambda: "reservation-event-1",
        clock=lambda: datetime(2026, 11, 24, 9, 0, tzinfo=timezone.utc),
    )
    reservation = {
        "student_id": 240107070,
        "seat_id": 1,
        "date": "2026-11-25",
        "time": "10:00",
    }

    result = service.create(reservation, [{"id": 1, "number": 101}])

    assert result["id"] == 1
    assert len(event_bus.published_events) == 1
    event = event_bus.published_events[0]
    assert isinstance(event, ReservationCreated)
    assert event.eventId == "reservation-event-1"
    assert event.reservationId == result["id"]
    assert event.studentId == 240107070
    assert event.seatId == 1

    records = audit_repository.get_all()
    assert len(records) == 1
    assert records[0]["eventId"] == event.eventId
    assert records[0]["eventType"] == "RESERVATION_CREATED"
    assert records[0]["reservationId"] == result["id"]


def test_duplicate_event_delivery_creates_audit_effect_only_once():
    event_bus, audit_repository = build_event_system()
    event = ReservationCreated(
        eventId="same-event-delivered-twice",
        occurredAt=datetime(2026, 11, 24, 9, 30, tzinfo=timezone.utc),
        reservationId=77,
        studentId=240107070,
        seatId=2,
        date="2026-11-25",
        time="11:00",
    )

    event_bus.publish(event)
    event_bus.publish(event)

    assert len(event_bus.published_events) == 2
    assert audit_repository.processed_count() == 1
    records = audit_repository.get_all()
    assert len(records) == 1
    assert records[0]["eventId"] == event.eventId
