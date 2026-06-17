from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable, Coroutine
from uuid import UUID

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DomainEvent:
    event_type: str
    company_id: UUID
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: DomainEvent) -> None:
        logger.info("event_published", event_type=event.event_type, company_id=str(event.company_id))
        for handler in self._handlers.get(event.event_type, []):
            await handler(event)
        for handler in self._handlers.get("*", []):
            await handler(event)


event_bus = EventBus()


async def log_activity_handler(event: DomainEvent) -> None:
    logger.info(
        "domain_event",
        event_type=event.event_type,
        company_id=str(event.company_id),
        payload=event.payload,
    )


event_bus.subscribe("*", log_activity_handler)
