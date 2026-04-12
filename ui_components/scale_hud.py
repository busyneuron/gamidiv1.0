# ui_components/scale_hud.py
import pygame

class ScaleHUD:
    def __init__(self, parent):
        self.parent = parent
        self.font = parent.theme.fonts.get_black_italic(140)
        self.mode_map = {
            "Ionian": "ion",
            "Dorian": "dor",
            "Phrygian": "phr",
            "Lydian": "lyd",
            "Mixolydian": "mix",
            "Aeolian": "aeol",
            "Minor": "min",
            "Major": "maj",
            "Locrian": "loc",
        }
        self.notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    def draw(self, surface, state, rect):
        # Get tonic letter (without octave)
        tonic = self.notes[state.root_note % 12]
        mode_short = self.mode_map.get(state.mode, state.mode[:3].upper())
        if state.pentatonic_active:
            text = f"{tonic}{mode_short}.p"
        else:
            text = f"{tonic}{mode_short}"

        text_surf = self.font.render(text, True, self.parent.theme.accent)
        text_rect = text_surf.get_rect(midleft=(rect.left + 10, rect.centery))
        surface.blit(text_surf, text_rect)