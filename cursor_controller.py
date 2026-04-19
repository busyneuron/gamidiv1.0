# cursor_controller.py
from event_bus import bus

class CursorController:
    def __init__(self, theory_engine, initial_note=60):
        self.theory = theory_engine
        self._cursor_note = initial_note
        self.jump_interval = 1
        self.active_jump_intervals = set()
        self._reachable_notes = None
        bus.on("ACTION_STATE_CHANGED", self._on_action_state_changed)
        bus.on("CURSOR_MOVED", self._on_cursor_moved)
        bus.on("SCALE_CHANGED", self._on_scale_changed)

    @property
    def cursor_note(self):
        return self._cursor_note

    @cursor_note.setter
    def cursor_note(self, value):
        if value != self._cursor_note:
            self._cursor_note = value
            self._update_reachable_notes()
            bus.emit("CURSOR_MOVED", new_note=self._cursor_note)

    def _on_action_state_changed(self, action_id, active):
        if action_id.startswith("jump_interval_"):
            interval = int(action_id.split("_")[-1]) - 1
            if active:
                self.active_jump_intervals.add(interval)
            else:
                self.active_jump_intervals.discard(interval)
            new_interval = max(self.active_jump_intervals) if self.active_jump_intervals else 1
            if new_interval != self.jump_interval:
                self.jump_interval = new_interval
                self._update_reachable_notes()

    def _on_cursor_moved(self, new_note):
        # Already handled by setter; this is for external changes
        if new_note != self._cursor_note:
            self._cursor_note = new_note
            self._update_reachable_notes()

    def _on_scale_changed(self, legal_notes, root_note, mode):
        if not legal_notes:
            return
        # Find the note in legal_notes closest to current cursor
        closest = min(legal_notes, key=lambda note: abs(note - self._cursor_note))
        if closest != self._cursor_note:
            self.cursor_note = closest
        # Scale change may affect reachable notes because get_next_note depends on legal notes
        self._update_reachable_notes()

    def _update_reachable_notes(self):
        if self.jump_interval <= 1:
            self._reachable_notes = None
        else:
            reachable = set()
            # Upward
            note = self._cursor_note
            while True:
                next_note = self.theory.get_next_note(note, 1, self.jump_interval, chromatic=False)
                if next_note == note or next_note < 0 or next_note > 127:
                    break
                note = next_note
                reachable.add(note)
            # Downward
            note = self._cursor_note
            while True:
                next_note = self.theory.get_next_note(note, -1, self.jump_interval, chromatic=False)
                if next_note == note or next_note < 0 or next_note > 127:
                    break
                note = next_note
                reachable.add(note)
            reachable.add(self._cursor_note)
            self._reachable_notes = reachable
        bus.emit("REACHABLE_NOTES_CHANGED", reachable=self._reachable_notes)

    def move_up(self):
        new_note = self.theory.get_next_note(self._cursor_note, 1, self.jump_interval, chromatic=False)
        if new_note != self._cursor_note:
            self.cursor_note = new_note

    def move_down(self):
        new_note = self.theory.get_next_note(self._cursor_note, -1, self.jump_interval, chromatic=False)
        if new_note != self._cursor_note:
            self.cursor_note = new_note