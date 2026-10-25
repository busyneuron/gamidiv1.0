# melody_history.py
from collections import defaultdict


class MelodyHistory:
    """Tick-stamped record of the lead voice's note on/off events.

    Canon voices read this back to replay the lead melody after a delay.
    Events are keyed by master tick so a canon can look up exactly what the
    lead played `delay_ticks` ago.
    """

    def __init__(self, max_ticks=768):
        # tick -> list of (kind, note), where kind is "on" or "off"
        self._events = defaultdict(list)
        self._max_ticks = max_ticks

    def record(self, tick, kind, note):
        """Record a note-on ("on") or note-off ("off") event at `tick`."""
        self._events[tick].append((kind, note))
        self._prune(tick)

    def events_at(self, tick):
        """Return the list of (kind, note) events that happened at `tick`."""
        return self._events.get(tick, [])

    def clear(self):
        self._events.clear()

    def _prune(self, current_tick):
        cutoff = current_tick - self._max_ticks
        for t in [t for t in self._events if t < cutoff]:
            del self._events[t]
