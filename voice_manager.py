# voice_manager.py
from event_bus import bus

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
        bus.on("CLOCK_TICK", self._on_clock_tick)

    def add_voice(self, voice):
        self.voices[voice.id] = voice

    def remove_voice(self, voice_id):
        if voice_id in self.voices:
            del self.voices[voice_id]

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

    def _on_clock_tick(self):
        for voice in self.voices.values():
            voice.on_clock_tick(self.cursor_note)

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
            # Ensure voice releases any pending note
            voice.release_note()

    def _on_voice_note_off(self, voice_id, note, channel):
        voice = self.voices.get(voice_id)
        if not voice:
            return
        # Always send note-off
        bus.emit("SEND_NOTE_OFF", note=note, channel=channel)

    def panic(self):
        for voice in self.voices.values():
            voice.panic()
    
    def jump_cursor_to_voice(self, voice_id):
        voice = self.voices.get(voice_id)
        if not voice:
            return
        # Get the voice's current sounding note
        new_cursor = voice.last_played_note
        if new_cursor is None:
            new_cursor = voice.get_target_pitch(self.cursor_note)
        if new_cursor is None:
            return
        # For each voice, recompute offsets based on its current absolute note
        for v in self.voices.values():
            current_note = v.last_played_note
            if current_note is None:
                current_note = v.get_target_pitch(self.cursor_note)
            if current_note is None:
                continue
            deg_off, oct_off = self.theory.get_offset_between_notes(new_cursor, current_note)
            v.degree_offset = deg_off
            v.octave_offset = oct_off
        # Update cursor
        self.cursor_note = new_cursor
        bus.emit("CURSOR_MOVED", new_note=self.cursor_note)