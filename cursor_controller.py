# cursor_controller.py
from event_bus import bus

class CursorController:
    def __init__(self, theory_engine, initial_note=60):
        self.theory = theory_engine
        self._cursor_note = initial_note
        self.jump_interval = 1
        self.temp_jump_interval = None
        bus.on("ACTION_STATE_CHANGED", self._on_action_state_changed)
        bus.on("CURSOR_MOVED", self._on_cursor_moved)
        bus.on("SCALE_CHANGED", self._on_scale_changed)

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
        if not legal_notes:
            return
        closest = min(legal_notes, key=lambda note: abs(note - self._cursor_note))
        if closest != self._cursor_note:
            self.cursor_note = closest

    def set_temp_jump_interval(self, interval):
        self.temp_jump_interval = interval
        bus.emit("JUMP_INTERVAL_CHANGED", interval=self._get_current_interval())

    def clear_temp_jump_interval(self):
        self.temp_jump_interval = None
        bus.emit("JUMP_INTERVAL_CHANGED", interval=self._get_current_interval())

    def _get_current_interval(self):
        return self.temp_jump_interval if self.temp_jump_interval is not None else self.jump_interval

    def move_up(self):
        interval = self._get_current_interval()
        new_note = self.theory.get_next_note(self._cursor_note, 1, interval, chromatic=False)
        if new_note != self._cursor_note:
            self.cursor_note = new_note

    def move_down(self):
        interval = self._get_current_interval()
        new_note = self.theory.get_next_note(self._cursor_note, -1, interval, chromatic=False)
        if new_note != self._cursor_note:
            self.cursor_note = new_note