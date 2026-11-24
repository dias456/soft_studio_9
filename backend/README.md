# Backend — Library Seat Reservation System

## Purpose
The backend handles the application's business logic and communicates with the database.

## Planned Responsibilities
- Check seat availability.
- Create and cancel reservations.
- Prevent overlapping reservations.
- Return reservation information.
- Verify user permissions.
- Integrate with the university authentication service.

## Planned Technology
Python with FastAPI

## Database
PostgreSQL

## Status
Planning stage. Implementation will be added in a later milestone.

## Event-driven contribution

After a seat's availability is successfully changed, `SeatService` publishes
the completed business fact `SeatAvailabilityChanged` through a synchronous
in-process event bus. `SeatAvailabilityChangedAuditConsumer` records an
observable audit entry. Its audit repository atomically claims each unique
`eventId`, so delivering the same event twice creates only one audit effect.
Run the complete suite from this directory:

```bash
python -m pytest tests/ -v
```
