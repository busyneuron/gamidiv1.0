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
        self.ostinato_enabled = True
        self.motif = [("quarter", "normal")]
        self.compiled_motif = RhythmEngine.compile_motif(self.motif)
        self._update_cumulative()      # pre‑compute cumulative starts & total ticks
        self.last_played_note = None
        self.muted = False

    def _update_cumulative(self):
        """Pre‑compute cumulative start ticks for each step and total motif length."""
        self.cumulative_starts = []
        running = 0
        for step in self.compiled_motif:
            self.cumulative_starts.append(running)
            running += step.total_ticks
        self.total_motif_ticks = running

    def set_motif(self, motif):
        self.release_note()            # stop any currently sounding note
        self.motif = motif
        self.compiled_motif = RhythmEngine.compile_motif(motif)
        self._update_cumulative()
        # last_played_note is already None after release_note()

    def set_offset(self, degree, octave=0):
        self.degree_offset = degree
        self.octave_offset = octave

    def get_target_pitch(self, cursor_note):
        return self.theory.get_pitch_at_offset(cursor_note, self.degree_offset, self.octave_offset)

    def on_master_tick(self, master_tick, cursor_note):
        """Called on every master clock tick with the global tick count."""
        if not self.ostinato_enabled or self.muted or not self.compiled_motif:
            return
        if self.total_motif_ticks == 0:
            return

        pattern_pos = master_tick % self.total_motif_ticks

        # Find active step using binary search (linear scan is fine for small motifs)
        step_index = 0
        for i, start in enumerate(self.cumulative_starts):
            if pattern_pos >= start:
                step_index = i
            else:
                break

        step = self.compiled_motif[step_index]
        ticks_inside = pattern_pos - self.cumulative_starts[step_index]

        # Note on at the beginning of a non‑rest step
        if ticks_inside == 0 and not step.is_rest:
            pitch = self.get_target_pitch(cursor_note)
            if 0 <= pitch <= 127:
                if pitch != self.last_played_note:
                    self.play_note(pitch)
            else:
                self.release_note()

        # Note off when we reach the gate length (but only if we are still inside the same step)
        if not step.is_rest and ticks_inside == step.gate_ticks:
            self.release_note()

        # Optional: if we are past the gate and still inside the step, do nothing (note already off)

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

    def panic(self):
        self.release_note()