from datetime import datetime, timezone
from uuid import uuid4

from events import InProcessEventBus, SeatAvailabilityChanged


class SeatService:

    def __init__(self, event_bus=None, event_id_factory=None, clock=None):
        self.event_bus = event_bus or InProcessEventBus()
        self.event_id_factory = event_id_factory or (lambda: str(uuid4()))
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def change_availability(self, seats, seat_id, is_available):
        seat = next((item for item in seats if item["id"] == seat_id), None)

        if seat is None:
            raise ValueError("Seat not found")

        current_availability = seat.get("is_available", True)
        if current_availability == is_available:
            raise ValueError("Seat availability is already set to this value")

        # Changing the seat is the main business operation.
        seat["is_available"] = is_available

        # Publish only after the change has completed successfully.
        self.event_bus.publish(
            SeatAvailabilityChanged(
                eventId=self.event_id_factory(),
                occurredAt=self.clock(),
                seatId=seat_id,
                isAvailable=is_available,
            )
        )

        return seat.copy()


class ReservationService:

    def __init__(self, repository):
        self.repository = repository

    def create(self, reservation, seats):

        # Check if the seat exists
        seat_exists = False

        for seat in seats:
            if seat["id"] == reservation["seat_id"]:
                seat_exists = True
                if not seat.get("is_available", True):
                    raise ValueError("Seat is unavailable")

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

        return self.repository.save(reservation)
