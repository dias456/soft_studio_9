from datetime import datetime, timezone

from audit import InMemoryAuditRepository, SeatAvailabilityChangedAuditConsumer
from events import InProcessEventBus, SeatAvailabilityChanged
from services import SeatService


def build_event_system():
    event_bus = InProcessEventBus()
    audit_repository = InMemoryAuditRepository()
    consumer = SeatAvailabilityChangedAuditConsumer(audit_repository)
    event_bus.subscribe(SeatAvailabilityChanged, consumer.handle)
    return event_bus, audit_repository


def test_successful_availability_change_publishes_event_and_creates_audit_record():
    event_bus, audit_repository = build_event_system()
    service = SeatService(
        event_bus,
        event_id_factory=lambda: "seat-event-1",
        clock=lambda: datetime(2026, 11, 24, 9, 0, tzinfo=timezone.utc),
    )
    seats = [{"id": 1, "number": 101, "is_available": True}]

    result = service.change_availability(seats, seat_id=1, is_available=False)

    assert result["is_available"] is False
    assert seats[0]["is_available"] is False
    assert len(event_bus.published_events) == 1
    event = event_bus.published_events[0]
    assert isinstance(event, SeatAvailabilityChanged)
    assert event.eventId == "seat-event-1"
    assert event.seatId == 1
    assert event.isAvailable is False

    records = audit_repository.get_all()
    assert len(records) == 1
    assert records[0]["eventId"] == event.eventId
    assert records[0]["eventType"] == "SEAT_AVAILABILITY_CHANGED"
    assert records[0]["seatId"] == 1
    assert records[0]["isAvailable"] is False


def test_duplicate_event_delivery_creates_audit_effect_only_once():
    event_bus, audit_repository = build_event_system()
    event = SeatAvailabilityChanged(
        eventId="same-event-delivered-twice",
        occurredAt=datetime(2026, 11, 24, 9, 30, tzinfo=timezone.utc),
        seatId=2,
        isAvailable=False,
    )

    event_bus.publish(event)
    event_bus.publish(event)

    assert len(event_bus.published_events) == 2
    assert audit_repository.processed_count() == 1
    records = audit_repository.get_all()
    assert len(records) == 1
    assert records[0]["eventId"] == event.eventId
