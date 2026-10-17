"""
KİRVE AI OS - Event Bus Architecture
Lightweight publish-subscribe bus for system events, window focus changes,
and silent mode notifications.
"""
import threading
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
import time

@dataclass
class SystemEvent:
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class EventBus:
    """
    Central Event Bus for KİRVE AI OS.
    Allows sub-agents, tools, and background monitors to communicate asynchronously.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[SystemEvent], None]]] = {}
        self._lock = threading.Lock()
        self._history: List[SystemEvent] = []

    def subscribe(self, event_name: str, handler: Callable[[SystemEvent], None]) -> None:
        """Subscribes a callable handler to a specific event name."""
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            self._subscribers[event_name].append(handler)

    def publish(self, event_name: str, data: Optional[Dict[str, Any]] = None) -> SystemEvent:
        """Publishes an event to all registered subscribers."""
        event = SystemEvent(name=event_name, data=data or {})
        with self._lock:
            self._history.append(event)
            # Keep recent 200 events
            if len(self._history) > 200:
                self._history.pop(0)
            handlers = list(self._subscribers.get(event_name, []))

        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass  # Handlers shouldn't crash the bus
        return event

    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        with self._lock:
            return [{
                "name": e.name,
                "data": e.data,
                "timestamp": e.timestamp
            } for e in self._history[-limit:]]

# Global Event Bus instance
default_event_bus = EventBus()
