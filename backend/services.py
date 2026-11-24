from datetime import datetime, timezone
from uuid import uuid4

from events import InProcessEventBus, ReservationCreated


class ReservationService:

    def __init__(self, repository, event_bus=None, event_id_factory=None, clock=None):
        self.repository = repository
        self.event_bus = event_bus or InProcessEventBus()
        self.event_id_factory = event_id_factory or (lambda: str(uuid4()))
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def create(self, reservation, seats):

        # Check if the seat exists
        seat_exists = False

        for seat in seats:
            if seat["id"] == reservation["seat_id"]:
                seat_exists = True

        if not seat_exists:
            raise ValueError("Seat not found")

        # Check if the seat is already booked
        for existing in self.repository.get_all():
            if (
                existing["seat_id"] == reservation["seat_id"]
                and existing["date"] == reservation["date"]
                and existing["time"] == reservation["time"]
            ):
                raise ValueError("Seat is already reserved")

        # Save is the main business operation. If it fails, no event is published.
        saved = self.repository.save(reservation)

        # Publish only after the reservation has been saved successfully.
        self.event_bus.publish(
            ReservationCreated(
                eventId=self.event_id_factory(),
                occurredAt=self.clock(),
                reservationId=saved["id"],
                studentId=saved["student_id"],
                seatId=saved["seat_id"],
                date=saved["date"],
                time=saved["time"],
            )
        )

        return saved
