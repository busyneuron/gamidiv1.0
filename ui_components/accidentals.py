# ui_components/accidentals.py
import pygame
from event_bus import bus

class AccidentalsDisplay:
    def __init__(self, parent):
        self.parent = parent
        self.font = parent.theme.fonts.get_mono_bold_italic(16)
        self.text_color = parent.theme.secondary
        self.padding_x = 5
        self.padding_y = 15
        self.line_spacing = 4
        self.degrees = ["I", "II", "III", "IV", "V", "VI", "VII"]

        # Current accidentals (degree_index -> shift)
        self.offsets = {}

        # Subscribe to event
        bus.on("ACCIDENTALS_CHANGED", self._on_accidentals_changed)

    def _on_accidentals_changed(self, accidentals: dict):
        """Update stored offsets when theory changes."""
        self.offsets = accidentals

    def draw(self, surface, rect):
        """Draw accidentals stacked vertically inside the given rect."""
        if not self.offsets:
            return

        # Sort by degree index (I to VII)
        items = sorted(self.offsets.items())  # (degree_index, shift)

        x = rect.x + self.padding_x
        y = rect.y + self.padding_y
        line_height = self.font.get_height() + self.line_spacing

        for idx, shift in items:
            if shift == 0:
                continue
            # Format label: e.g., "#IV" or "bII"
            symbol = "#" if shift > 0 else "b"
            label = f"{symbol * abs(shift)}{self.degrees[idx]}"
            text_surf = self.font.render(label, True, self.text_color)
            surface.blit(text_surf, (x, y))
            y += line_height

            # Stop if out of vertical space
            if y + line_height > rect.bottom - self.padding_y:
                break