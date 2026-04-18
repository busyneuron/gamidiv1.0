# voice_editor.py
from event_bus import bus
from rhythm_engine import RhythmEngine

class VoiceEditor:
    def __init__(self, voice_manager, theory_engine=None):
        self.vm = voice_manager
        self.theory = theory_engine
        self._selected_ids = set()
        # Listen to voice removal to clean selection
        bus.on("VOICE_REMOVED", self._on_voice_removed)

    def _on_voice_removed(self, voice_id):
        """Remove voice from selection if it was selected."""
        if voice_id in self._selected_ids:
            self._selected_ids.discard(voice_id)
            self._emit_selection()

    def _emit_selection(self):
        """Emit event with current selected voice IDs."""
        bus.emit("VOICE_SELECTION_CHANGED", selected_ids=self._selected_ids.copy())

    # --- Selection ---
    def select_voice(self, voice_id):
        """Select a single voice (clear previous selection)."""
        if voice_id in self.vm.voices:
            self._selected_ids = {voice_id}
        else:
            self._selected_ids.clear()
        self._emit_selection()

    def select_all_voices(self):
        """Select all existing voices."""
        self._selected_ids = set(self.vm.voices.keys())
        self._emit_selection()

    def clear_selection(self):
        """Deselect all voices."""
        self._selected_ids.clear()
        self._emit_selection()

    def get_selected_ids(self):
        """Return a copy of selected voice IDs."""
        return self._selected_ids.copy()

    # --- Voice removal ---
    def clear_selected_voices(self):
        """Remove all selected voices from VoiceManager."""
        for vid in list(self._selected_ids):
            if vid in self.vm.voices:
                self.vm.remove_voice(vid)
        # Selection cleared automatically via _on_voice_removed
        # If no voices left, create a default one
        if not self.vm.voices:
            self._create_default_voice()

    def clear_all_voices(self):
        """Remove all voices, then create a default voice."""
        for vid in list(self.vm.voices.keys()):
            self.vm.remove_voice(vid)
        self._selected_ids.clear()
        self._create_default_voice()
        self._emit_selection()

    def _create_default_voice(self):
        """Create a default voice (degree 0, quarter note) if none exist."""
        from voice import Voice
        default = Voice(voice_id=0, event_bus=bus, theory_engine=self.theory,
                        degree_offset=0, octave_offset=0, channel=0)
        default.set_motif([("quarter", "normal")])
        self.vm.add_voice(default)
        # Optionally select it
        self.select_voice(0)

    # --- Channel editing ---
    def change_selected_voice_channel(self, delta):
        """Add delta to channel of all selected voices (clamp 0-15)."""
        for vid in self._selected_ids:
            voice = self.vm.voices.get(vid)
            if voice:
                new_channel = max(0, min(15, voice.channel + delta))
                if new_channel != voice.channel:
                    voice.channel = new_channel
                    # Optionally emit event for UI update
                    bus.emit("VOICE_CHANNEL_CHANGED", voice_id=vid, channel=new_channel)

    # --- Motif presets ---
    # Define preset motifs (you can expand this)
    MOTIF_PRESETS = {
        "quarter": [("quarter", "normal")],
        "eighth": [("eighth", "normal")],
        "gallop": [
            ("eighth", "staccato"),
            ("sixteenth", "staccato"),
            ("sixteenth", "staccato")
        ],
        "syncopated": [
            ("eighth rest", ""),
            ("eighth", "staccato"),
            ("eighth rest", ""),
            ("eighth", "staccato"),
            ("quarter", "normal")
        ]
    }

    def set_selected_voice_motif(self, preset_name):
        """Apply a named motif preset to all selected voices."""
        motif = self.MOTIF_PRESETS.get(preset_name)
        if not motif:
            bus.emit("ADD_LOG", text=f"Unknown motif preset: {preset_name}", color=(255,100,100))
            return
        for vid in self._selected_ids:
            voice = self.vm.voices.get(vid)
            if voice:
                voice.set_motif(motif)
        bus.emit("ADD_LOG", text=f"Applied motif '{preset_name}' to {len(self._selected_ids)} voice(s)", color=(100,200,100))

        # --- Mode and quantization for selected voices ---
    def set_selected_voice_mode(self, mode):
        """Set mode ('ostinato' or 'sustain') for all selected voices."""
        if mode not in ("ostinato", "sustain"):
            return
        for vid in self._selected_ids:
            voice = self.vm.voices.get(vid)
            if voice:
                voice.set_mode(mode)
        bus.emit("ADD_LOG", text=f"Set mode '{mode}' for {len(self._selected_ids)} voice(s)", color=(100,200,200))

    def set_selected_voice_sustain_quantization(self, ticks):
        """Set sustain quantization (in ticks) for selected voices."""
        for vid in self._selected_ids:
            voice = self.vm.voices.get(vid)
            if voice:
                voice.set_sustain_quantization(ticks)
        bus.emit("ADD_LOG", text=f"Set sustain quantization to {ticks} ticks for {len(self._selected_ids)} voice(s)", color=(100,200,200))