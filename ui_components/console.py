# ui_components/console.py
import pygame
from event_bus import bus

class Console:
    def __init__(self, parent):
        self.parent = parent
        self.font = parent.theme.fonts.get_mono_reg(12)
        self.bg_color = (0, 0, 0, 0)
        self.border_radius = 8
        self.padding_x = 15
        self.padding_y = 15
        self.line_spacing = 2
        self.max_lines = 8
        self.text_color = parent.theme.dark

        self.log_messages = []  # list of (text, color)

        bus.on("ADD_LOG", self._on_add_log)

    def _on_add_log(self, text, color):
        self.add_log(text, color)

    def add_log(self, text, color=None):
        if color is None:
            color = self.text_color
        # Store original (non-wrapped) message; wrapping happens at draw time.
        self.log_messages.insert(0, (text, color))
        # We'll trim later in draw based on wrapped line count.
        # But keep a reasonable cap to avoid unbounded growth.
        if len(self.log_messages) > self.max_lines * 3:
            self.log_messages.pop()

    def _wrap_text(self, text, max_width, font):
        """Wrap text to fit max_width (in pixels). Returns list of lines."""
        words = text.split(' ')
        lines = []
        current_line = []
        current_width = 0

        for word in words:
            word_surf = font.render(word, True, (0,0,0))
            word_width = word_surf.get_width()
            # Add space width if not first word
            space_width = font.render(' ', True, (0,0,0)).get_width()
            if current_line:
                test_width = current_width + space_width + word_width
            else:
                test_width = word_width

            if test_width <= max_width:
                if current_line:
                    current_line.append(word)
                    current_width += space_width + word_width
                else:
                    current_line = [word]
                    current_width = word_width
            else:
                # Finish current line
                if current_line:
                    lines.append(' '.join(current_line))
                # Start new line with this word
                current_line = [word]
                current_width = word_width
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def draw(self, surface, rect):
        # Draw background
        bg_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        bg_surf.fill(self.bg_color)
        pygame.draw.rect(bg_surf, self.bg_color, bg_surf.get_rect(), border_radius=self.border_radius)
        surface.blit(bg_surf, rect)

        # Calculate available width for text
        text_max_width = rect.width - 2 * self.padding_x
        if text_max_width <= 0:
            return

        # Build a list of all wrapped lines (with colors)
        wrapped_lines = []  # list of (line_text, color)
        for text, color in self.log_messages:
            lines = self._wrap_text(text, text_max_width, self.font)
            for line in lines:
                wrapped_lines.append((line, color))
                if len(wrapped_lines) >= self.max_lines:
                    break
            if len(wrapped_lines) >= self.max_lines:
                break

        # Draw lines from top (newest) to bottom
        text_x = rect.x + self.padding_x
        text_y = rect.y + self.padding_y
        line_height = self.font.get_height() + self.line_spacing

        for i, (line, color) in enumerate(wrapped_lines[:self.max_lines]):
            y = text_y + i * line_height
            if y + line_height > rect.bottom - self.padding_y:
                break
            text_surf = self.font.render(line, True, color)
            surface.blit(text_surf, (text_x, y))