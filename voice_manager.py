# voice_manager.py
from event_bus import bus
from voice import Voice

class VoiceManager:
    def __init__(self, theory_engine=None):
        self.voices = {}
        self.gate = False
        self.chord = False
        self.cursor_note = 60
        self.theory = theory_engine

        bus.on("VOICE_NOTE_ON", self._on_voice_note_on)
        bus.on("VOICE_NOTE_OFF", self._on_voice_note_off)
        bus.on("CURSOR_MOVED", self._on_cursor_moved)
        bus.on("MASTER_TICK", self._on_master_tick)  

        self.create_initial_voice(self.theory)

    def create_initial_voice(self, theory):
        voice = Voice(voice_id=0, event_bus=bus, theory_engine=theory,
                    degree_offset=0, octave_offset=0, channel=0)
        voice.set_motif([("quarter", "staccato"),("eighth", "normal"),("eighth", "normal")])
        self.add_voice(voice)

    def add_voice(self, voice):
        self.voices[voice.id] = voice
        bus.emit("VOICE_ADDED", voice_id=voice.id)

    def remove_voice(self, voice_id):
        if voice_id in self.voices:
            del self.voices[voice_id]
            bus.emit("VOICE_REMOVED", voice_id=voice_id)

    def set_gate(self, state):
        if self.gate and not state:
            self.release_all_voices()
        self.gate = state

    def set_chord(self, state):
        if self.chord and not state:
            for voice in self.voices.values():
                if voice.degree_offset != 0:
                    voice.release_note()
        self.chord = state

    def release_all_voices(self):
        for voice in self.voices.values():
            voice.release_note()

    def _on_cursor_moved(self, new_note):
        self.cursor_note = new_note

    def _on_master_tick(self, tick):
        """Called on every master tick with the global tick count."""
        for voice in self.voices.values():
            voice.on_master_tick(tick, self.cursor_note)

    def _should_play_voice(self, voice):
        if not self.gate:
            return False
        if not self.chord and voice.degree_offset != 0:
            return False
        return True

    def _on_voice_note_on(self, voice_id, note, velocity, channel):
        voice = self.voices.get(voice_id)
        if not voice:
            return
        if self._should_play_voice(voice):
            bus.emit("SEND_NOTE_ON", note=note, velocity=velocity, channel=channel)
        else:
            voice.release_note()

    def _on_voice_note_off(self, voice_id, note, channel):
        voice = self.voices.get(voice_id)
        if not voice:
            return
        bus.emit("SEND_NOTE_OFF", note=note, channel=channel)

    def panic(self):
        for voice in self.voices.values():
            voice.panic()
    
    def jump_cursor_to_voice(self, voice_id):
        voice = self.voices.get(voice_id)
        if not voice:
            return
        new_cursor = voice.last_played_note
        if new_cursor is None:
            new_cursor = voice.get_target_pitch(self.cursor_note)
        if new_cursor is None:
            return
        for v in self.voices.values():
            current_note = v.last_played_note
            if current_note is None:
                current_note = v.get_target_pitch(self.cursor_note)
            if current_note is None:
                continue
            deg_off, oct_off = self.theory.get_offset_between_notes(new_cursor, current_note)
            v.degree_offset = deg_off
            v.octave_offset = oct_off
        self.cursor_note = new_cursor
        bus.emit("CURSOR_MOVED", new_note=self.cursor_note)

    def _find_unique_offset(self, base_offset):
        current = base_offset
        max_iter = 10
        existing = {v.degree_offset for v in self.voices.values()}
        for _ in range(max_iter):
            if current not in existing:
                return current
            current += base_offset
        return None

    def stack_new_voice(self, base_degree_offset):
        offset = self._find_unique_offset(base_degree_offset)
        if offset is None:
            return None
        new_id = max(self.voices.keys(), default=-1) + 1
        new_voice = Voice(
            voice_id=new_id,
            event_bus=bus,
            theory_engine=self.theory,
            degree_offset=offset,
            octave_offset=0,
            channel=0
        )
        new_voice.set_motif([("quarter", "normal")])
        self.voices[new_id] = new_voice
        return new_voice