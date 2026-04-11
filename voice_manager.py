# voice_manager.py
from event_bus import bus

class VoiceManager:
    def __init__(self):
        self.voices = {}
        self.gate = False
        self.chord = False

        # Subscribe to voice events
        bus.on("VOICE_NOTE_ON", self._on_voice_note_on)
        bus.on("VOICE_NOTE_OFF", self._on_voice_note_off)

    def add_voice(self, voice):
        self.voices[voice.id] = voice

    def remove_voice(self, voice_id):
        if voice_id in self.voices:
            del self.voices[voice_id]

    def set_gate(self, state):
        self.gate = state

    def set_chord(self, state):
        self.chord = state

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

    def _on_voice_note_off(self, voice_id, note, channel):
        voice = self.voices.get(voice_id)
        if not voice:
            return
        if self._should_play_voice(voice):
            bus.emit("SEND_NOTE_OFF", note=note, channel=channel)