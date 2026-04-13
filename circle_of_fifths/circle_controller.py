# circle_of_fifths/circle_controller.py
import math
import pygame
from event_bus import bus
from theory_engine import TheoryEngine
from .circle_state import CircleState, PulseInfo

# Constants for note names and pitch classes (same as old code)
MAJOR_NOTES = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
MAJOR_PITCHES = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5]
MINOR_NAMES = ["a", "e", "b", "f#", "db", "ab", "eb", "bb", "f", "c", "g", "d"]
MINOR_PITCHES = [(p - 3) % 12 for p in MAJOR_PITCHES]

class CircleController:
    def __init__(self, theory_engine: TheoryEngine):
        self.theory = theory_engine
        self.state = CircleState()
        self.active = False  # whether this widget receives stick input
        self._last_root_note = self.theory.root_note
        self._last_mode = self.theory.mode

        # Subscribe to events
        bus.on("RAW_AXIS_MOVED", self._on_axis_moved)
        bus.on("FOCUS_CHANGED", self._on_focus_changed)
        bus.on("NOTE_ON_SENT", self._on_note_on)
        # Optionally listen to scale changes to reset hover? Not necessary but safe
        bus.on("SCALE_CHANGED", self._on_scale_changed)
        bus.on("TOGGLE_CIRCLE_RING", self._on_toggle_ring)


    def _on_toggle_ring(self):
        self.toggle_ring()

    def _on_focus_changed(self, mode: str):
        """Activate only when focus mode is 'circle'."""
        self.active = (mode == "circle")

    def _on_axis_moved(self, axis: int, value: float):
        if not self.active:
            return
        # We expect right stick axes: axis 2 = X, axis 3 = Y (common on many controllers)
        # But we need both X and Y values. The event gives one axis at a time.
        # We'll store the latest values and process when both have been updated?
        # Simpler: in update loop we could poll, but this is event-driven.
        # Alternative: store axes values and only process when we have both.
        # For simplicity, we will store axes in a dict and process on every axis move.
        if not hasattr(self, '_axes'):
            self._axes = {2: 0.0, 3: 0.0}
        self._axes[axis] = value
        # Process stick only when we have both axes (or just use latest)
        # We'll call _update_stick with current X (axis2) and Y (axis3)
        x = self._axes.get(2, 0.0)
        y = self._axes.get(3, 0.0)
        self._update_stick(-x, -y)

    def _update_stick(self, x: float, y: float):
        """Process stick movement: compute hover index and handle grace timer."""
        dist = math.hypot(x, y)
        if dist < self.state.DEADZONE:
            # In deadzone: increment exit timer
            self.state.exit_timer += 1
            if self.state.exit_timer >= self.state.EXIT_GRACE_FRAMES and self.state.hovered_index is not None:
                self._select_current()
                self.state.hovered_index = None
                self.state.exit_timer = 0
            else:
                # No selection yet, just clear hover?
                # Old code kept hovered_index until exit timer triggers.
                # We'll keep hovered_index as is; it will be cleared on selection or new stick movement.
                pass
            return

        # Stick is outside deadzone: reset exit timer and compute new hover index
        self.state.exit_timer = 0
        angle = math.degrees(math.atan2(y, x))
        angle = (angle + 360) % 360
        angle = (angle - 90) % 360  # 0° = North (top)
        idx = int((angle + 15) // 30) % 12
        if idx != self.state.hovered_index:
            self.state.hovered_index = idx

    def _select_current(self):
        """Select the currently hovered gate and update theory engine."""
        if self.state.hovered_index is None:
            return
        idx = self.state.hovered_index
        if self.state.active_ring == "major":
            note_name = MAJOR_NOTES[idx]
            pitch_class = MAJOR_PITCHES[idx]
            mode = "Major"
        else:
            note_name = MINOR_NAMES[idx]
            pitch_class = MINOR_PITCHES[idx]
            mode = "Minor"

        # Preserve octave from current root note
        current_root = self.theory.root_note
        octave = current_root // 12
        new_root = octave * 12 + pitch_class
        # Clamp to MIDI range (0-127)
        if new_root < 0:
            new_root += 12
        elif new_root > 127:
            new_root -= 12

        # Update theory engine (this will emit SCALE_CHANGED)
        self.theory.set_root(new_root)
        self.theory.set_mode(mode)
        
        # NEW: Activate filter mode with the selected note as pivot
        self.theory.set_filter_mode(True, new_root)

        # Optional: emit a log event for UI
        bus.emit("ADD_LOG", text=f"Circle: {note_name} ({mode}) selected", color=(255,200,100))

        # Reset hover and timer
        self.state.hovered_index = None
        self.state.exit_timer = 0

    def _on_note_on(self, note: int, velocity: int, channel: int):
        """Record pulse when a note is played."""
        pc = note % 12
        # Check if this pitch class exists in either ring (we can precompute sets)
        if pc in MAJOR_PITCHES or pc in MINOR_PITCHES:
            self.state.pulse = PulseInfo(pitch_class=pc, timestamp_ms=pygame.time.get_ticks())

    def _on_scale_changed(self, legal_notes, root_note, mode):
        """Sync internal state if theory changes externally (e.g., from other widgets)."""
        self._last_root_note = root_note
        self._last_mode = mode
        # No need to change hover or selection, just update for view.

    def toggle_ring(self):
        """Switch between major and minor rings."""
        self.state.active_ring = "minor" if self.state.active_ring == "major" else "major"
        bus.emit("ADD_LOG", text=f"Circle ring: {self.state.active_ring.upper()}", color=(200,200,100))

    def get_state(self) -> CircleState:
        """Return current state for the view."""
        return self.state

    def get_theory(self) -> TheoryEngine:
        """Allow view to access theory for scale information."""
        return self.theory