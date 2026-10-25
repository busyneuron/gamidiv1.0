# ui_components/keyboard_controller.py
import time
from event_bus import bus
from .keyboard_state import KeyboardState

class KeyboardController:
    def __init__(self, initial_state: KeyboardState, theory_engine):
        self.state = initial_state
        self.theory = theory_engine
        self.current_note = initial_state.current_note

        # Subscribe to events
        bus.on("NOTE_ON_SENT", self._on_note_on)
        bus.on("NOTE_OFF_SENT", self._on_note_off)
        bus.on("CURSOR_MOVED", self._on_cursor_moved)
        bus.on("SCALE_CHANGED", self._on_scale_changed)
        bus.on("ROOT_CHANGED", self._on_root_changed)
        bus.on("REACHABLE_NOTES_CHANGED", self._on_reachable_notes_changed)

    def _on_note_on(self, note, velocity, channel):
        self.state.active_notes.add(note)
        self.state.last_trigger_time[note] = time.time()

    def _on_note_off(self, note, channel):
        self.state.active_notes.discard(note)

    def _on_cursor_moved(self, new_note):
        self.current_note = new_note
        self.state.current_note = new_note
        # reachable notes handled by separate event

    def _on_scale_changed(self, legal_notes, root_note, mode):
        self.state.legal_notes = set(legal_notes)
        self.state.root_note = root_note
        self.state.root_pc = root_note % 12

    def _on_root_changed(self, root_note):
        self.state.root_note = root_note
        self.state.root_pc = root_note % 12

    def _on_reachable_notes_changed(self, reachable):
        self.state.reachable_notes = reachable

    def get_state(self) -> KeyboardState:
        return self.state