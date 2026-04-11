# ui_components/keyboard_controller.py
import time
from event_bus import bus
from .keyboard_state import KeyboardState

class KeyboardController:
    def __init__(self, initial_state: KeyboardState):
        self.state = initial_state

        # Subscribe to events
        bus.on("NOTE_ON_SENT", self._on_note_on)
        bus.on("NOTE_OFF_SENT", self._on_note_off)
        bus.on("CURSOR_MOVED", self._on_cursor_moved)
        bus.on("SCALE_CHANGED", self._on_scale_changed)
        bus.on("ROOT_CHANGED", self._on_root_changed)
    
    def _on_note_on(self, note, velocity, channel):
        self.state.active_notes.add(note)
        self.state.last_trigger_time[note] = time.time()

    def _on_note_off(self, note, channel):
        self.state.active_notes.discard(note)
        # keep last_trigger_time for fade; it will naturally expire

    def _on_cursor_moved(self, new_note):
        self.state.current_note = new_note

    def _on_scale_changed(self, legal_notes, root_note, mode):
        self.state.legal_notes = set(legal_notes)
        self.state.root_note = root_note
        self.state.root_pc = root_note % 12
        # Optionally store mode for display elsewhere

    def _on_root_changed(self, root_note):
        self.state.root_note = root_note
        self.state.root_pc = root_note % 12

    def get_state(self) -> KeyboardState:
        return self.state