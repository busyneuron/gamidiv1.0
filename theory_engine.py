# theory_engine.py
class TheoryEngine:
    def __init__(self, root_note=60, mode="Major"):
        self.root_note = root_note
        self.mode = mode
        self.cursor_degree = 0  # 0 = root of scale
        self.cursor_octave = 4  # octave (C4 = 60)
        # Major scale intervals (Ionian)
        self.scale_intervals = [0, 2, 4, 5, 7, 9, 11]
        # Map mode name to intervals (expand later)
        self.modes = {
            "Major": [0, 2, 4, 5, 7, 9, 11],
            "Minor": [0, 2, 3, 5, 7, 8, 10],
        }
        self.set_mode(mode)

    def set_mode(self, mode_name):
        if mode_name in self.modes:
            self.scale_intervals = self.modes[mode_name]
            self.mode = mode_name

    def move_cursor(self, degree_delta):
        """Move cursor by scale degrees, but do nothing if new pitch out of MIDI range."""
        # Store original state
        orig_degree = self.cursor_degree
        orig_octave = self.cursor_octave

        # Tentatively move degree
        self.cursor_degree += degree_delta
        # Wrap around scale, adjusting octave as needed
        while self.cursor_degree >= len(self.scale_intervals):
            self.cursor_degree -= len(self.scale_intervals)
            self.cursor_octave += 1
        while self.cursor_degree < 0:
            self.cursor_degree += len(self.scale_intervals)
            self.cursor_octave -= 1

        # Calculate new pitch
        new_pitch = self.get_cursor_midi_pitch()
        # If out of valid MIDI range, revert changes
        if new_pitch < 0 or new_pitch > 127:
            self.cursor_degree = orig_degree
            self.cursor_octave = orig_octave

    def get_cursor_midi_pitch(self):
        """Return MIDI note number of current cursor position."""
        # root_note is MIDI note of C in octave 4 (default 60 = C4)
        # Convert cursor_octave to offset from octave 4
        octave_offset = self.cursor_octave - 4
        base = self.root_note + octave_offset * 12
        return base + self.scale_intervals[self.cursor_degree]

    def get_pitch_at_offset(self, degree_offset, octave_offset=0):
        """Return MIDI note (may be outside 0-127) for a voice offset."""
        degree = self.cursor_degree + degree_offset
        octave = self.cursor_octave + octave_offset
        # Allow octave to be any integer (negative or large)
        base = self.root_note + (octave - 4) * 12
        # Adjust degree to within scale length, but keep track of extra octave shifts
        scale_len = len(self.scale_intervals)
        extra_octave = 0
        while degree >= scale_len:
            degree -= scale_len
            extra_octave += 1
        while degree < 0:
            degree += scale_len
            extra_octave -= 1
        octave += extra_octave
        base = self.root_note + (octave - 4) * 12
        return base + self.scale_intervals[degree]

    def get_legal_notes(self):
        """Return set of all MIDI notes in the current scale across all octaves."""
        legal = set()
        # Octave range that covers MIDI 0..127 (octave -1 to 9)
        for octave in range(-1, 10):
            base = self.root_note + (octave - 4) * 12
            for interval in self.scale_intervals:
                note = base + interval
                if 0 <= note <= 127:
                    legal.add(note)
        return legal