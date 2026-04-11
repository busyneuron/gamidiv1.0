# cursor_controller.py
from event_bus import bus

class CursorController:
    def __init__(self, theory_engine, initial_note=60):
        self.theory = theory_engine
        self.cursor_note = initial_note
        self.jump_interval = 1
        # Listen to held actions for jump intervals (placeholder)
        bus.on("ACTION_STATE_CHANGED", self._on_action_state_changed)
        bus.on("CURSOR_MOVED", self._on_cursor_moved)

    def _on_action_state_changed(self, action_id, active):
        # For now, ignore; we'll implement later
        pass

    def _on_cursor_moved(self, new_note):
        self.cursor_note = new_note

    def move_up(self):
        new_note = self.theory.get_next_note(self.cursor_note, 1, self.jump_interval, chromatic=False)
        if new_note != self.cursor_note:
            self.cursor_note = new_note
            bus.emit("CURSOR_MOVED", new_note=self.cursor_note)

    def move_down(self):
        new_note = self.theory.get_next_note(self.cursor_note, -1, self.jump_interval, chromatic=False)
        if new_note != self.cursor_note:
            self.cursor_note = new_note
            bus.emit("CURSOR_MOVED", new_note=self.cursor_note)