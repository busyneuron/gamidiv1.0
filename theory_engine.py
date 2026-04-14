# theory_engine.py
from event_bus import bus

class TheoryEngine:
    def __init__(self, root_note=60, mode="Major"):
        self.root_note = root_note
        self.mode = mode
        self.accidental_offsets = {}          # degree_index -> semitone shift
        self.filter_root = False
        self.filter_pivot_note = None
        self.extensions = set()               # intervals 6,8,10,12
        self.omissions = set()                # intervals 2,4

        self.SCALES = {
            "Major": [0,2,4,5,7,9,11],
            "Minor": [0,2,3,5,7,8,10],
            "Dorian": [0,2,3,5,7,9,10],
            "Phrygian": [0,1,3,5,7,8,10], 
            "Lydian": [0,2,4,6,7,9,11],
            "Mixolydian": [0,2,4,5,7,9,10],
            "Locrian": [0,1,3,5,6,8,10],
        }
        self._update_effective_intervals()
        self._emit_chord_qualities()   # initial emission

    def _update_effective_intervals(self):
        base = self.SCALES[self.mode]
        self.effective_intervals = []
        for i, interval in enumerate(base):
            shift = self.accidental_offsets.get(i, 0)
            self.effective_intervals.append((interval + shift) % 12)

    def _emit_chord_qualities(self):
        """Compute chord qualities and emit event."""
        qualities = self.get_chord_qualities()
        bus.emit("CHORD_QUALITIES_CHANGED", qualities=qualities)

    def get_chord_qualities(self):
        """
        Return a dict mapping pitch_class (0-11) to:
        {
            'diatonic': bool,
            'degree': int (0-6) or None,
            'quality': 'tonic' | 'major' | 'minor' | 'diminished' | None,
            'roman': str or None
        }
        """
        root_pc = self.root_note % 12
        intervals = self.effective_intervals  # 7 ints

        # Precompute triad quality for each degree
        triad_quality = []
        for d in range(7):
            root_int = intervals[d]
            third_int = intervals[(d + 2) % 7]
            fifth_int = intervals[(d + 4) % 7]
            third_dist = (third_int - root_int) % 12
            fifth_dist = (fifth_int - root_int) % 12
            if third_dist == 4 and fifth_dist == 7:
                quality = "major"
            elif third_dist == 3 and fifth_dist == 7:
                quality = "minor"
            elif third_dist == 3 and fifth_dist == 6:
                quality = "diminished"
            else:
                quality = None  # should not happen for diatonic
            triad_quality.append(quality)

        # Roman numeral map
        roman_map = ["I", "II", "III", "IV", "V", "VI", "VII"]

        result = {}
        # Initialize all 12 pitch classes as non-diatonic
        for pc in range(12):
            result[pc] = {
                'diatonic': False,
                'degree': None,
                'quality': None,
                'roman': None
            }

        # Fill diatonic notes
        for d, interval in enumerate(intervals):
            pc = (root_pc + interval) % 12
            quality = triad_quality[d]
            # Override quality for tonic (degree 0)
            if d == 0:
                quality = "tonic"
            roman = roman_map[d]
            if quality == "minor":
                roman = roman.lower()
            elif quality == "diminished":
                roman = roman.lower() + "°"
            # For major and tonic, keep uppercase
            result[pc] = {
                'diatonic': True,
                'degree': d,
                'quality': quality,
                'roman': roman
            }
        return result

    # --- Scale & root ---
    def set_mode(self, mode_name):
        if mode_name in self.SCALES:
            self.mode = mode_name
            self._update_effective_intervals()
            self._emit_chord_qualities()
            bus.emit("SCALE_CHANGED", legal_notes=self.get_legal_notes(),
                     root_note=self.root_note, mode=self.mode)

    def set_root(self, new_root):
        self.root_note = new_root
        self._update_effective_intervals()
        self._emit_chord_qualities()
        bus.emit("SCALE_CHANGED", legal_notes=self.get_legal_notes(),
                 root_note=self.root_note, mode=self.mode)

    # --- Accidentals ---
    def modify_degree_by_note(self, note, delta):
        note_pc = (note - self.root_note) % 12
        for i, interval in enumerate(self.effective_intervals):
            if interval % 12 == note_pc:
                self.accidental_offsets[i] = self.accidental_offsets.get(i, 0) + delta
                self._update_effective_intervals()
                self._emit_chord_qualities()
                bus.emit("ACCIDENTALS_CHANGED", accidentals=self.accidental_offsets)
                bus.emit("SCALE_CHANGED", legal_notes=self.get_legal_notes(),
                         root_note=self.root_note, mode=self.mode)
                return True
        return False

    def reset_accidentals(self):
        self.accidental_offsets.clear()
        self._update_effective_intervals()
        self._emit_chord_qualities()
        bus.emit("ACCIDENTALS_CHANGED", accidentals={})
        bus.emit("SCALE_CHANGED", legal_notes=self.get_legal_notes(),
                 root_note=self.root_note, mode=self.mode)

    # --- Filter mode ---
    def set_filter_mode(self, active, pivot_note=None):
        self.filter_root = active
        if pivot_note is not None:
            self.filter_pivot_note = pivot_note
        self._update_effective_intervals()
        self._emit_chord_qualities()
        bus.emit("FILTER_MODE_CHANGED", active=active, pivot=self.filter_pivot_note)
        bus.emit("SCALE_CHANGED", legal_notes=self.get_legal_notes(),
                 root_note=self.root_note, mode=self.mode)

    def set_extensions(self, extensions):
        self.extensions = set(extensions)
        if self.filter_root:
            self._update_effective_intervals()
            self._emit_chord_qualities()
            bus.emit("SCALE_CHANGED", legal_notes=self.get_legal_notes(),
                     root_note=self.root_note, mode=self.mode)

    def set_omissions(self, omissions):
        self.omissions = set(omissions)
        if self.filter_root:
            self._update_effective_intervals()
            self._emit_chord_qualities()
            bus.emit("SCALE_CHANGED", legal_notes=self.get_legal_notes(),
                     root_note=self.root_note, mode=self.mode)

    # --- Legal notes (unchanged from your version) ---
    def get_legal_notes(self):
        if self.filter_root and self.filter_pivot_note is not None:
            return self._get_filter_legal_notes()
        else:
            return self._get_scale_legal_notes()

    def _get_scale_legal_notes(self):
        legal = set()
        for octave in range(-1, 10):
            base = self.root_note + (octave - 4) * 12
            for interval in self.effective_intervals:
                note = base + interval
                if 0 <= note <= 127:
                    legal.add(note)
        return legal

    def _get_filter_legal_notes(self):
        # Find degree index of pivot note
        pivot_pc = (self.filter_pivot_note - self.root_note) % 12
        pivot_degree = None
        for i, interval in enumerate(self.effective_intervals):
            if interval % 12 == pivot_pc:
                pivot_degree = i
                break
        if pivot_degree is None:
            return self._get_scale_legal_notes()

        chord_degrees = [pivot_degree, pivot_degree+2, pivot_degree+4]
        for ext in self.extensions:
            chord_degrees.append(pivot_degree + ext)
        # Remove omitted degrees (relative to pivot)
        chord_degrees = [d for d in chord_degrees if (d - pivot_degree) not in self.omissions]

        legal = set()
        for octave in range(-1, 10):
            for d in chord_degrees:
                octave_shift, idx = divmod(d, 7)
                interval = self.effective_intervals[idx] + 12 * octave_shift
                note = self.root_note + interval + (octave - 4) * 12
                if 0 <= note <= 127:
                    legal.add(note)
        return legal

    # --- Helper for voices (cursor note is external) ---
    def get_pitch_at_offset(self, cursor_note, degree_offset, octave_offset=0):
        legal = sorted(self.get_legal_notes())
        if not legal:
            return cursor_note
        try:
            idx = legal.index(cursor_note)
        except ValueError:
            idx = min(range(len(legal)), key=lambda i: abs(legal[i] - cursor_note))
        target_idx = idx + degree_offset + octave_offset * len(legal)
        target_idx = max(0, min(target_idx, len(legal)-1))
        return legal[target_idx]

    # --- Cursor movement helper ---
    def get_next_note(self, current_note, direction, jump=1, chromatic=False):
        if chromatic:
            new_note = current_note + direction
            if 0 <= new_note <= 127:
                return new_note
            return current_note
        legal = sorted(self.get_legal_notes())
        if not legal:
            return current_note
        try:
            idx = legal.index(current_note)
        except ValueError:
            idx = min(range(len(legal)), key=lambda i: abs(legal[i] - current_note))
        new_idx = idx + direction * jump
        new_idx = max(0, min(new_idx, len(legal)-1))
        return legal[new_idx]

    def get_offset_between_notes(self, from_note, to_note):
        legal = sorted(self.get_legal_notes())
        if not legal:
            return 0, 0
        def closest_idx(note):
            try:
                return legal.index(note)
            except ValueError:
                return min(range(len(legal)), key=lambda i: abs(legal[i] - note))
        from_idx = closest_idx(from_note)
        to_idx = closest_idx(to_note)
        diff = to_idx - from_idx
        degree_offset = diff % len(legal)
        octave_offset = diff // len(legal)
        return degree_offset, octave_offset