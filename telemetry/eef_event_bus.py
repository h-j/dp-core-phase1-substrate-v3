"""
Thread-safe Asynchronous Telemetry Event Bus for EEF v1.0 / MVF v1.0.
Decouples step execution routines from telemetry processing.
"""

import logging
import queue
import threading
from typing import Callable, List, Optional
from telemetry.events import BaseTelemetryEvent

logger = logging.getLogger("eef_event_bus")


class TelemetryEventBus:
    """
    In-memory async/thread-safe Telemetry Event Bus.
    """

    _instance: Optional["TelemetryEventBus"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelemetryEventBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.queue: queue.Queue = queue.Queue(maxsize=10000)
        self.listeners: List[Callable[[BaseTelemetryEvent], None]] = []
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.start_worker()

    def subscribe(self, listener: Callable[[BaseTelemetryEvent], None]):
        """Register a subscriber listener callback."""
        if listener not in self.listeners:
            self.listeners.append(listener)

    def publish(self, event: BaseTelemetryEvent):
        """Publish a telemetry event to the queue."""
        try:
            self.queue.put_nowait(event)
        except queue.Full:
            logger.warning(f"Telemetry queue full! Dropping event: {event.event_id}")

    def _process_queue(self):
        """Worker thread processing queued events."""
        while not self._stop_event.is_set() or not self.queue.empty():
            try:
                event = self.queue.get(timeout=0.1)
                for listener in self.listeners:
                    try:
                        listener(event)
                    except Exception as e:
                        logger.error(f"Error in telemetry listener {listener.__name__}: {e}", exc_info=True)
                self.queue.task_done()
            except queue.Empty:
                continue

    def start_worker(self):
        """Start the background processing worker thread."""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._stop_event.clear()
            self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self._worker_thread.start()

    def flush_and_stop(self):
        """Wait for queue to drain and stop the worker thread."""
        self._stop_event.set()
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)


# Global singleton helper
event_bus = TelemetryEventBus()
