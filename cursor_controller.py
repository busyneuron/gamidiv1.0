# cursor_controller.py
from event_bus import bus

class CursorController:
    def __init__(self, theory_engine, initial_note=60):
        self.theory = theory_engine
        self._cursor_note = initial_note
        self.jump_interval = 1
        self.active_jump_intervals = set()
        self._reachable_notes = None

        # --- Cursor movement modes ---
        self._continuous_mode = False       # False = PRESS, True = HIT
        self._held_up = False
        self._held_down = False
        self._note_was_sent_last_tick = False

        bus.on("ACTION_STATE_CHANGED", self._on_action_state_changed)
        bus.on("CURSOR_MOVED", self._on_cursor_moved)
        bus.on("SCALE_CHANGED", self._on_scale_changed)
        bus.on("MASTER_TICK", self._on_master_tick)
        bus.on("NOTE_ON_SENT", self._on_note_on_sent)

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
        if new_note != self._cursor_note:
            self._cursor_note = new_note
            self._update_reachable_notes()

    def _on_scale_changed(self, legal_notes, root_note, mode):
        self._update_reachable_notes()

    def _update_reachable_notes(self):
        if self.jump_interval <= 1:
            self._reachable_notes = None
        else:
            reachable = set()
            note = self._cursor_note
            while True:
                next_note = self.theory.get_next_note(note, 1, self.jump_interval, chromatic=False)
                if next_note == note or next_note < 0 or next_note > 127:
                    break
                note = next_note
                reachable.add(note)
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

    # --- Cursor movement mode (PRESS vs HIT) ---
    def set_cursor_mode(self, continuous: bool):
        """Switch between PRESS (one move per press) and HIT (one move per note)."""
        if continuous == self._continuous_mode:
            return
        self._continuous_mode = continuous
        self._held_up = self._held_down = False
        self._note_was_sent_last_tick = False
        label = "HIT" if continuous else "PRESS"
        bus.emit("ADD_LOG", text=f"Cursor mode: {label}", color=(200, 200, 100))

    def is_continuous_mode(self) -> bool:
        return self._continuous_mode

    def set_held(self, direction: str, held: bool):
        """Called on button press/release. In PRESS mode, press triggers immediate move."""
        if direction == "up":
            self._held_up = held
        elif direction == "down":
            self._held_down = held
        if not self._continuous_mode and held:
            if direction == "up":
                self.move_up()
            elif direction == "down":
                self.move_down()

    def _on_note_on_sent(self, note, velocity, channel):
        if self._continuous_mode:
            self._note_was_sent_last_tick = True

    def _on_master_tick(self, tick, bar=0, tick_in_bar=0, **kwargs):
        if not self._continuous_mode:
            self._note_was_sent_last_tick = False
            return
        if not self._note_was_sent_last_tick:
            return
        self._note_was_sent_last_tick = False
        if self._held_up and not self._held_down:
            self.move_up()
        elif self._held_down and not self._held_up:
            self.move_down()