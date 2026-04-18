# ui_components/keyboard_controller.py
import time
from event_bus import bus
from .keyboard_state import KeyboardState

class KeyboardController:
    def __init__(self, initial_state: KeyboardState, theory_engine):
        self.state = initial_state
        self.theory = theory_engine
        self.current_cursor = initial_state.current_note
        self.current_jump_interval = 1

        bus.on("NOTE_ON_SENT", self._on_note_on)
        bus.on("NOTE_OFF_SENT", self._on_note_off)
        bus.on("CURSOR_MOVED", self._on_cursor_moved)
        bus.on("SCALE_CHANGED", self._on_scale_changed)
        bus.on("ROOT_CHANGED", self._on_root_changed)
        bus.on("JUMP_INTERVAL_CHANGED", self._on_jump_interval_changed)

        self._update_reachable_notes()

    def _on_note_on(self, note, velocity, channel):
        self.state.active_notes.add(note)
        self.state.last_trigger_time[note] = time.time()

    def _on_note_off(self, note, channel):
        self.state.active_notes.discard(note)

    def _on_cursor_moved(self, new_note):
        self.state.current_note = new_note
        self.current_cursor = new_note
        self._update_reachable_notes()

    def _on_jump_interval_changed(self, interval):
        self.current_jump_interval = interval
        self._update_reachable_notes()

    def _on_scale_changed(self, legal_notes, root_note, mode):
        self.state.legal_notes = set(legal_notes)
        self.state.root_note = root_note
        self.state.root_pc = root_note % 12
        self._update_reachable_notes()

    def _on_root_changed(self, root_note):
        self.state.root_note = root_note
        self.state.root_pc = root_note % 12
        self._update_reachable_notes()

    def _update_reachable_notes(self):
        if self.current_jump_interval <= 1:
            self.state.reachable_notes = None
        else:
            reachable = self.theory.get_reachable_notes(self.current_cursor, self.current_jump_interval)
            self.state.reachable_notes = reachable if reachable else None

    def get_state(self) -> KeyboardState:
        return self.state