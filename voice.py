# voice.py
from rhythm_engine import RhythmEngine

class Voice:
    def __init__(self, voice_id, event_bus, theory_engine, degree_offset=0, octave_offset=0, channel=0):
        self.id = voice_id
        self.bus = event_bus
        self.theory = theory_engine
        self.degree_offset = degree_offset
        self.octave_offset = octave_offset
        self.channel = channel
        self.muted = False

        # Mode: "ostinato" or "sustain"
        self.mode = "ostinato"

        # Ostinato data
        self.motif = [("quarter", "normal")]
        self.compiled_motif = RhythmEngine.compile_motif(self.motif)
        self._update_cumulative()
        self.last_played_note = None

        # Sustain data
        self.sustain_current_note = None
        self.sustain_target_note = None
        self.sustain_quant_ticks = 12   # quarter note

    def _update_cumulative(self):
        self.cumulative_starts = []
        running = 0
        for step in self.compiled_motif:
            self.cumulative_starts.append(running)
            running += step.total_ticks
        self.total_motif_ticks = running

    # --- Common methods ---
    def set_offset(self, degree, octave=0):
        self.degree_offset = degree
        self.octave_offset = octave

    def get_target_pitch(self, cursor_note):
        return self.theory.get_pitch_at_offset(cursor_note, self.degree_offset, self.octave_offset)

    def play_note(self, pitch):
        if pitch == self.last_played_note:
            return
        self.release_note()
        self.bus.emit("VOICE_NOTE_ON", voice_id=self.id, note=pitch, velocity=100, channel=self.channel)
        self.last_played_note = pitch

    def release_note(self):
        if self.last_played_note is not None:
            self.bus.emit("VOICE_NOTE_OFF", voice_id=self.id, note=self.last_played_note, channel=self.channel)
            self.last_played_note = None
        # Clear sustain state as well
        self.sustain_current_note = None
        self.sustain_target_note = None

    def panic(self):
        self.release_note()

    def reset_for_song_position(self):
        self.release_note()
        self.sustain_current_note = None
        self.sustain_target_note = None

    # --- Mode management ---
    def set_mode(self, mode):
        if mode not in ("ostinato", "sustain"):
            return
        if self.mode == mode:
            return

        if mode == "sustain":
            # Switching from ostinato to sustain
            # Keep the currently playing note (if any) as sustain current note
            if self.last_played_note is not None:
                self.sustain_current_note = self.last_played_note
                self.sustain_target_note = self.last_played_note
            else:
                self.sustain_current_note = None
                self.sustain_target_note = None
        else:
            # Switching from sustain to ostinato
            # Release any sustain note
            self.release_note()

        self.mode = mode

    def set_sustain_quantization(self, ticks):
        self.sustain_quant_ticks = max(1, ticks)

    # --- Ostinato logic (unchanged) ---
    def set_motif(self, motif):
        self.release_note()
        self.motif = motif
        self.compiled_motif = RhythmEngine.compile_motif(motif)
        self._update_cumulative()

    def _on_master_tick_ostinato(self, master_tick, cursor_note):
        if self.muted or not self.compiled_motif:
            return
        if self.total_motif_ticks == 0:
            return

        pattern_pos = master_tick % self.total_motif_ticks
        step_index = 0
        for i, start in enumerate(self.cumulative_starts):
            if pattern_pos >= start:
                step_index = i
            else:
                break
        step = self.compiled_motif[step_index]
        ticks_inside = pattern_pos - self.cumulative_starts[step_index]

        if ticks_inside == 0 and not step.is_rest:
            pitch = self.get_target_pitch(cursor_note)
            if 0 <= pitch <= 127:
                if pitch != self.last_played_note:
                    self.play_note(pitch)
            else:
                self.release_note()

        if not step.is_rest and ticks_inside == step.gate_ticks:
            self.release_note()

    # --- Sustain logic ---
    def on_cursor_moved_sustain(self, cursor_note):
        """Called when cursor moves. Stores target note for next grid tick."""
        pitch = self.get_target_pitch(cursor_note)
        if 0 <= pitch <= 127:
            self.sustain_target_note = pitch
        else:
            self.sustain_target_note = None

    def _on_master_tick_sustain(self, master_tick, cursor_note):
        """Called on each master tick; change note only on quantization boundaries."""
        if self.muted:
            return

        # If no current note and no target, set target from cursor
        if self.sustain_current_note is None and self.sustain_target_note is None:
            pitch = self.get_target_pitch(cursor_note)
            if 0 <= pitch <= 127:
                self.sustain_target_note = pitch
            else:
                return

        # Only act on grid ticks
        if master_tick % self.sustain_quant_ticks != 0:
            return

        if self.sustain_target_note is not None and self.sustain_target_note != self.sustain_current_note:
            # Release old note if any
            if self.sustain_current_note is not None:
                # Release the note (use release_note to emit off)
                # But release_note would clear last_played_note; we need to manage carefully.
                # Instead, directly emit note off for the current note.
                self.bus.emit("VOICE_NOTE_OFF", voice_id=self.id, note=self.sustain_current_note, channel=self.channel)
                self.last_played_note = None
            # Play new note
            self.bus.emit("VOICE_NOTE_ON", voice_id=self.id, note=self.sustain_target_note, velocity=100, channel=self.channel)
            self.sustain_current_note = self.sustain_target_note
            self.last_played_note = self.sustain_target_note

    # --- Main tick dispatch ---
    def on_master_tick(self, master_tick, cursor_note):
        if self.mode == "ostinato":
            self._on_master_tick_ostinato(master_tick, cursor_note)
        else:
            self._on_master_tick_sustain(master_tick, cursor_note)