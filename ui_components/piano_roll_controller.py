# ui_components/piano_roll_controller.py
from event_bus import bus
from .piano_roll_state import PianoRollState

class PianoRollController:
    def __init__(self, initial_state: PianoRollState = None):
        self.state = initial_state or PianoRollState()
        bus.on("CLOCK_TICK", self._on_clock_tick)
        bus.on("NOTE_ON_SENT", self._on_note_on)
        bus.on("NOTE_OFF_SENT", self._on_note_off)

    def _on_clock_tick(self):
        self.state.pulse_count += 1

    def _on_note_on(self, note, velocity, channel):
        self.state.add_note_on(note, channel, self.state.pulse_count)

    def _on_note_off(self, note, channel):
        self.state.add_note_off(note, channel, self.state.pulse_count)

    def get_state(self) -> PianoRollState:
        return self.state