# event_bus.py
from typing import Callable, Dict, List, Any

class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def on(self, event_name: str, callback: Callable):
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)

    def off(self, event_name: str, callback: Callable):
        if event_name in self._listeners:
            self._listeners[event_name].remove(callback)

    def emit(self, event_name: str, **data):
        for cb in self._listeners.get(event_name, []):
            cb(**data)

# Global instance (or you can pass around)
bus = EventBus()