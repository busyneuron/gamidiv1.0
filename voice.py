# voice.py
from rhythm_engine import RhythmEngine

class Voice:
    def __init__(self, voice_id, event_bus, theory_engine, degree_offset=0, octave_offset=0, channel=0):
        self.id = voice_id
        self.bus = event_bus
        self.theory_engine = theory_engine
        self.degree_offset = degree_offset
        self.octave_offset = octave_offset
        self.channel = channel
        self.ostinato_enabled = True
        self.motif = [("quarter", "normal")]
        self.compiled_motif = RhythmEngine.compile_motif(self.motif)
        self.motif_index = 0
        self.tick_counter = 0
        self.current_note = self.get_target_pitch()  # may be None if out of range
        self.last_played_note = None
        self.muted = False

        self.bus.on("CLOCK_TICK", self.on_clock_tick)

    def set_motif(self, motif):
        self.motif = motif
        self.compiled_motif = RhythmEngine.compile_motif(motif)
        self.motif_index = 0
        self.tick_counter = 0

    def set_offset(self, degree, octave=0):
        self.degree_offset = degree
        self.octave_offset = octave

    def get_target_pitch(self):
        pitch = self.theory_engine.get_pitch_at_offset(self.degree_offset, self.octave_offset)
        if 0 <= pitch <= 127:
            return pitch
        return None

    def on_clock_tick(self):
        if not self.ostinato_enabled or not self.compiled_motif or self.muted:
            return

        step = self.compiled_motif[self.motif_index]

        # Start of a new step
        if self.tick_counter == 0 and not step.is_rest:
            # Recalculate pitch using current cursor position
            self.current_note = self.get_target_pitch()
            self.play_note()

        self.tick_counter += 1

        # Release note after gate_ticks
        if self.tick_counter == step.gate_ticks and not step.is_rest:
            self.release_note()

        # End of step
        if self.tick_counter >= step.total_ticks:
            self.tick_counter = 0
            self.motif_index = (self.motif_index + 1) % len(self.compiled_motif)

    def play_note(self):
        # If current_note is None (out of range), just ensure silence
        if self.current_note is None:
            self.release_note()
            return
        # Avoid retriggering the same note
        if self.current_note == self.last_played_note:
            return
        # Release any previous note
        self.release_note()
        # Play new note
        self.bus.emit("VOICE_NOTE_ON", voice_id=self.id, note=self.current_note,
                      velocity=100, channel=self.channel)
        self.last_played_note = self.current_note

    def release_note(self):
        if self.last_played_note is not None:
            self.bus.emit("VOICE_NOTE_OFF", voice_id=self.id,
                          note=self.last_played_note, channel=self.channel)
            self.last_played_note = None

    def panic(self):
        self.release_note()