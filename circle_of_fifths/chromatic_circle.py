# circle_of_fifths/chromatic_circle.py
from event_bus import bus
from .base_circle import BaseCircle, MAJOR_NOTES, MINOR_NAMES, MAJOR_PITCHES, MINOR_PITCHES

class ChromaticCircle(BaseCircle):
    def __init__(self, parent, theory_engine):
        super().__init__(parent, theory_engine)

    def get_gate_label(self, gate_index: int, is_major_ring: bool, chord_info: dict) -> str:
        """Return the note name (e.g., 'C', 'G', 'a', 'e', etc.)."""
        if is_major_ring:
            return MAJOR_NOTES[gate_index]
        else:
            return MINOR_NAMES[gate_index]

    def on_select(self, gate_index: int) -> None:
        """Change root and mode to the selected gate."""
        is_major = (self.active_ring == "major")
        pc = MAJOR_PITCHES[gate_index] if is_major else MINOR_PITCHES[gate_index]
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

        # Highlight the new tonic gate
        self.selected_index = gate_index
        self.selected_ring = self.active_ring
        bus.emit("ADD_LOG", text=f"Circle: {note_name} ({mode}) selected", color=(255,200,100))

    def get_center_text(self) -> str:
        """Chromatic mode has no center text."""
        return None

    def toggle_ring(self):
        super().toggle_ring()
        self.selected_index = None
        self.selected_ring = None