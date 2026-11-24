
from audit import InMemoryAuditRepository, SeatAvailabilityChangedAuditConsumer
from events import InProcessEventBus, SeatAvailabilityChanged
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from repository import ReservationRepository
from services import ReservationService, SeatService

app = FastAPI()

seats = [
    {"id": 1, "number": 101, "is_available": True},
    {"id": 2, "number": 102, "is_available": True},
    {"id": 3, "number": 103, "is_available": True}
]

repository = ReservationRepository()
event_bus = InProcessEventBus()
audit_repository = InMemoryAuditRepository()
audit_consumer = SeatAvailabilityChangedAuditConsumer(audit_repository)
event_bus.subscribe(SeatAvailabilityChanged, audit_consumer.handle)
reservation_service = ReservationService(repository)
seat_service = SeatService(event_bus)


class Reservation(BaseModel):
    student_id: int
    seat_id: int
    date: str
    time: str


class SeatAvailabilityUpdate(BaseModel):
    is_available: bool


@app.get("/")
def home():
    return {"message": "Library Seat Reservation System is running"}


@app.get("/seats")
def get_seats():
    return {"seats": seats}


@app.patch("/seats/{seat_id}/availability")
def change_seat_availability(seat_id: int, update: SeatAvailabilityUpdate):
    try:
        seat = seat_service.change_availability(
            seats, seat_id, update.is_available
        )
        return {
            "message": "Seat availability changed successfully",
            "seat": seat,
        }
    except ValueError as error:
        if str(error) == "Seat not found":
            raise HTTPException(status_code=404, detail=str(error))
        raise HTTPException(status_code=409, detail=str(error))


@app.post("/reservations")
def create_reservation(reservation: Reservation):
    try:
        result = reservation_service.create(reservation.model_dump(), seats)
        return {
            "message": "Reservation created successfully",
            "reservation": result
        }
    except ValueError as error:
        if str(error) == "Seat not found":
            raise HTTPException(status_code=404, detail=str(error))
        raise HTTPException(status_code=409, detail=str(error))


@app.get("/reservations")
def get_reservations():
    return {"reservations": repository.get_all()}


@app.get("/audit-records")
def get_audit_records():
    """Observable output produced by the ReservationCreated consumer."""
    return {"audit_records": audit_repository.get_all()}
