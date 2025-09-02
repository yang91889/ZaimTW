from __future__ import annotations
from typing import Callable, Dict, List, Any

class EventBus:
    def __init__(self) -> None:
        self._subs: Dict[str, List[Callable[[Any], None]]] = {}

    def publish(self, topic: str, payload: Any = None) -> None:
        for cb in self._subs.get(topic, []):
            try:
                cb(payload)
            except Exception:
                # 這裡可加上你的 log
                pass

    def subscribe(self, topic: str, cb: Callable[[Any], None]) -> None:
        self._subs.setdefault(topic, []).append(cb)

# Topics
EV_TX_CREATED = "tx_created"
EV_RATES_UPDATED = "rates_updated"
