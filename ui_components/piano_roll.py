# ui_components/piano_roll.py
import pygame
from .piano_roll_state import PianoRollState

class PianoRoll:
    def __init__(self, parent):
        self.p = parent
        self.scroll_speed = 8.0
        self.box_color = parent.theme.secondary
        self.active_box_color = parent.theme.adjust_brightness("secondary", 1.5)
        self.white_width_scale = 0.8
        self.black_width_scale = 0.5

    def draw(self, surface, state: PianoRollState, rect: pygame.Rect):
        current_p = state.pulse_count
        white_w = 736 // 75
        start_x = (736 - (75 * white_w)) // 2

        for entry in state.history:
            start = entry.start_pulse
            end = entry.end_pulse if entry.end_pulse is not None else current_p

            y_bottom = rect.bottom - (current_p - start) * self.scroll_speed
            y_top = rect.bottom - (current_p - end) * self.scroll_speed

            if y_bottom < rect.top or y_top > rect.bottom:
                continue

            note = entry.note
            x_pos = start_x + self.get_x_pos(note, white_w)
            is_black = note % 12 in [1, 3, 6, 8, 10]

            width = int(white_w * (self.black_width_scale if is_black else self.white_width_scale))
            note_rect = pygame.Rect(x_pos, y_top, width, y_bottom - y_top)
            color = self.active_box_color if entry.end_pulse is None else self.box_color
            pygame.draw.rect(surface, color, note_rect, border_radius=2)

    def get_x_pos(self, midi, white_w):
        white_indices = [0, 2, 4, 5, 7, 9, 11]
        octave = midi // 12
        note_in_octave = midi % 12
        white_key_count = octave * 7
        for i in range(note_in_octave):
            if i in white_indices:
                white_key_count += 1
        x = white_key_count * white_w
        if note_in_octave in [1, 3, 6, 8, 10]:
            x -= (int(white_w * 0.8) // 2)
        return x