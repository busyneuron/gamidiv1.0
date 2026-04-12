# radial_menu/rm_view.py
import pygame
import math
from .rm_models import RadialState

class RadialMenuView:
    def __init__(self, parent, controller):
        self.parent = parent
        self.controller = controller

        # ==========================================
        # CONFIGURATION
        # ==========================================
        self.base_radius = 45
        self.ring_step = 30
        self.pointer_size = 5
        self.pointer_arrow_size = 12
        self.trail_maxlen = 20

        self.crosshair_color = (40, 40, 45)
        self.path_line_color = (0, 0, 0, 200)
        self.trail_color = (0, 180, 140)
        self.direction_line_color = (0, 180, 140, 128)
        self.pointer_color = (0, 180, 140)
        self.dim_color = (80, 80, 80)
        self.dim_alpha = 180

        self.circle_size_normal = 8
        self.circle_size_hover = 10
        self.circle_size_dim = 4
        self.hover_outline_color = (255, 255, 255)
        self.hover_outline_width = 2

        self.float_amplitude = 2.0
        self.float_speed = 0.5
        self.float_style = "radial"

        self.gate_png = None
        self.gate_cache = {}
        self._load_gate_png()


        self.pointer_idle_anim_scale = 1.0
        self.pointer_idle_anim_start = 0
        self.pointer_idle_anim_duration = 200
        self.pointer_idle_anim_active = False
        self.prev_dist = 0.0
        self.pointer_idle_threshold = 0.1

        self.pointer_size = 24                    # desired width/height in pixels
        self.pointer_idle_size = 15
        self.pointer_tint = parent.theme.bright        # color to tint the pointer
        self.pointer_img = None
        self.pointer_idle_img = None
        self._load_pointer_images()

        # Animation state
        self.animated_radii = {}
        self.target_radii = {}
        self.anim_start_time = {}
        self.prev_stack_len = 0
        self.animation_duration = 200
        self.animation_easing = "ease_out"
        self.initial_scale = 0.4

        self.circle_anim = {}

        self.trail = []
        self.ripples = []

        self.gate_on_png = None
        self.gate_on_mask = None
        self.mask_scroll_x = 0
        self.mask_scroll_speed = 0.2
        self._load_gate_on_assets()

    # ----------------------------------------------------------------------
    # Asset loading
    # ----------------------------------------------------------------------
    def _load_gate_png(self):
        try:
            self.gate_png = pygame.image.load("assets/gate.png").convert_alpha()
        except:
            self.gate_png = None
    
    def _load_gate_on_assets(self):
        try:
            self.gate_on_png = pygame.image.load("assets/gate_on.png").convert_alpha()
            self.gate_on_mask = pygame.image.load("assets/gate_on_mask.png").convert_alpha()
        except Exception as e:
            print(f"Failed to load gate_on assets: {e}")
            self.gate_on_png = None
            self.gate_on_mask = None

    def _load_pointer_images(self):
        try:
            raw = pygame.image.load("assets/pointer.png").convert_alpha()
            self.pointer_img = self._tint_image(raw, self.pointer_tint)
            raw_idle = pygame.image.load("assets/pointer_idle.png").convert_alpha()
            self.pointer_idle_img = self._tint_image(raw_idle, self.pointer_tint)
        except Exception as e:
            print(f"Failed to load pointer images: {e}")
            self.pointer_img = None
            self.pointer_idle_img = None

    def _tint_image(self, image, color):
        """Tint an RGBA surface with the given RGB color."""
        tinted = image.copy()
        tinted.fill(color, special_flags=pygame.BLEND_RGB_MULT)
        return tinted

    def _get_gate_surface(self, color, radius):
        radius = max(1, int(radius))
        key = (color, radius)
        if key in self.gate_cache:
            return self.gate_cache[key]
        if self.gate_png:
            scaled = pygame.transform.smoothscale(self.gate_png, (radius*2, radius*2))
            tinted = scaled.copy()
            tinted.fill(color, special_flags=pygame.BLEND_RGB_MULT)
            self.gate_cache[key] = tinted
            return tinted
        else:
            surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (radius, radius), radius)
            self.gate_cache[key] = surf
            return surf

    # ----------------------------------------------------------------------
    # Animation helpers
    # ----------------------------------------------------------------------
    def _update_ring_animations(self, state, now):
        current_len = len(state.stack)
        if current_len != self.prev_stack_len:
            if current_len > self.prev_stack_len:
                new_level = current_len - 1
                target = self.base_radius + new_level * self.ring_step
                self.target_radii[new_level] = target
                self.animated_radii[new_level] = target * self.initial_scale
                self.anim_start_time[new_level] = now
            self.prev_stack_len = current_len

        for level in range(current_len):
            target = self.base_radius + level * self.ring_step
            if level not in self.target_radii:
                self.target_radii[level] = target
                self.animated_radii[level] = target
            if level in self.anim_start_time:
                elapsed = now - self.anim_start_time[level]
                if elapsed >= self.animation_duration:
                    self.animated_radii[level] = target
                    del self.anim_start_time[level]
                else:
                    t = elapsed / self.animation_duration
                    if self.animation_easing == "ease_out":
                        t = 1 - (1 - t)**2
                    elif self.animation_easing == "ease_in_out":
                        t = 0.5 - 0.5 * math.cos(math.pi * t)
                    start_rad = self.animated_radii[level]
                    self.animated_radii[level] = start_rad + (target - start_rad) * t
            else:
                self.animated_radii[level] = target

    def _update_circle_animation(self, key, target_size, now):
        if key not in self.circle_anim:
            self.circle_anim[key] = {'size': target_size, 'target': target_size, 'start_time': now}
            return target_size
        anim = self.circle_anim[key]
        if anim['target'] != target_size:
            anim['target'] = target_size
            anim['start_time'] = now
        elapsed = now - anim['start_time']
        if elapsed >= self.animation_duration:
            anim['size'] = target_size
            return target_size
        t = elapsed / self.animation_duration
        if self.animation_easing == "ease_out":
            t = 1 - (1 - t)**2
        elif self.animation_easing == "ease_in_out":
            t = 0.5 - 0.5 * math.cos(math.pi * t)
        start = anim['size']
        anim['size'] = start + (target_size - start) * t
        return anim['size']

    # ----------------------------------------------------------------------
    # Drawing subcomponents
    # ----------------------------------------------------------------------
    def _draw_rings(self, surface, state, cx, cy, active, now, entry_gate_for_level):
        for i, menu in enumerate(state.stack):
            radius = self.animated_radii.get(i, self.base_radius + i * self.ring_step)
            is_top = (i == len(state.stack)-1)
            if not active:
                dim_factor = 0.4
                highlight_gate = None
            else:
                if is_top:
                    dim_factor = 1.0
                    highlight_gate = state.hovered_direction
                else:
                    # For parent menus, dim all except the entry gate
                    dim_factor = 0.3
                    highlight_gate = entry_gate_for_level.get(i)
            self._draw_menu(surface, menu, cx, cy, radius, dim_factor,
                            state.hovered_direction if (is_top and active) else None,
                            now, i, highlight_gate)

    def _draw_menu(self, screen, menu, cx, cy, radius, dim_factor, hovered_dir, now, level, highlight_gate=None):
        for i, (dir_key, gate) in enumerate(menu.gates.items()):
            angle = self._direction_to_angle(dir_key)
            rad = math.radians(angle)
            px = cx + math.cos(rad) * radius
            py = cy + math.sin(rad) * radius

            # Determine effective dim factor for this gate
            effective_dim = dim_factor
            if highlight_gate == dir_key:
                effective_dim = 1.0   # fully bright

            # Floating animation only for non-dimmed gates
            if effective_dim >= 0.9:
                t = now / 1000.0
                phase = t * self.float_speed * 2 * math.pi + (i * 2 * math.pi / 8)
                if self.float_style == "radial":
                    offset = math.sin(phase) * self.float_amplitude
                    px += math.cos(rad) * offset
                    py += math.sin(rad) * offset

            center = (int(px), int(py))
            is_hovered = (hovered_dir == dir_key)
            is_active = self.controller.is_gate_active(gate.action_id) if gate.action_id else False

            # Determine target size and color
            if effective_dim < 1.0:
                target_size = self.circle_size_dim
                alpha = int(self.dim_alpha * effective_dim)
                color = self.dim_color
            elif is_hovered:
                target_size = self.circle_size_hover
                alpha = 255
                color = gate.color
            else:
                target_size = self.circle_size_normal
                alpha = 255
                color = gate.color

            anim_key = (level, dir_key)
            current_size = self._update_circle_animation(anim_key, target_size, now)

            # Draw active indicator (bubble + scrolling mask) if gate is active and not dimmed
            if is_active and effective_dim >= 0.9:
                # Update mask scroll
                if self.gate_on_mask:
                    self.mask_scroll_x += self.mask_scroll_speed
                    if self.mask_scroll_x >= self.gate_on_mask.get_width():
                        self.mask_scroll_x -= self.gate_on_mask.get_width()

                # Draw the gate_on bubble (scaled)
                if self.gate_on_png:
                    bubble_size = int(current_size * 2)
                    bubble_surf = pygame.transform.smoothscale(self.gate_on_png, (bubble_size, bubble_size))
                    bubble_rect = bubble_surf.get_rect(center=center)
                    screen.blit(bubble_surf, bubble_rect)

                # Draw the scrolling mask over the bubble
                if self.gate_on_mask:
                    mask_size = int(current_size * 2)
                    mask_surf = pygame.transform.smoothscale(self.gate_on_mask, (mask_size, mask_size))
                    src_x = int(self.mask_scroll_x) % mask_surf.get_width()
                    src_rect = pygame.Rect(src_x, 0, mask_surf.get_width(), mask_surf.get_height())
                    screen.blit(mask_surf, bubble_rect, src_rect, special_flags=pygame.BLEND_RGBA_MULT)

            # Draw the regular gate circle (you can skip this if you want only the bubble)
            surf = self._get_gate_surface(color, int(current_size))
            if effective_dim < 1.0:
                surf.set_alpha(alpha)
            rect = surf.get_rect(center=center)
            screen.blit(surf, rect)

            # Hover outline
            if is_hovered and effective_dim >= 0.9:
                pygame.draw.circle(screen, self.hover_outline_color, center, int(current_size) + 2, self.hover_outline_width)

            # Label
            font = self.parent.font_status
            label_surf = font.render(gate.label, True, color)
            if effective_dim < 1.0:
                label_surf.set_alpha(alpha)
            text_x = px + (12 if math.cos(rad) >= 0 else -label_surf.get_width() - 12)
            text_y = py - 6
            screen.blit(label_surf, (int(text_x), int(text_y)))
            
    def _draw_path_line(self, surface, state, cx, cy, active):
        if not active or len(state.stack) <= 1:
            return
        points = [(cx, cy)]
        for i, menu in enumerate(state.stack):
            radius = self.animated_radii.get(i, self.base_radius + i * self.ring_step)
            if i == len(state.stack)-1:
                if state.hovered_direction and state.hovered_direction in menu.gates:
                    angle = self._direction_to_angle(state.hovered_direction)
                    rad = math.radians(angle)
                    px = cx + math.cos(rad) * radius
                    py = cy + math.sin(rad) * radius
                    points.append((px, py))
            else:
                next_menu = state.stack[i+1]
                for dir_key, gate in menu.gates.items():
                    if gate.sub_menu == next_menu:
                        angle = self._direction_to_angle(dir_key)
                        rad = math.radians(angle)
                        px = cx + math.cos(rad) * radius
                        py = cy + math.sin(rad) * radius
                        points.append((px, py))
                        break
        if len(points) > 1:
            for j in range(len(points)-1):
                start = (int(points[j][0]), int(points[j][1]))
                end = (int(points[j+1][0]), int(points[j+1][1]))
                pygame.draw.line(surface, self.path_line_color, start, end, 2)

    def _draw_trail(self, surface, cx, cy, active):
        if not active or len(self.trail) <= 1:
            return
        for j in range(len(self.trail)-1):
            age = j / len(self.trail)
            brightness = max(0.3, 1.0 - age * 0.7)
            color = tuple(int(c * brightness) for c in self.trail_color)
            start = (int(self.trail[j][0]), int(self.trail[j][1]))
            end = (int(self.trail[j+1][0]), int(self.trail[j+1][1]))
            pygame.draw.line(surface, color, start, end, 1)
        # Optional: draw circles at points
        # for j, (x, y) in enumerate(self.trail):
        #     age = j / len(self.trail)
        #     brightness = max(0.3, 1.0 - age * 0.7)
        #     color = tuple(int(c * brightness) for c in self.trail_color)
        #     pygame.draw.circle(surface, color, (int(x), int(y)), 2)

    def _draw_direction_line(self, surface, cx, cy, active):
        if active and len(self.trail) > 0:
            last_ptr = self.trail[-1]
            dir_color = tuple(int(c * 0.5) for c in self.trail_color)
            pygame.draw.line(surface, dir_color, (cx, cy), (int(last_ptr[0]), int(last_ptr[1])), 1)

    def _draw_crosshair(self, surface, cx, cy, active):
        color = self.crosshair_color if active else (80, 80, 80)
        pygame.draw.line(surface, color, (cx - 20, cy), (cx + 20, cy), 1)
        pygame.draw.line(surface, color, (cx, cy - 20), (cx, cy + 20), 1)

    def _draw_pointer(self, surface, cx, cy, axes, active, now):
        if not active or len(self.trail) == 0:
            return
        dist = math.hypot(axes.get("radial_menu_x", 0.0), axes.get("radial_menu_y", 0.0))
        ptr_x, ptr_y = self.trail[-1]
        
        if dist > 0.0:
            angle = math.atan2(ptr_y - cy, ptr_x - cx)
            angle_deg = math.degrees(angle)
            if self.pointer_img:
                # Original pointer points north (up). Rotate to match angle.
                # North is -90° in math coordinates. To point at angle, rotation = angle_deg + 90
                rot_deg = angle_deg + 90
                rotated = pygame.transform.rotate(self.pointer_img, -rot_deg)
                scaled = pygame.transform.smoothscale(rotated, (self.pointer_size, self.pointer_size))
                rect = scaled.get_rect(center=(int(ptr_x), int(ptr_y)))
                surface.blit(scaled, rect)
            else:
                # Fallback polygon
                arrow_len = self.pointer_arrow_size
                tip = (ptr_x, ptr_y)
                left = (ptr_x - arrow_len * math.cos(angle - math.pi/6),
                        ptr_y - arrow_len * math.sin(angle - math.pi/6))
                right = (ptr_x - arrow_len * math.cos(angle + math.pi/6),
                         ptr_y - arrow_len * math.sin(angle + math.pi/6))
                pygame.draw.polygon(surface, self.pointer_color, [tip, left, right])
        else:
            # Idle pointer: apply animation scale
            scale = self.pointer_idle_anim_scale
            if self.pointer_idle_anim_active:
                elapsed = now - self.pointer_idle_anim_start
                if elapsed >= self.pointer_idle_anim_duration:
                    scale = 1.0
                    self.pointer_idle_anim_active = False
                else:
                    t = elapsed / self.pointer_idle_anim_duration
                    # ease out: t = 1 - (1-t)^2
                    t = 1 - (1 - t) ** 2
                    scale = 0.2 + (1.0 - 0.2) * t
                    self.pointer_idle_anim_scale = scale
            target_size = int(self.pointer_idle_size * scale)
            target_size = max(1, target_size)
            if self.pointer_idle_img:
                scaled = pygame.transform.smoothscale(self.pointer_idle_img, (target_size, target_size))
                rect = scaled.get_rect(center=(int(ptr_x), int(ptr_y)))
                surface.blit(scaled, rect)
            elif self.pointer_img:
                scaled = pygame.transform.smoothscale(self.pointer_img, (target_size, target_size))
                rect = scaled.get_rect(center=(int(ptr_x), int(ptr_y)))
                surface.blit(scaled, rect)
            else:
                pygame.draw.circle(surface, self.pointer_color, (int(ptr_x), int(ptr_y)), target_size // 2)

    # ----------------------------------------------------------------------
    # Main draw
    # ----------------------------------------------------------------------
    def draw(self, surface, rect):
        now = pygame.time.get_ticks()
        state = self.controller.get_state()
        if not state.stack:
            return
        active = self.controller.is_active()
        axes = self.controller.get_axes()
        cx = rect.centerx
        cy = rect.centery

        # Compute which gate in each parent menu leads to the next level
        entry_gate_for_level = {}
        stack = state.stack
        for i in range(len(stack)-1):
            menu = stack[i]
            next_menu = stack[i+1]
            for dir_key, gate in menu.gates.items():
                if gate.sub_menu == next_menu:
                    entry_gate_for_level[i] = dir_key
                    break

        # Update pointer trail (unchanged)
        if active:
            ptr_x = cx + axes.get("radial_menu_x", 0.0) * self.base_radius
            ptr_y = cy + axes.get("radial_menu_y", 0.0) * self.base_radius
            self.trail.append((ptr_x, ptr_y))
            if len(self.trail) > self.trail_maxlen:
                self.trail.pop(0)

        dist = math.hypot(axes.get("radial_menu_x", 0.0), axes.get("radial_menu_y", 0.0))
        if dist <= self.pointer_idle_threshold and self.prev_dist > self.pointer_idle_threshold:
            self.pointer_idle_anim_scale = 0.2
            self.pointer_idle_anim_start = now
            self.pointer_idle_anim_active = True
        self.prev_dist = dist

        self._update_ring_animations(state, now)

        self._draw_rings(surface, state, cx, cy, active, now, entry_gate_for_level)
        self._draw_path_line(surface, state, cx, cy, active)
        self._draw_pointer(surface, cx, cy, axes, active, now)

    @staticmethod
    def _direction_to_angle(direction: str) -> float:
        dirs = ["E", "SE", "S", "SW", "W", "NW", "N", "NE"]
        idx = dirs.index(direction)
        return idx * 45