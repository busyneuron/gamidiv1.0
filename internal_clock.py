# internal_clock.py
import os
import threading
import time
from event_bus import bus

PPQN = 24


class InternalClock:
    """Emits MIDI clock ticks on the bus when no external clock is present.
    Auto-pauses while external ticks keep arriving and resumes after silence."""

    def __init__(self, bpm=120.0, silence_resume=2.0):
        self.bpm = bpm
        self.silence_resume = silence_resume
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._last_external = 0.0
        self._internal_active = False
        self._emitting = False
        bus.on("CLOCK_TICK", self._on_external_tick)

    def _on_external_tick(self):
        if self._emitting:
            return
        with self._lock:
            was_active = self._internal_active
            self._last_external = time.monotonic()
            self._internal_active = False
        if was_active:
            bus.emit("ADD_LOG", text="[CLOCK] External clock detected", color=(100, 200, 100))

    def start(self):
        thread = threading.Thread(target=self._run, daemon=True, name="internal-clock")
        thread.start()

    def stop(self):
        self._stop_event.set()

    def _run(self):
        interval = 60.0 / self.bpm / PPQN
        while not self._stop_event.is_set():
            with self._lock:
                silence = time.monotonic() - self._last_external
            if silence > self.silence_resume:
                if not self._internal_active:
                    self._internal_active = True
                    bus.emit("TRANSPORT_START")
                    bus.emit("ADD_LOG", text=f"[CLOCK] Internal clock {self.bpm:g} BPM", color=(100, 200, 100))
                self._emit_tick()
                time.sleep(interval)
            else:
                time.sleep(0.05)

    def _emit_tick(self):
        self._emitting = True
        try:
            bus.emit("CLOCK_TICK")
        finally:
            self._emitting = False


def create_default_clock():
    """Internal clock unless disabled via GAMIDI_INTERNAL_CLOCK=0."""
    if os.environ.get("GAMIDI_INTERNAL_CLOCK", "1") == "0":
        return None
    try:
        bpm = float(os.environ.get("GAMIDI_BPM", "120"))
    except ValueError:
        bpm = 120.0
    return InternalClock(bpm=bpm)
