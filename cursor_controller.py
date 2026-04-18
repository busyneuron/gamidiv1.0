# cursor_controller.py
from event_bus import bus

class CursorController:
    def __init__(self, theory_engine, initial_note=60):
        self.theory = theory_engine
        self._cursor_note = initial_note
        self.jump_interval = 1
        bus.on("ACTION_STATE_CHANGED", self._on_action_state_changed)
        bus.on("CURSOR_MOVED", self._on_cursor_moved)
        bus.on("SCALE_CHANGED", self._on_scale_changed)  # NEW

    @property
    def cursor_note(self):
        return self._cursor_note

    @cursor_note.setter
    def cursor_note(self, value):
        self._cursor_note = value
        bus.emit("CURSOR_MOVED", new_note=self._cursor_note)

    def _on_action_state_changed(self, action_id, active):
        pass

    def _on_cursor_moved(self, new_note):
        self._cursor_note = new_note

    def _on_scale_changed(self, legal_notes, root_note, mode):
        """Snap cursor to the nearest legal note when scale changes."""
        if not legal_notes:
            return
        # Find the note in legal_notes closest to current cursor
        closest = min(legal_notes, key=lambda note: abs(note - self._cursor_note))
        if closest != self._cursor_note:
            self.cursor_note = closest

    def move_up(self):
        new_note = self.theory.get_next_note(self._cursor_note, 1, self.jump_interval, chromatic=False)
        if new_note != self._cursor_note:
            self.cursor_note = new_note

    def move_down(self):
        new_note = self.theory.get_next_note(self._cursor_note, -1, self.jump_interval, chromatic=False)
        if new_note != self._cursor_note:
            self.cursor_note = new_note