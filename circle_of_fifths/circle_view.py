# circle_of_fifths/circle_view.py
import math
import pygame
from .circle_controller import CircleController, MAJOR_NOTES, MAJOR_PITCHES, MINOR_NAMES, MINOR_PITCHES

class CircleView:
    def __init__(self, parent, controller: CircleController):
        self.parent = parent  # GamidiInterface, for fonts and theme
        self.controller = controller
        self.theory = controller.get_theory()

        # Cache for tinted circle surfaces (color, radius) -> surface
        self.circle_cache = {}
        # Load white circle PNG (same as old)
        self.white_circle = None
        try:
            self.white_circle = pygame.image.load("assets/circle.png").convert_alpha()
        except Exception as e:
            print(f"Warning: assets/circle.png not found. Falling back to pygame.draw.circle. {e}")

        # Animation state for radii
        self.current_radius = {}   # key = (ring, idx) -> current radius
        self.target_radius = {}    # key = (ring, idx) -> target radius
        self.anim_start_time = {}  # key = (ring, idx) -> start tick

        # Animation settings (same as old)
        self.animation_duration = 150      # milliseconds
        self.easing = "ease_out"           # "linear", "ease_out", "ease_in_out"

        # Radii for focused state (scaled)
        self.scale_factor = 1.2
        self.radius_tonic = 14 * self.scale_factor
        self.radius_triad = 11 * self.scale_factor
        self.radius_diatonic = 10 * self.scale_factor
        self.radius_other = 6 * self.scale_factor
        self.radius_hover_major = 12 * self.scale_factor
        self.radius_hover_minor = 10 * self.scale_factor

        # Radii for dimmed state
        self.dim_radius_tonic = 12
        self.dim_radius_triad = 10
        self.dim_radius_diatonic = 9
        self.dim_radius_other = 6

        # Pulse base radii
        self.pulse_base_radius_major = 12
        self.pulse_base_radius_minor = 10
        self.PULSE_MAX_SCALE = 1.5

        # Colors will be set by apply_theme()
        self._init_default_colors()

    def _init_default_colors(self):
        """Fallback colors (will be overridden by theme)."""
        # Major focused
        self.major_focused_tonic = (255, 80, 80)
        self.major_focused_triad = (255, 165, 0)
        self.major_focused_diatonic = (0, 200, 200)
        self.major_focused_other = (100, 100, 100)
        self.major_focused_text = (255, 255, 255)
        self.major_focused_hover_color = (255, 255, 255)
        self.major_focused_hover_text = (0, 0, 0)

        # Major dimmed
        self.major_dim_tonic = (180, 80, 80)
        self.major_dim_triad = (139, 0, 0)
        self.major_dim_diatonic = (80, 180, 180)
        self.major_dim_other = (60, 60, 60)
        self.major_dim_text = (200, 200, 200)

        # Minor focused
        self.minor_focused_tonic = (255, 80, 80)
        self.minor_focused_triad = (128, 0, 128)
        self.minor_focused_diatonic = (0, 200, 200)
        self.minor_focused_other = (100, 100, 100)
        self.minor_focused_text = (255, 255, 255)
        self.minor_focused_hover_color = (255, 255, 255)
        self.minor_focused_hover_text = (0, 0, 0)

        # Minor dimmed
        self.minor_dim_tonic = (180, 80, 80)
        self.minor_dim_triad = (6, 64, 43)
        self.minor_dim_diatonic = (80, 180, 180)
        self.minor_dim_other = (60, 60, 60)
        self.minor_dim_text = (200, 200, 200)

    def apply_theme(self, theme):
        """Set colors from a Theme object (called from interface)."""
        # Major focused
        self.major_focused_tonic = theme.accent
        self.major_focused_triad = theme.color2
        self.major_focused_diatonic = theme.bright
        self.major_focused_other = theme.neutral
        self.major_focused_text = (255, 255, 255)
        self.major_focused_hover_color = (255, 255, 255)
        self.major_focused_hover_text = (0, 0, 0)

        # Major dimmed (60% brightness)
        self.major_dim_tonic = tuple(int(c * 0.6) for c in theme.accent)
        self.major_dim_triad = tuple(int(c * 0.6) for c in theme.color2)
        self.major_dim_diatonic = tuple(int(c * 0.6) for c in theme.bright)
        self.major_dim_other = tuple(int(c * 0.6) for c in theme.neutral)
        self.major_dim_text = (200, 200, 200)

        # Minor focused
        self.minor_focused_tonic = theme.complementary
        self.minor_focused_triad = theme.color3
        self.minor_focused_diatonic = theme.bright
        self.minor_focused_other = theme.neutral
        self.minor_focused_text = (255, 255, 255)
        self.minor_focused_hover_color = (255, 255, 255)
        self.minor_focused_hover_text = (0, 0, 0)

        # Minor dimmed
        self.minor_dim_tonic = tuple(int(c * 0.6) for c in theme.complementary)
        self.minor_dim_triad = tuple(int(c * 0.6) for c in theme.color3)
        self.minor_dim_diatonic = tuple(int(c * 0.6) for c in theme.bright)
        self.minor_dim_other = tuple(int(c * 0.6) for c in theme.neutral)
        self.minor_dim_text = (200, 200, 200)

    # ------------------------------------------------------------------
    # Circle surface caching
    # ------------------------------------------------------------------
    def _get_circle_surface(self, color, radius):
        """Return a cached surface of a circle with given color and radius."""
        radius = max(1, int(radius))
        key = (color, radius)
        if key in self.circle_cache:
            return self.circle_cache[key]
        if self.white_circle is not None:
            scaled = pygame.transform.smoothscale(self.white_circle, (radius*2, radius*2))
            tinted = scaled.copy()
            tinted.fill(color, special_flags=pygame.BLEND_RGB_MULT)
            self.circle_cache[key] = tinted
            return tinted
        else:
            surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (radius, radius), radius)
            self.circle_cache[key] = surf
            return surf

    # ------------------------------------------------------------------
    # Animation helpers
    # ------------------------------------------------------------------
    def _update_radius_animation(self, ring, idx, target_radius, now):
        key = (ring, idx)
        if key not in self.current_radius:
            self.current_radius[key] = target_radius
            self.target_radius[key] = target_radius
            return target_radius
        if self.target_radius.get(key) != target_radius:
            self.target_radius[key] = target_radius
            self.anim_start_time[key] = now
            return self.current_radius[key]
        if key in self.anim_start_time:
            elapsed = now - self.anim_start_time[key]
            if elapsed >= self.animation_duration:
                self.current_radius[key] = target_radius
                del self.anim_start_time[key]
                return target_radius
            else:
                t = elapsed / self.animation_duration
                if self.easing == "ease_out":
                    t = 1 - (1 - t)**2
                elif self.easing == "ease_in_out":
                    t = 0.5 - 0.5 * math.cos(math.pi * t)
                start_rad = self.current_radius[key]
                new_rad = start_rad + (target_radius - start_rad) * t
                self.current_radius[key] = new_rad
                return new_rad
        else:
            return self.current_radius.get(key, target_radius)

    # ------------------------------------------------------------------
    # Style getters
    # ------------------------------------------------------------------
    def _get_major_gate_style(self, is_focused, is_tonic, has_triad, is_diatonic):
        if not is_focused:
            if is_tonic:
                return self.major_dim_tonic, self.dim_radius_tonic, self.major_dim_text
            elif has_triad:
                return self.major_dim_triad, self.dim_radius_triad, self.major_dim_text
            elif is_diatonic:
                return self.major_dim_diatonic, self.dim_radius_diatonic, self.major_dim_text
            else:
                return self.major_dim_other, self.dim_radius_other, self.major_dim_text
        else:
            if is_tonic:
                return self.major_focused_tonic, self.radius_tonic, self.major_focused_text
            elif has_triad:
                return self.major_focused_triad, self.radius_triad, self.major_focused_text
            elif is_diatonic:
                return self.major_focused_diatonic, self.radius_diatonic, self.major_focused_text
            else:
                return self.major_focused_other, self.radius_other, self.major_focused_text

    def _get_minor_gate_style(self, is_focused, is_tonic, has_triad, is_diatonic):
        if not is_focused:
            if is_tonic:
                return self.minor_dim_tonic, self.dim_radius_tonic, self.minor_dim_text
            elif has_triad:
                return self.minor_dim_triad, self.dim_radius_triad, self.minor_dim_text
            elif is_diatonic:
                return self.minor_dim_diatonic, self.dim_radius_diatonic, self.minor_dim_text
            else:
                return self.minor_dim_other, self.dim_radius_other, self.minor_dim_text
        else:
            if is_tonic:
                return self.minor_focused_tonic, self.radius_tonic, self.minor_focused_text
            elif has_triad:
                return self.minor_focused_triad, self.radius_triad, self.minor_focused_text
            elif is_diatonic:
                return self.minor_focused_diatonic, self.radius_diatonic, self.minor_focused_text
            else:
                return self.minor_focused_other, self.radius_other, self.minor_focused_text

    # ------------------------------------------------------------------
    # Draw rings
    # ------------------------------------------------------------------
    def _draw_ring(self, surface, cx, cy, ring_radius, is_focused, is_major):
        """Draw one complete ring (major or minor)."""
        state = self.controller.get_state()
        root_note = self.theory.root_note
        root_pc = root_note % 12
        current_mode = self.theory.mode
        scale_intervals = self.theory.effective_intervals  # list of 7 ints

        # Precompute triad qualities for each scale degree (0-6)
        triad_quality = []
        for d in range(7):
            root_int = scale_intervals[d]
            third_int = scale_intervals[(d + 2) % 7]
            fifth_int = scale_intervals[(d + 4) % 7]
            third_dist = (third_int - root_int) % 12
            fifth_dist = (fifth_int - root_int) % 12
            if third_dist == 4 and fifth_dist == 7:
                quality = "major"
            elif third_dist == 3 and fifth_dist == 7:
                quality = "minor"
            elif third_dist == 3 and fifth_dist == 6:
                quality = "diminished"
            else:
                quality = "other"
            triad_quality.append(quality)

        # Map pitch class to degree index (0-6)
        pc_to_degree = {}
        for d, interval in enumerate(scale_intervals):
            note_pc = (root_pc + interval) % 12
            pc_to_degree[note_pc] = d

        now = pygame.time.get_ticks()
        ring_key = "major" if is_major else "minor"

        for i in range(12):
            angle = math.radians(i * 30 - 90)
            if is_major:
                pc = MAJOR_PITCHES[i]
                name = MAJOR_NOTES[i]
                is_tonic = (current_mode not in ["Minor", "Aeolian"] and pc == root_pc)
                is_diatonic = pc in pc_to_degree
                has_triad = False
                if is_diatonic:
                    deg = pc_to_degree[pc]
                    if triad_quality[deg] == "major":
                        has_triad = True
                color, target_radius, text_color = self._get_major_gate_style(
                    is_focused, is_tonic, has_triad, is_diatonic)
            else:
                pc = MINOR_PITCHES[i]
                name = MINOR_NAMES[i]
                is_tonic = (current_mode in ["Minor", "Aeolian"] and pc == root_pc)
                is_diatonic = pc in pc_to_degree
                has_triad = False
                if is_diatonic:
                    deg = pc_to_degree[pc]
                    if triad_quality[deg] == "minor":
                        has_triad = True
                color, target_radius, text_color = self._get_minor_gate_style(
                    is_focused, is_tonic, has_triad, is_diatonic)

            # Degree mode: override name and style for diatonic gates that match chord quality
            if state.degree_mode and is_diatonic:
                # Determine if this gate should show a numeral based on ring and chord quality
                should_show_numeral = False
                if is_major:
                    # Outer ring: only show numerals for major chords (I, IV, V)
                    if has_triad:  # has_triad here means major triad
                        should_show_numeral = True
                else:
                    # Inner ring: only show numerals for minor chords (i, iv, v)
                    if has_triad:  # has_triad here means minor triad
                        should_show_numeral = True
                
                if should_show_numeral:
                    # Replace note name with roman numeral
                    name = self.controller._get_roman_numeral(i, is_major)
                    
                    # Override style for selected degree
                    if state.selected_degree_index == i:
                        if is_major:
                            color = self.major_focused_tonic
                            target_radius = self.radius_tonic
                            text_color = self.major_focused_text
                        else:
                            color = self.minor_focused_tonic
                            target_radius = self.radius_tonic
                            text_color = self.minor_focused_text
                # else: keep original note name and "other" style (already set)

            # Hover override (this takes precedence over selected degree)
            if is_focused and state.hovered_index == i and state.active_ring == ring_key:
                if is_major:
                    color = self.major_focused_hover_color
                    target_radius = self.radius_hover_major
                    text_color = self.major_focused_hover_text
                else:
                    color = self.minor_focused_hover_color
                    target_radius = self.radius_hover_minor
                    text_color = self.minor_focused_hover_text

            # Animated radius
            animated_radius = self._update_radius_animation(ring_key, i, target_radius, now)

            # Get circle surface
            circle_surf = self._get_circle_surface(color, int(animated_radius))

            # Position
            x = cx + math.cos(angle) * ring_radius
            y = cy + math.sin(angle) * ring_radius
            rect = circle_surf.get_rect(center=(int(x), int(y)))
            surface.blit(circle_surf, rect)

            # Draw text
            text_surf = self.parent.font_status.render(name, True, text_color)
            text_rect = text_surf.get_rect(center=(int(x), int(y)))
            surface.blit(text_surf, text_rect)

    # ------------------------------------------------------------------
    # Pulse effect
    # ------------------------------------------------------------------
    def _draw_pulse_effect(self, surface, cx, cy, outer_radius, inner_radius):
        state = self.controller.get_state()
        if state.pulse is None:
            return
        now = pygame.time.get_ticks()
        elapsed = now - state.pulse.timestamp_ms
        if elapsed >= state.PULSE_DURATION_MS:
            # Clear pulse
            self.controller.state.pulse = None
            return

        pulse_factor = 1.0 - (elapsed / state.PULSE_DURATION_MS)
        pc = state.pulse.pitch_class
        # Determine which ring contains this pc and get index and base radius
        if pc in MAJOR_PITCHES:
            idx = MAJOR_PITCHES.index(pc)
            ring_radius = outer_radius
            base_radius = self.pulse_base_radius_major
        elif pc in MINOR_PITCHES:
            idx = MINOR_PITCHES.index(pc)
            ring_radius = inner_radius
            base_radius = self.pulse_base_radius_minor
        else:
            return

        angle = math.radians(idx * 30 - 90)
        base_x = cx + math.cos(angle) * ring_radius
        base_y = cy + math.sin(angle) * ring_radius
        pulse_radius = base_radius * (1 + pulse_factor * (self.PULSE_MAX_SCALE - 1))
        alpha = int(255 * pulse_factor)

        if self.white_circle is not None:
            pulse_surf = self._get_circle_surface((255, 255, 255), int(pulse_radius))
            pulse_surf.set_alpha(alpha)
            rect = pulse_surf.get_rect(center=(int(base_x), int(base_y)))
            surface.blit(pulse_surf, rect)
        else:
            # Fallback: draw an outlined circle
            ring_surf = pygame.Surface((int(pulse_radius*2), int(pulse_radius*2)), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (255, 255, 255, alpha),
                               (int(pulse_radius), int(pulse_radius)), int(pulse_radius), 2)
            surface.blit(ring_surf, (int(base_x - pulse_radius), int(base_y - pulse_radius)))

    # ------------------------------------------------------------------
    # Main draw
    # ------------------------------------------------------------------
    def draw(self, surface, rect):
        """Draw the circle centered inside the given rect."""
        cx = rect.centerx
        cy = rect.centery
        max_radius = min(rect.width, rect.height) // 2 - 10
        outer_radius = max_radius * 0.8
        inner_radius = max_radius * 0.5
        # Focused state: currently we consider circle always focused if it's active? 
        # For dimming, we might check if another widget has focus.
        # Simpler: always draw as focused (as in old code). 
        # If you want dimming when circle is not the active focus, pass a flag.
        is_focused = True  # or check focus manager state
        self._draw_ring(surface, cx, cy, outer_radius, is_focused, is_major=True)
        self._draw_ring(surface, cx, cy, inner_radius, is_focused, is_major=False)
        self._draw_pulse_effect(surface, cx, cy, outer_radius, inner_radius)
        # Center dot (simple pygame draw)
        center_dot_color = (120, 120, 140)
        center_dot_radius = 8
        pygame.draw.circle(surface, center_dot_color, (cx, cy), center_dot_radius, 1)