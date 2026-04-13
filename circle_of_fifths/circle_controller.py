# circle_of_fifths/circle_controller.py
import math
import pygame
from typing import Optional
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

        
        bus.on("RIGHT_STICK_UPDATED", self._on_stick_updated)
        bus.on("FOCUS_CHANGED", self._on_focus_changed)
        bus.on("NOTE_ON_SENT", self._on_note_on)
        
        bus.on("SCALE_CHANGED", self._on_scale_changed)
        bus.on("TOGGLE_CIRCLE_RING", self._on_toggle_ring)
        bus.on("TOGGLE_DEGREE_MODE", self._on_toggle_degree_mode)

    def _get_scale_degree(self, pitch_class: int, is_major_ring: bool) -> Optional[int]:
        """
        Return the scale degree index (0-6) if pitch_class is in the current scale,
        otherwise None. Assumes root is self.theory.root_note.
        """
        root_pc = self.theory.root_note % 12
        intervals = self.theory.effective_intervals  # list of 7 ints (semitones from root)
        target = (pitch_class - root_pc) % 12
        for i, interval in enumerate(intervals):
            if interval % 12 == target:
                return i
        return None

    def _is_diatonic(self, gate_idx: int, is_major_ring: bool) -> bool:
        pc = MAJOR_PITCHES[gate_idx] if is_major_ring else MINOR_PITCHES[gate_idx]
        return self._get_scale_degree(pc, is_major_ring) is not None

    def _get_roman_numeral(self, gate_idx: int, is_major_ring: bool) -> str:
        pc = MAJOR_PITCHES[gate_idx] if is_major_ring else MINOR_PITCHES[gate_idx]
        degree = self._get_scale_degree(pc, is_major_ring)
        if degree is None:
            return ""  # should not happen for diatonic
        
        # Determine triad quality for this degree
        intervals = self.theory.effective_intervals
        root_int = intervals[degree]
        third_int = intervals[(degree + 2) % 7]
        fifth_int = intervals[(degree + 4) % 7]
        third_dist = (third_int - root_int) % 12
        fifth_dist = (fifth_int - root_int) % 12
        
        if third_dist == 4 and fifth_dist == 7:
            quality = "major"
        elif third_dist == 3 and fifth_dist == 7:
            quality = "minor"
        elif third_dist == 3 and fifth_dist == 6:
            quality = "diminished"
        else:
            quality = "other"
        
        roman_map = ["I", "II", "III", "IV", "V", "VI", "VII"]
        roman = roman_map[degree]
        if quality == "minor":
            roman = roman.lower()
        elif quality == "diminished":
            roman = roman.lower() + "°"
        return roman
    
    def _on_toggle_degree_mode(self):
        self.toggle_degree_mode()

    def toggle_degree_mode(self):
        self.state.degree_mode = not self.state.degree_mode
        if not self.state.degree_mode:
            # Clear selected degree when exiting degree mode
            self.state.selected_degree_index = None
        bus.emit("ADD_LOG", text=f"Degree mode: {'ON' if self.state.degree_mode else 'OFF'}", color=(200,200,100))

    def _on_toggle_ring(self):
        self.toggle_ring()

    def _on_focus_changed(self, mode: str):
        """Activate only when focus mode is 'circle'."""
        self.active = (mode == "circle")

    def _on_stick_updated(self, x: float, y: float):
        if not self.active:
            return
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
            
    def _has_major_triad(self, gate_idx: int, is_major_ring: bool) -> bool:
        """Return True if this gate represents a major triad in the current scale."""
        pc = MAJOR_PITCHES[gate_idx] if is_major_ring else MINOR_PITCHES[gate_idx]
        root_pc = self.theory.root_note % 12
        intervals = self.theory.effective_intervals
        pc_to_degree = {}
        for d, interval in enumerate(intervals):
            note_pc = (root_pc + interval) % 12
            pc_to_degree[note_pc] = d
        
        if pc not in pc_to_degree:
            return False
        deg = pc_to_degree[pc]
        
        # Get triad quality for this degree
        root_int = intervals[deg]
        third_int = intervals[(deg + 2) % 7]
        fifth_int = intervals[(deg + 4) % 7]
        third_dist = (third_int - root_int) % 12
        fifth_dist = (fifth_int - root_int) % 12
        
        return (third_dist == 4 and fifth_dist == 7)  # major triad

    def _has_minor_triad(self, gate_idx: int, is_major_ring: bool) -> bool:
        """Return True if this gate represents a minor triad in the current scale."""
        pc = MAJOR_PITCHES[gate_idx] if is_major_ring else MINOR_PITCHES[gate_idx]
        root_pc = self.theory.root_note % 12
        intervals = self.theory.effective_intervals
        pc_to_degree = {}
        for d, interval in enumerate(intervals):
            note_pc = (root_pc + interval) % 12
            pc_to_degree[note_pc] = d
        
        if pc not in pc_to_degree:
            return False
        deg = pc_to_degree[pc]
        
        # Get triad quality for this degree
        root_int = intervals[deg]
        third_int = intervals[(deg + 2) % 7]
        fifth_int = intervals[(deg + 4) % 7]
        third_dist = (third_int - root_int) % 12
        fifth_dist = (fifth_int - root_int) % 12
        
        return (third_dist == 3 and fifth_dist == 7)  # minor triad

    def _select_current(self):
        """Select the currently hovered gate and update theory engine."""
        if self.state.hovered_index is None:
            return
        idx = self.state.hovered_index
        is_major_ring = (self.state.active_ring == "major")
        
        # Determine if this gate should be treated as a "degree mode selection"
        # This requires: degree mode active AND the gate should show a numeral
        should_treat_as_degree = False
        if self.state.degree_mode:
            # Check if this gate would show a roman numeral (same logic as view)
            is_diatonic = self._is_diatonic(idx, is_major_ring)
            if is_diatonic:
                if is_major_ring:
                    # Outer ring: only major chords
                    has_triad = self._has_major_triad(idx, is_major_ring)
                    should_treat_as_degree = has_triad
                else:
                    # Inner ring: only minor chords
                    has_triad = self._has_minor_triad(idx, is_major_ring)
                    should_treat_as_degree = has_triad
        
        if should_treat_as_degree:
            # Degree mode selection: set filter pivot without changing root
            pitch_class = MAJOR_PITCHES[idx] if is_major_ring else MINOR_PITCHES[idx]
            current_root = self.theory.root_note
            octave = current_root // 12
            pivot_note = octave * 12 + pitch_class
            if pivot_note < 0:
                pivot_note += 12
            elif pivot_note > 127:
                pivot_note -= 12
            
            self.theory.set_filter_mode(True, pivot_note)
            self.state.selected_degree_index = idx
            roman = self._get_roman_numeral(idx, is_major_ring)
            bus.emit("ADD_LOG", text=f"Degree: {roman} selected", color=(255,200,100))
        else:
            # Non-degree selection: change root and mode
            self.state.selected_degree_index = None
            
            if is_major_ring:
                note_name = MAJOR_NOTES[idx]
                pitch_class = MAJOR_PITCHES[idx]
                mode = "Major"
            else:
                note_name = MINOR_NAMES[idx]
                pitch_class = MINOR_PITCHES[idx]
                mode = "Minor"

            current_root = self.theory.root_note
            octave = current_root // 12
            new_root = octave * 12 + pitch_class
            if new_root < 0:
                new_root += 12
            elif new_root > 127:
                new_root -= 12

            self.theory.set_root(new_root)
            self.theory.set_mode(mode)
            self.theory.set_filter_mode(True, new_root)

            bus.emit("ADD_LOG", text=f"Circle: {note_name} ({mode}) selected", color=(255,200,100))
        
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