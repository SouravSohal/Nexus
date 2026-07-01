from typing import Callable, Dict, List, Any
from backend.app.core.logging import logger

class EventBus:
    """
    EventBus represents a lightweight, synchronous, in-memory publisher-subscriber bus.
    It isolates bounded contexts by allowing them to publish and subscribe to domain events.
    """

    def __init__(self):
        self._registry: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_name: str, callback: Callable[[Any], None]) -> None:
        """
        Registers a callback handler for a specific domain event name.
        """
        if event_name not in self._registry:
            self._registry[event_name] = []
        self._registry[event_name].append(callback)
        logger.info(f"[SYSTEM] Subscribed handler to event '{event_name}'")

    def publish(self, event_name: str, event_payload: Any) -> None:
        """
        Synchronously dispatches the event payload to all registered callback handlers.
        """
        if event_name not in self._registry:
            return
            
        for handler in self._registry[event_name]:
            try:
                handler(event_payload)
            except Exception as e:
                logger.error(f"[SYSTEM] Error running event handler for '{event_name}': {str(e)}")
