# circle_of_fifths/base_circle.py
import math
import os
from turtle import mode
import pygame
from abc import ABC, abstractmethod
from event_bus import bus
from theory_engine import TheoryEngine

# Constants for pitch classes and note names (shared)
MAJOR_NOTES = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
MAJOR_PITCHES = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5]
MINOR_NAMES = ["a", "e", "b", "f#", "db", "ab", "eb", "bb", "f", "c", "g", "d"]
MINOR_PITCHES = [(p - 3) % 12 for p in MAJOR_PITCHES]

class BaseCircle(ABC):
    def __init__(self, parent, theory_engine: TheoryEngine):
        self.parent = parent          # GamidiInterface (for fonts, theme)
        self.theory = theory_engine
        self.focus_active = False   # set by FOCUS_CHANGED event
        self.mode_active = False    # set by interface toggling
        self.active_ring = "major"    # "major" or "minor"
        self.hovered_index = None
        self.exit_timer = 0
        self.selected_index = None    # index of selected gate (0-11)
        self.selected_roman = None   # store roman numeral for center text
        self.selected_ring = None 

        # Chord qualities from theory
        self.chord_qualities = self.theory.get_chord_qualities()

        # PNG cache
        self.circle_cache = {}
        self.white_circle = None
        try:
            self.white_circle = pygame.image.load("assets/circle.png").convert_alpha()
        except Exception as e:
            print(f"Warning: assets/circle.png not found. {e}")


        self._load_selected_animation_frames(folder="assets/circle_degree_selected_animation")

        # Animation state
        self.current_radius = {}
        self.target_radius = {}
        self.anim_start_time = {}
        self.animation_duration = 150
        self.easing = "ease_out"

        # Radii for focused state
        self.scale_factor = 1.4
        self.radius_tonic = 14 * self.scale_factor
        self.radius_triad = 11 * self.scale_factor
        self.radius_diatonic = 10 * self.scale_factor
        self.radius_other = 7 * self.scale_factor
        self.radius_hover_major = 14 * self.scale_factor
        self.radius_hover_minor = 10 * self.scale_factor

        # Radii for dimmed state
        self.dim_radius_tonic = 12
        self.dim_radius_triad = 10
        self.dim_radius_diatonic = 9
        self.dim_radius_other = 6

        # Center text config (optional, can be overridden)
        self.center_text_font = parent.theme.fonts.get_regular(50)
        self.center_text_color = parent.theme.dark
        self.center_text_offset_x = 0
        self.center_text_offset_y = 0

        # Entry animation for mode switching
        self.entry_anim_active = False
        self.entry_anim_start_time = 0
        self.entry_anim_duration = 800  # milliseconds
        self.entry_anim_wave_speed = 4.0  # cycles around the circle

        self.outer_radius_ratio = 0.85  
        self.inner_radius_ratio = 0.5 

        # Selected gate animation
        self.selected_anim_frames = []          # list of pygame.Surface
        self.selected_anim_frame_index = 0
        self.selected_anim_last_update = 0
        self.selected_anim_frame_delay = 100    # milliseconds per frame
        self.selected_anim_playing = False

        # Colors (will be set by apply_theme)
        self._init_default_colors()

        # Subscribe to events
        bus.on("RIGHT_STICK_UPDATED", self._on_stick_updated)
        bus.on("FOCUS_CHANGED", self._on_focus_changed)
        bus.on("CHORD_QUALITIES_CHANGED", self._on_chord_qualities_changed)
        bus.on("TOGGLE_CIRCLE_RING", self._on_toggle_ring)


    def _update_selected_animation(self):
        if not self.selected_anim_playing or not self.selected_anim_frames:
            return
        now = pygame.time.get_ticks()
        if now - self.selected_anim_last_update >= self.selected_anim_frame_delay:
            self.selected_anim_frame_index = (self.selected_anim_frame_index + 1) % len(self.selected_anim_frames)
            self.selected_anim_last_update = now

    def _load_selected_animation_frames(self, folder="assets/circle_degree_selected_animation"):
        import re
        print(f"Looking for frames in: {os.path.abspath(folder)}")
        frames = []
        # Gather all matching files
        pattern = re.compile(r'circle_degree_selected_(\d+)\.png')
        files = []
        for f in os.listdir(folder):
            match = pattern.match(f)
            if match:
                num = int(match.group(1))
                files.append((num, os.path.join(folder, f)))
        # Sort by number
        files.sort(key=lambda x: x[0])
        for num, path in files:
            try:
                img = pygame.image.load(path).convert_alpha()
                frames.append(img)
                print(f"Loaded: {path}")
            except Exception as e:
                print(f"Failed to load {path}: {e}")
        if frames:
            self.selected_anim_frames = frames
            self.selected_anim_playing = True
            print(f"Loaded {len(frames)} animation frames")
        else:
            print("No animation frames found")

    def _on_toggle_ring(self):
        """Handle TOGGLE_CIRCLE_RING event. Only toggle if this circle is active."""
        if self.mode_active:
            self.toggle_ring()

    def _get_tonic_index(self) -> int:
        """Return the gate index of the current tonic (root) based on active ring."""
        root_pc = self.theory.root_note % 12
        if self.active_ring == "major":
            for i, pc in enumerate(MAJOR_PITCHES):
                if pc == root_pc:
                    return i
        else:
            for i, pc in enumerate(MINOR_PITCHES):
                if pc == root_pc:
                    return i
        return 0  # fallback
    
    def start_entry_animation(self):
        """Trigger the entry wave animation."""
        self.entry_anim_active = True
        self.entry_anim_start_time = pygame.time.get_ticks()
        # Use selected index if available, otherwise tonic
        if self.selected_index is not None:
            self.anim_center_index = self.selected_index
        else:
            self.anim_center_index = self._get_tonic_index()

    # ------------------------------------------------------------------
    # Abstract methods (must be overridden)
    # ------------------------------------------------------------------
    @abstractmethod
    def get_gate_label(self, gate_index: int, is_major_ring: bool, chord_info: dict) -> str:
        """Return the text to display on the gate."""
        pass

    @abstractmethod
    def on_select(self, gate_index: int) -> None:
        """Handle selection of a gate."""
        pass

    def get_center_text(self) -> str:
        """Override to return text for center of circle (e.g., roman numeral). Default None."""
        return None

    # Optional override: change style for selected gate, etc.
    def get_gate_style(self, is_focused: bool, is_major_ring: bool,
                       is_tonic: bool, has_triad: bool, is_diatonic: bool,
                       is_selected: bool):
        """Return (color, radius, text_color). Subclasses can override."""
        if is_selected:
            # Default: selected gate uses tonic style
            if is_major_ring:
                return self.major_focused_tonic, self.radius_tonic, self.major_focused_text
            else:
                return self.minor_focused_tonic, self.radius_tonic, self.minor_focused_text
        else:
            if is_major_ring:
                return self._get_major_gate_style(is_focused, is_tonic, has_triad, is_diatonic)
            else:
                return self._get_minor_gate_style(is_focused, is_tonic, has_triad, is_diatonic)

    # ------------------------------------------------------------------
    # Internal style helpers (can be used by subclasses)
    # ------------------------------------------------------------------
    def _init_default_colors(self):
        # Major focused
        self.major_focused_tonic = (255, 80, 80)
        self.major_focused_triad = (255, 165, 0)
        self.major_focused_diatonic = (0, 200, 200)
        self.major_focused_other = (100, 100, 100)
        self.major_focused_text = (255, 255, 255)
        self.major_focused_hover_color = (255, 255, 255)
        self.major_focused_hover_text = (0, 0, 0)

        self.major_dim_tonic = (180, 80, 80)
        self.major_dim_triad = (139, 0, 0)
        self.major_dim_diatonic = (80, 180, 180)
        self.major_dim_other = (60, 60, 60)
        self.major_dim_text = (200, 200, 200)

        self.minor_focused_tonic = (255, 80, 80)
        self.minor_focused_triad = (128, 0, 128)
        self.minor_focused_diatonic = (0, 200, 200)
        self.minor_focused_other = (100, 100, 100)
        self.minor_focused_text = (255, 255, 255)
        self.minor_focused_hover_color = (255, 255, 255)
        self.minor_focused_hover_text = (0, 0, 0)

        self.minor_dim_tonic = (180, 80, 80)
        self.minor_dim_triad = (6, 64, 43)
        self.minor_dim_diatonic = (80, 180, 180)
        self.minor_dim_other = (60, 60, 60)
        self.minor_dim_text = (200, 200, 200)

    def apply_theme(self, theme):
        # Major focused
        self.major_focused_tonic = theme.adjust_brightness("accent", 1.4)
        self.major_focused_triad = theme.adjust_brightness("color2", 1.2)
        self.major_focused_diatonic = theme.adjust_brightness("neutral", 1.6)
        self.major_focused_other = theme.adjust_brightness("neutral", 1.6)
        self.major_focused_text = (255, 255, 255)
        self.major_focused_hover_color = (255, 255, 255)
        self.major_focused_hover_text = (0, 0, 0)

        self.major_dim_tonic = tuple(int(c * 0.6) for c in theme.accent)
        self.major_dim_triad = tuple(int(c * 0.6) for c in theme.color2)
        self.major_dim_diatonic = tuple(int(c * 0.6) for c in theme.bright)
        self.major_dim_other = tuple(int(c * 0.6) for c in theme.neutral)
        self.major_dim_text = (200, 200, 200)

        self.minor_focused_tonic = theme.complementary
        self.minor_focused_triad = theme.color3
        self.minor_focused_diatonic = theme.adjust_brightness("neutral", 1.6)
        self.minor_focused_other = theme.adjust_brightness("neutral", 1.6)
        self.minor_focused_text = (255, 255, 255)
        self.minor_focused_hover_color = (255, 255, 255)
        self.minor_focused_hover_text = (0, 0, 0)

        self.minor_dim_tonic = tuple(int(c * 0.6) for c in theme.complementary)
        self.minor_dim_triad = tuple(int(c * 0.6) for c in theme.color3)
        self.minor_dim_diatonic = tuple(int(c * 0.6) for c in theme.bright)
        self.minor_dim_other = tuple(int(c * 0.6) for c in theme.neutral)
        self.minor_dim_text = (200, 200, 200)

    def _get_major_gate_style(self, is_focused, is_tonic, has_triad, is_diatonic):
        if not is_focused:
            if is_tonic: return self.major_dim_tonic, self.dim_radius_tonic, self.major_dim_text
            elif has_triad: return self.major_dim_triad, self.dim_radius_triad, self.major_dim_text
            elif is_diatonic: return self.major_dim_diatonic, self.dim_radius_diatonic, self.major_dim_text
            else: return self.major_dim_other, self.dim_radius_other, self.major_dim_text
        else:
            if is_tonic: return self.major_focused_tonic, self.radius_tonic, self.major_focused_text
            elif has_triad: return self.major_focused_triad, self.radius_triad, self.major_focused_text
            elif is_diatonic: return self.major_focused_diatonic, self.radius_diatonic, self.major_focused_text
            else: return self.major_focused_other, self.radius_other, self.major_focused_text

    def _get_minor_gate_style(self, is_focused, is_tonic, has_triad, is_diatonic):
        if not is_focused:
            if is_tonic: return self.minor_dim_tonic, self.dim_radius_tonic, self.minor_dim_text
            elif has_triad: return self.minor_dim_triad, self.dim_radius_triad, self.minor_dim_text
            elif is_diatonic: return self.minor_dim_diatonic, self.dim_radius_diatonic, self.minor_dim_text
            else: return self.minor_dim_other, self.dim_radius_other, self.minor_dim_text
        else:
            if is_tonic: return self.minor_focused_tonic, self.radius_tonic, self.minor_focused_text
            elif has_triad: return self.minor_focused_triad, self.radius_triad, self.minor_focused_text
            elif is_diatonic: return self.minor_focused_diatonic, self.radius_diatonic, self.minor_focused_text
            else: return self.minor_focused_other, self.radius_other, self.minor_focused_text

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------
    def _get_circle_surface(self, color, radius):
        radius = max(1, int(radius))
        key = (color, radius)
        if key in self.circle_cache:
            return self.circle_cache[key]
        if self.white_circle:
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
                if self.easing == "ease_out": t = 1 - (1 - t)**2
                elif self.easing == "ease_in_out": t = 0.5 - 0.5 * math.cos(math.pi * t)
                start_rad = self.current_radius[key]
                new_rad = start_rad + (target_radius - start_rad) * t
                self.current_radius[key] = new_rad
                return new_rad
        else:
            return self.current_radius.get(key, target_radius)

    def _draw_ring(self, surface, cx, cy, ring_radius, is_focused, is_major):
        now = pygame.time.get_ticks()
        ring_key = "major" if is_major else "minor"

        for i in range(12):
            angle = math.radians(i * 30 - 90)
            pc = MAJOR_PITCHES[i] if is_major else MINOR_PITCHES[i]
            info = self.chord_qualities.get(pc, {})
            is_diatonic = info.get('diatonic', False)
            quality = info.get('quality')
            mode_is_minor = self.theory.mode in ["Minor", "Aeolian"]
            is_tonic = (quality == 'tonic') and ((is_major and not mode_is_minor) or (not is_major and mode_is_minor))
            if is_major:
                has_triad = (quality == 'major')
            else:
                has_triad = (quality == 'minor')

            is_selected = (self.selected_index == i and self.selected_ring == ring_key)

            # --- Entry animation wave ---
            pulse_factor = 0.0
            if self.entry_anim_active:
                elapsed = now - self.entry_anim_start_time
                if elapsed >= self.entry_anim_duration:
                    self.entry_anim_active = False
                else:
                    dist = min(abs(i - self.anim_center_index), 12 - abs(i - self.anim_center_index))
                    delay = (dist / 12.0) * self.entry_anim_duration
                    if elapsed >= delay:
                        local_t = (elapsed - delay) / (self.entry_anim_duration * 0.3)
                        if local_t <= 1.0:
                            pulse_factor = 1.0 - local_t**0.5
                            pulse_factor = min(1.0, pulse_factor * 2.0)

            # Get base style
            color, target_radius, text_color = self.get_gate_style(
                is_focused, is_major, is_tonic, has_triad, is_diatonic, is_selected
            )

            

            # Apply pulse effect
            if pulse_factor > 0:
                target_radius = target_radius * (1 + 0.3 * pulse_factor)
                r, g, b = color[:3]
                factor = 1 + 0.5 * pulse_factor
                color = (min(255, int(r * factor)), min(255, int(g * factor)), min(255, int(b * factor)))

            # Hover override
            if is_focused and self.hovered_index == i and self.active_ring == ring_key:
                if is_major:
                    color = self.major_focused_hover_color
                    target_radius = self.radius_hover_major
                    text_color = self.major_focused_hover_text
                else:
                    color = self.minor_focused_hover_color
                    target_radius = self.radius_hover_minor
                    text_color = self.minor_focused_hover_text

            # Label from subclass
            label = self.get_gate_label(i, is_major, info)

            animated_radius = self._update_radius_animation(ring_key, i, target_radius, now)

            # --- Use animation frame for selected gate if available ---
            if is_selected and self.selected_anim_playing and self.selected_anim_frames:
                print(f"ANIMATING gate {i} frame {self.selected_anim_frame_index}")
                frame = self.selected_anim_frames[self.selected_anim_frame_index]
                scaled_frame = pygame.transform.smoothscale(frame, (int(animated_radius*2), int(animated_radius*2)))
                surf = scaled_frame
            else:
                print(f"NO ANIM for gate {i}: selected={is_selected}, playing={self.selected_anim_playing}, frames={len(self.selected_anim_frames) if self.selected_anim_frames else 0}")
                surf = self._get_circle_surface(color, int(animated_radius))

            x = cx + math.cos(angle) * ring_radius
            y = cy + math.sin(angle) * ring_radius
            rect = surf.get_rect(center=(int(x), int(y)))
            surface.blit(surf, rect)

            text_surf = self.parent.font_status.render(label, True, text_color)
            text_rect = text_surf.get_rect(center=(int(x), int(y)))
            surface.blit(text_surf, text_rect)

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------
    def _on_focus_changed(self, mode: str):
        self.focus_active = (mode == "circle")

    def _on_stick_updated(self, x: float, y: float):
        if not (self.focus_active and self.mode_active):
            return
        # Optional inversion
        x = -x
        y = -y
        dist = math.hypot(x, y)
        DEADZONE = 0.01
        EXIT_GRACE_FRAMES = 10

        if dist < DEADZONE:
            self.exit_timer += 1
            if self.exit_timer >= EXIT_GRACE_FRAMES and self.hovered_index is not None:
                self.on_select(self.hovered_index)
                self.hovered_index = None
                self.exit_timer = 0
            return

        self.exit_timer = 0
        angle = math.degrees(math.atan2(y, x))
        angle = (angle + 360) % 360
        angle = (angle - 90) % 360
        idx = int((angle + 15) // 30) % 12
        if idx != self.hovered_index:
            self.hovered_index = idx

    def _on_chord_qualities_changed(self, qualities: dict):
        self.chord_qualities = qualities

    def toggle_ring(self):
        self.active_ring = "minor" if self.active_ring == "major" else "major"
        self.hovered_index = None
        self.exit_timer = 0
        # Optionally clear selected_index when ring changes? Subclass can decide.
        bus.emit("ADD_LOG", text=f"Circle ring: {self.active_ring.upper()}", color=(200,200,100))

    # ------------------------------------------------------------------
    # Public draw method
    # ------------------------------------------------------------------
    def draw(self, surface, rect):
        self._update_selected_animation()
        cx = rect.centerx
        cy = rect.centery
        max_radius = min(rect.width, rect.height) // 2 - 10
        outer_radius = max_radius * self.outer_radius_ratio
        inner_radius = max_radius * self.inner_radius_ratio
        is_focused = True

        self._draw_ring(surface, cx, cy, outer_radius, is_focused, is_major=True)
        self._draw_ring(surface, cx, cy, inner_radius, is_focused, is_major=False)

        center_text = self.get_center_text()
        if center_text:
            text_surf = self.center_text_font.render(center_text, True, self.center_text_color[:3])
            if len(self.center_text_color) == 4:
                text_surf.set_alpha(self.center_text_color[3])
            text_rect = text_surf.get_rect(center=(cx + self.center_text_offset_x, cy + self.center_text_offset_y))
            surface.blit(text_surf, text_rect)

        # Optional center dot
        # pygame.draw.circle(surface, (120,120,140), (cx, cy), 8, 1)