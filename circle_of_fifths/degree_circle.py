# circle_of_fifths/degree_circle.py
from event_bus import bus
from .base_circle import BaseCircle, MAJOR_NOTES, MINOR_NAMES, MAJOR_PITCHES, MINOR_PITCHES

class DegreeCircle(BaseCircle):
    def __init__(self, parent, theory_engine):
        super().__init__(parent, theory_engine)
        # Optional: custom colors for selected gate (can be set in apply_theme)
        self.major_selected_color = (255, 215, 0)   # gold
        self.minor_selected_color = (255, 215, 0)   # gold
        self.radius_selected = self.radius_tonic    # same as tonic by default

    def apply_theme(self, theme):
        """Override to also set selected colors from theme."""
        super().apply_theme(theme)
        # Use theme.bright for selected color, or keep gold
        self.major_selected_color = theme.bright
        self.minor_selected_color = theme.bright

    def get_gate_label(self, gate_index: int, is_major_ring: bool, chord_info: dict) -> str:
        """Return roman numeral if gate is diatonic and matches ring quality; otherwise note name."""
        is_diatonic = chord_info.get('diatonic', False)
        quality = chord_info.get('quality')
        roman = chord_info.get('roman', '')

        if is_diatonic:
            if quality == 'tonic':
                return roman
            elif is_major_ring and quality == 'major':
                return roman
            elif not is_major_ring and quality == 'minor':
                return roman
        # Fallback to note name
        return MAJOR_NOTES[gate_index] if is_major_ring else MINOR_NAMES[gate_index]

    def get_gate_style(self, is_focused: bool, is_major_ring: bool,
                       is_tonic: bool, has_triad: bool, is_diatonic: bool,
                       is_selected: bool):
        """Override to use selected color for the chosen degree."""
        if is_selected:
            # Use custom selected color and radius
            if is_major_ring:
                return self.major_selected_color, self.radius_selected, self.major_focused_text
            else:
                return self.minor_selected_color, self.radius_selected, self.minor_focused_text
        else:
            # Fallback to base style (tonic, triad, diatonic, other)
            if is_major_ring:
                return self._get_major_gate_style(is_focused, is_tonic, has_triad, is_diatonic)
            else:
                return self._get_minor_gate_style(is_focused, is_tonic, has_triad, is_diatonic)

    def on_select(self, gate_index: int) -> None:
        """Set filter pivot without changing root. Also highlight selected gate."""
        is_major = (self.active_ring == "major")
        pc = MAJOR_PITCHES[gate_index] if is_major else MINOR_PITCHES[gate_index]
        info = self.chord_qualities.get(pc, {})
        is_diatonic = info.get('diatonic', False)
        quality = info.get('quality')
        roman = info.get('roman', '')

        # Only treat as degree if it's a diatonic chord matching the ring quality (or tonic)
        should_treat = False
        if is_diatonic:
            if quality == 'tonic':
                should_treat = True
            elif is_major and quality == 'major':
                should_treat = True
            elif not is_major and quality == 'minor':
                should_treat = True

        if should_treat:
            current_root = self.theory.root_note
            octave = current_root // 12
            pivot_note = octave * 12 + pc
            if pivot_note < 0:
                pivot_note += 12
            elif pivot_note > 127:
                pivot_note -= 12

            self.theory.set_filter_mode(True, pivot_note)
            self.selected_index = gate_index   # highlight this gate
            bus.emit("ADD_LOG", text=f"Degree: {roman} selected", color=(255,200,100))
        else:
            # Non-diatonic or wrong quality: treat as chromatic selection (change root)
            note_name = MAJOR_NOTES[gate_index] if is_major else MINOR_NAMES[gate_index]
            mode = "Major" if is_major else "Minor"
            current_root = self.theory.root_note
            octave = current_root // 12
            new_root = octave * 12 + pc
            if new_root < 0:
                new_root += 12
            elif new_root > 127:
                new_root -= 12

            self.theory.set_root(new_root)
            self.theory.set_mode(mode)
            self.theory.set_filter_mode(True, new_root)
            self.selected_index = gate_index   # highlight new tonic
            bus.emit("ADD_LOG", text=f"Circle: {note_name} ({mode}) selected", color=(255,200,100))

    def get_center_text(self) -> str:
        """Return the roman numeral of the selected gate (if any)."""
        if self.selected_index is not None:
            is_major = (self.active_ring == "major")
            pc = MAJOR_PITCHES[self.selected_index] if is_major else MINOR_PITCHES[self.selected_index]
            info = self.chord_qualities.get(pc, {})
            roman = info.get('roman', '')
            return roman
        return None

    def toggle_ring(self):
        """When toggling rings, clear selected index (or keep? We choose to clear)."""
        super().toggle_ring()
        self.selected_index = None