"""
Lightweight, synchronous internal EventBus for DP-Core reflective cognition.

Decouples cognition producers from consumers using domain events with deterministic ordering,
type safety, and optional dispatch debug telemetry.
"""
import logging
import os
import time
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Type

from core.events import Event

logger = logging.getLogger(__name__)


class EventBus:
    """
    Synchronous internal EventBus supporting publish, subscribe, and unsubscribe operations.

    Dispatch is executed synchronously in deterministic registration order.
    Future asynchronous backends can wrap `publish()` without altering publisher code.
    """

    def __init__(self, debug_logging: Optional[bool] = None):
        self._subscribers: Dict[Type[Event], List[Callable[[Event], None]]] = defaultdict(list)
        if debug_logging is not None:
            self.debug_logging = debug_logging
        else:
            self.debug_logging = os.environ.get("EVENT_BUS_DEBUG", "0").strip() == "1"

    def subscribe(self, event_type: Type[Event], subscriber: Callable[[Event], None]) -> None:
        """Register a subscriber callback for a specific event type."""
        if not issubclass(event_type, Event):
            raise TypeError(f"event_type must be a subclass of Event, got {event_type}")
        if subscriber not in self._subscribers[event_type]:
            self._subscribers[event_type].append(subscriber)

    def unsubscribe(self, event_type: Type[Event], subscriber: Callable[[Event], None]) -> None:
        """Remove a subscriber callback for a specific event type."""
        if subscriber in self._subscribers[event_type]:
            self._subscribers[event_type].remove(subscriber)

    def publish(self, event: Event, publisher: Optional[str] = None) -> None:
        """
        Publish a domain event to all registered subscribers synchronously in order.

        Args:
            event: Instance of an Event subclass.
            publisher: Optional name or qualname of the publisher component.
        """
        if not isinstance(event, Event):
            raise TypeError(f"Expected an Event instance, got {type(event)}")

        if publisher:
            event.publisher = publisher

        event_type = type(event)
        event_name = event_type.__name__
        pub_name = event.publisher or "unknown_publisher"

        # Gather subscribers for exact class and any registered parent Event classes
        callbacks: List[Callable[[Event], None]] = []
        for reg_type, subs in self._subscribers.items():
            if isinstance(event, reg_type):
                callbacks.extend(subs)

        if not callbacks:
            if self.debug_logging:
                logger.debug(
                    "[EventBus] Event '%s' published by '%s' with 0 subscribers.",
                    event_name,
                    pub_name,
                )
            return

        for callback in callbacks:
            sub_name = getattr(callback, "__qualname__", str(callback))
            start_time = time.perf_counter()
            try:
                callback(event)
            except Exception as exc:
                logger.error(
                    "[EventBus] Subscriber '%s' failed processing event '%s': %s",
                    sub_name,
                    event_name,
                    exc,
                    exc_info=True,
                )
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            if self.debug_logging:
                logger.debug(
                    "[EventBus] Event: %s | Publisher: %s | Subscriber: %s | Duration: %.3f ms",
                    event_name,
                    pub_name,
                    sub_name,
                    duration_ms,
                )

    def clear(self) -> None:
        """Remove all registered subscribers."""
        self._subscribers.clear()


# Global Singleton Instance
_GLOBAL_EVENT_BUS: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Return the global default EventBus instance."""
    global _GLOBAL_EVENT_BUS
    if _GLOBAL_EVENT_BUS is None:
        _GLOBAL_EVENT_BUS = EventBus()
    return _GLOBAL_EVENT_BUS


def reset_event_bus() -> EventBus:
    """Reset and reinitialize the global default EventBus instance (useful for testing)."""
    global _GLOBAL_EVENT_BUS
    if _GLOBAL_EVENT_BUS is not None:
        _GLOBAL_EVENT_BUS.clear()
    _GLOBAL_EVENT_BUS = EventBus()
    return _GLOBAL_EVENT_BUS
