# ui_components/keyboard.py
import pygame
import time
from .keyboard_state import KeyboardState

class Keyboard:
    def __init__(self, parent):
        self.p = parent
        
        # ==========================================
        # CONFIGURATION
        # ==========================================
        self.height_scale_white = 0.60
        self.height_scale_black = 0.38
        self.width_scale = 0.8
        self.outline_thickness = 1
        self.pulse_duration = 0.5  # seconds

        self.white_active_fill = (255, 255, 255)
        self.white_active_outline = (255, 255, 255)
        self.black_active_fill = (255, 255, 255)
        self.black_active_outline = (255, 255, 255)
        
        self.white_fill_legal = self.p.theme.bright 
        self.white_fill_illegal = self.p.theme.bright           
        self.black_fill_legal = self.p.theme.bright     
        self.black_fill_illegal = self.p.theme.dark   
        
        self.white_alpha_fill_active = 255
        self.white_alpha_fill_legal = 255
        self.white_alpha_fill_illegal = 100

        self.black_alpha_fill_active = 255
        self.black_alpha_fill_legal = 255
        self.black_alpha_fill_illegal = 100
        
        self.white_outline_legal = self.p.theme.dark 
        self.white_outline_illegal = (0, 180, 140)
        self.black_outline_legal = self.p.theme.dark 
        self.black_outline_illegal = (0, 180, 140)
        
        self.white_alpha_out_active = 255
        self.white_alpha_out_legal = 180
        self.white_alpha_out_illegal = 30

        self.black_alpha_out_active = 255
        self.black_alpha_out_legal = 180
        self.black_alpha_out_illegal = 30
        
        self.fade_duration = 0.30  # kept for future fade state
        
        # Jump reachable dimming
        self.white_fill_dim = (40, 100, 100)
        self.white_outline_dim = (40, 100, 100)
        self.black_fill_dim = (20, 30, 40)
        self.black_outline_dim = (20, 30, 40)
        self.dim_with_alpha = True
        self.jump_alpha_factor = 0.3
        
        # Key movement animation (disabled)
        self.key_move_enabled = False
        
        # Scrolling masks
        self.mask_enabled = True
        self.mask_scroll_speed = 0.2
        self.legal_mask_path = "assets/legal_mask.png"
        self.illegal_mask_path = "assets/illegal_mask.png"
        
        self.legal_mask = None
        self.illegal_mask = None
        self.mask_scroll_x = 0
        self._load_masks()
        
        self.cursor_dot_color = (0, 0, 0)       # black
        self.cursor_dot_radius = 4
        self.cursor_dot_offset = 8              # pixels above the key

    def _load_masks(self):
        if not self.mask_enabled:
            return
        white_w = 736 // 75
        kb_width = 75 * white_w
        kb_height = int(736 // 16 * 2 * self.height_scale_white)
        try:
            legal_tex = pygame.image.load(self.legal_mask_path).convert_alpha()
            illegal_tex = pygame.image.load(self.illegal_mask_path).convert_alpha()
            self.legal_mask = self._create_tiled_surface(legal_tex, kb_width, kb_height)
            self.illegal_mask = self._create_tiled_surface(illegal_tex, kb_width, kb_height)
        except Exception as e:
            print(f"Failed to load masks: {e}. Disabling.")
            self.mask_enabled = False
    
    def _create_tiled_surface(self, tex, width, height):
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        tex_w, tex_h = tex.get_size()
        for x in range(0, width, tex_w):
            for y in range(0, height, tex_h):
                surf.blit(tex, (x, y))
        return surf
    
    def draw(self, surface, state: KeyboardState, rect: pygame.Rect):
        now = time.time()
        white_w = 736 // 75
        white_h = int(rect.height * self.height_scale_white)
        black_w = int(white_w * 0.75)
        black_h = int(rect.height * self.height_scale_black)
        start_x = (736 - (75 * white_w)) // 2
        key_y = rect.top + (rect.height - white_h) // 2
        
        if self.mask_enabled and self.legal_mask:
            self.mask_scroll_x += self.mask_scroll_speed
            if self.mask_scroll_x >= self.legal_mask.get_width():
                self.mask_scroll_x -= self.legal_mask.get_width()
        
        # White keys
        for note in range(0, 128):
            if not self._is_black(note):
                self._draw_key(surface, note, start_x, key_y, white_w, white_h,
                               False, state, now)
        # Black keys
        for note in range(0, 128):
            if self._is_black(note):
                self._draw_key(surface, note, start_x, key_y, black_w, black_h,
                               True, state, now)
    
    def _draw_key(self, surface, note, start_x, y, logical_w, h, is_black, state, now):
        x = start_x + self.get_x_pos(note, 736 // 75)
        actual_w = max(2, int((736 // 75) * self.width_scale))
        offset_x = x + (logical_w - actual_w) // 2
        key_rect = pygame.Rect(offset_x, y, actual_w, h)
        radius = actual_w // 2
        
        is_legal = note in state.legal_notes
        is_active = note in state.active_notes
        root_pc = state.root_pc
        
        # Choose base fill/outline colors and alphas
        if is_black:
            if is_legal:
                base_fill = self.black_fill_legal
                alpha_fill = self.black_alpha_fill_legal
                base_outline = self.black_outline_legal
                alpha_out = self.black_alpha_out_legal
            else:
                base_fill = self.black_fill_illegal
                alpha_fill = self.black_alpha_fill_illegal
                base_outline = self.black_outline_illegal
                alpha_out = self.black_alpha_out_illegal
        else:
            if is_legal:
                base_fill = self.white_fill_legal
                alpha_fill = self.white_alpha_fill_legal
                base_outline = self.white_outline_legal
                alpha_out = self.white_alpha_out_legal
            else:
                base_fill = self.white_fill_illegal
                alpha_fill = self.white_alpha_fill_illegal
                base_outline = self.white_outline_illegal
                alpha_out = self.white_alpha_out_illegal
        
        # Apply jump dimming
        if state.reachable_notes is not None and is_legal and note not in state.reachable_notes:
            if self.dim_with_alpha:
                alpha_fill = int(alpha_fill * self.jump_alpha_factor)
                alpha_out = int(alpha_out * self.jump_alpha_factor)
            else:
                if is_black:
                    base_fill = self.black_fill_dim
                    base_outline = self.black_outline_dim
                else:
                    base_fill = self.white_fill_dim
                    base_outline = self.white_outline_dim
        
        fill_color = (*base_fill, alpha_fill)
        outline_color = (*base_outline, alpha_out)
        
        # Override for active notes (full bright)
        if is_active:
            if is_black:
                fill_color = (*self.black_active_fill, self.black_alpha_fill_active)
                outline_color = (*self.black_active_outline, self.black_alpha_out_active)
            else:
                fill_color = (*self.white_active_fill, self.white_alpha_fill_active)
                outline_color = (*self.white_active_outline, self.white_alpha_out_active)
        
        # Pulse effect (from last trigger time)
        if note in state.last_trigger_time:
            elapsed = now - state.last_trigger_time[note]
            if elapsed < self.pulse_duration:
                t = elapsed / self.pulse_duration
                # Fade from white (255,255,255,255) to fill_color
                white_color = (255, 255, 255, 255)
                fill_color = self._lerp_color(white_color, fill_color, t)
        
        # Draw base key
        if fill_color[3] > 0:
            pygame.draw.rect(surface, fill_color, key_rect, border_radius=radius)
        
        # Overlay mask
        if self.mask_enabled and self.legal_mask:
            mask_surf = self.legal_mask if is_legal else self.illegal_mask
            src_x = (key_rect.x + self.mask_scroll_x) % mask_surf.get_width()
            src_rect = pygame.Rect(src_x, 0, key_rect.width, key_rect.height)
            surface.blit(mask_surf, key_rect, src_rect, special_flags=pygame.BLEND_RGBA_MULT)
        
        # Draw outline
        if self.outline_thickness > 0 and outline_color[3] > 0:
            pygame.draw.rect(surface, outline_color, key_rect, width=self.outline_thickness, border_radius=radius)
        
        # Root dot
        if note % 12 == root_pc:
            dot_y = y + h + 8
            dot_alpha = 255 if is_legal else 50
            base_dot_rgb = self.p.theme.accent[:3]
            dot_col = (255, 255, 255, dot_alpha) if is_active else (*base_dot_rgb, dot_alpha)
            pygame.draw.circle(surface, dot_col, (offset_x + actual_w // 2, int(dot_y)), 2)
        
        # Cursor dot (above the key)
        if note == state.current_note:
            dot_x = offset_x + actual_w // 2
            dot_y = key_rect.top - self.cursor_dot_offset
            pygame.draw.circle(surface, self.cursor_dot_color, (dot_x, dot_y), self.cursor_dot_radius)
    
    def _is_black(self, midi_note):
        return midi_note % 12 in [1, 3, 6, 8, 10]
    
    def get_x_pos(self, midi, white_w):
        white_indices = [0, 2, 4, 5, 7, 9, 11]
        octave = midi // 12
        note_in_octave = midi % 12
        white_key_count = (octave * 7)
        for i in range(note_in_octave):
            if i in white_indices:
                white_key_count += 1
        x = white_key_count * white_w
        if self._is_black(midi):
            x -= (int(white_w * 0.7) // 2)
        return x
    
    def _lerp_color(self, c1, c2, t):
        """Linear interpolate between two RGBA colors."""
        # Ensure both have 4 components
        c1 = c1 if len(c1) == 4 else (*c1, 255)
        c2 = c2 if len(c2) == 4 else (*c2, 255)
        return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))