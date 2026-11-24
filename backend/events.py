from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, DefaultDict, List, Type


@dataclass(frozen=True)
class SeatAvailabilityChanged:
    """A completed business fact: a seat's availability was changed."""

    eventId: str
    occurredAt: datetime
    seatId: int
    isAvailable: bool


class InProcessEventBus:
    """Small synchronous event bus; no external message broker is required."""

    def __init__(self):
        self._handlers = defaultdict(list)  # type: DefaultDict[Type[Any], List[Callable[[Any], None]]]
        self.published_events = []  # type: List[Any]

    def subscribe(self, event_type, handler):
        # type: (Type[Any], Callable[[Any], None]) -> None
        self._handlers[event_type].append(handler)

    def publish(self, event):
        # type: (Any) -> None
        self.published_events.append(event)
        for handler in self._handlers[type(event)]:
            handler(event)
