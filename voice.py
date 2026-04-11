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
        self.motif_index = 0
        self.tick_counter = 0
        self.last_played_note = None
        self.muted = False

        

    def set_motif(self, motif):
        self.motif = motif
        self.compiled_motif = RhythmEngine.compile_motif(motif)
        self.motif_index = 0
        self.tick_counter = 0

    def set_offset(self, degree, octave=0):
        self.degree_offset = degree
        self.octave_offset = octave

    def get_target_pitch(self, cursor_note):
        return self.theory.get_pitch_at_offset(cursor_note, self.degree_offset, self.octave_offset)

    def on_clock_tick(self, cursor_note):
        if not self.ostinato_enabled or not self.compiled_motif or self.muted:
            return

        step = self.compiled_motif[self.motif_index]

        if self.tick_counter == 0 and not step.is_rest:
            pitch = self.get_target_pitch(cursor_note)
            # Clamp to MIDI range (silence if out)
            if 0 <= pitch <= 127:
                self.play_note(pitch)
            else:
                self.release_note()
                self.last_played_note = None

        self.tick_counter += 1

        if self.tick_counter == step.gate_ticks and not step.is_rest:
            self.release_note()

        if self.tick_counter >= step.total_ticks:
            self.tick_counter = 0
            self.motif_index = (self.motif_index + 1) % len(self.compiled_motif)

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