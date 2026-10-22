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
        self.active_note_counts = {}   # note -> count of voices playing it

        bus.on("VOICE_NOTE_ON", self._on_voice_note_on)
        bus.on("VOICE_NOTE_OFF", self._on_voice_note_off)
        bus.on("CURSOR_MOVED", self._on_cursor_moved)
        bus.on("MASTER_TICK", self._on_master_tick)
        bus.on("SONG_POSITION", self._on_song_position)

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
            # Before removing, release any notes this voice is playing
            voice = self.voices[voice_id]
            if voice.last_played_note is not None:
                self._release_note(voice, voice.last_played_note, voice.channel)
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

    def _release_note(self, voice, note, channel):
        """Decrement counter for (note, channel) and send OFF if count reaches zero."""
        key = (note, channel)
        count = self.active_note_counts.get(key, 0)
        if count <= 0:
            return
        new_count = count - 1
        if new_count <= 0:
            self.active_note_counts.pop(key, None)
            bus.emit("SEND_NOTE_OFF", note=note, channel=channel)
        else:
            self.active_note_counts[key] = new_count

    def _play_note(self, voice, note, velocity, channel):
        """Increment counter for (note, channel) and send ON if count was zero."""
        key = (note, channel)
        count = self.active_note_counts.get(key, 0)
        if count == 0:
            bus.emit("SEND_NOTE_ON", note=note, velocity=velocity, channel=channel)
        self.active_note_counts[key] = count + 1

    def _on_cursor_moved(self, new_note):
        self.cursor_note = new_note
        for voice in self.voices.values():
            if voice.mode == "sustain":
                voice.on_cursor_moved_sustain(new_note)

    def _on_master_tick(self, tick, bar=0, tick_in_bar=0, **kwargs):
        for voice in self.voices.values():
            if voice.mode == "ostinato":
                voice.on_master_tick(tick, self.cursor_note)
            elif voice.mode == "sustain":
                if self.gate:
                    voice.on_master_tick(tick, self.cursor_note)
                else:
                    if voice.sustain_current_note is not None:
                        voice.release_note()

    def _on_song_position(self, pos):
        for voice in self.voices.values():
            voice.reset_for_song_position()
        self.active_note_counts.clear()   # also clear counter on jump

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
            self._play_note(voice, note, velocity, channel)
        else:
            # Voice is not allowed to play, so release it internally
            voice.release_note()

    def _on_voice_note_off(self, voice_id, note, channel):
        voice = self.voices.get(voice_id)
        if not voice:
            return
        self._release_note(voice, note, channel)

    def panic(self):
        for voice in self.voices.values():
            voice.panic()
        self.active_note_counts.clear()
        bus.emit("SEND_ALL_NOTES_OFF")   # optional, but good practice
    
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
        self.add_voice(new_voice)
        return new_voice

    # Helper methods for mode/quantization
    def set_voice_mode(self, voice_id, mode):
        voice = self.voices.get(voice_id)
        if voice:
            voice.set_mode(mode)

    def set_voice_sustain_quantization(self, voice_id, ticks):
        voice = self.voices.get(voice_id)
        if voice:
            voice.set_sustain_quantization(ticks)