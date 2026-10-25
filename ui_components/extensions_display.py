import pygame
from event_bus import bus

class ExtensionsDisplay:
    def __init__(self, parent):
        self.parent = parent
        self.font = parent.theme.fonts.get_mono_bold_italic(16)
        self.text_color = parent.theme.secondary
        self.bg_color = None
        self.padding_x = 50
        self.padding_y = -10
        self.extension_names = {6: "add7", 8: "add9", 10: "add11", 12: "add13"}
        self.omission_names = {2: "no3", 4: "no5"}

        # Listen to theory changes to update display
        bus.on("SCALE_CHANGED", self._on_scale_changed)
        self.current_text = ""

    def _on_scale_changed(self, legal_notes, root_note, mode):
        # This will be called when extensions/omissions change.
        # We'll update text on next draw.
        pass

    def draw(self, surface, rect, theory):
        parts = []
        for ext in sorted(theory.extensions):
            if ext in self.extension_names:
                parts.append(self.extension_names[ext])
        for omit in sorted(theory.omissions):
            if omit in self.omission_names:
                parts.append(self.omission_names[omit])
        if not parts:
            return
        text = ", ".join(parts)
        text_surf = self.font.render(text, True, self.text_color)
        text_rect = text_surf.get_rect()
        text_rect.left = rect.left + self.padding_x
        text_rect.top = rect.top + self.padding_y
        if self.bg_color:
            bg_rect = text_rect.inflate(self.padding_x * 2, self.padding_y * 2)
            pygame.draw.rect(surface, self.bg_color, bg_rect)
        surface.blit(text_surf, text_rect)