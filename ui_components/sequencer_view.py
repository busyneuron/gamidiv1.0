# ui_components/sequencer_view.py
import pygame
import os
import math


class SequencerView:
    def __init__(self, parent):
        self.parent = parent
        self.font = parent.theme.fonts.get_mono_bold(14)

        # ==========================================
        # Aesthetic parameters
        # ==========================================
        self.ball_radius = 9         # base step size
        self.gap_balls = 2           # gap between adjacent balls
        self.gap_quarters = 10       # extra gap every 4 steps (a quarter)
        self.quarter_group = 4       # steps per quarter (16th notes)

        self.color_active = parent.theme.accent
        self.color_inactive = (50, 50, 60)
        self.color_connection = parent.theme.accent
        self.color_playhead = (255, 255, 255)
        self.color_edit = (255, 255, 0)

        self.highlight_scale = 1.6   # how much a highlighted ball grows
        self.anim_duration = 150     # ms
        self.anim_easing = "ease_out"

        # ==========================================
        # Assets (graceful fallback to circles/lines)
        # ==========================================
        self.asset_step = self._load("assets/step.png")
        self.asset_start = self._load("assets/step_start.png")
        self.asset_mid = self._load("assets/step_mid.png")
        self.asset_end = self._load("assets/step_end.png")

        # Animation state
        self._radii = {}
        self._targets = {}
        self._anim_start = {}

    def _load(self, path):
        if os.path.exists(path):
            try:
                return pygame.image.load(path).convert_alpha()
            except Exception:
                return None
        return None

    def _step_center_x(self, rect, i, total):
        """X center of step i, honoring ball gaps and quarter gaps."""
        pitch = self.ball_radius * 2 + self.gap_balls
        num_qgaps = max(0, (total - 1) // self.quarter_group)
        total_w = total * pitch + num_qgaps * self.gap_quarters
        start_x = rect.centerx - total_w / 2 + self.ball_radius
        return start_x + i * pitch + (i // self.quarter_group) * self.gap_quarters

    def _animated_radius(self, i, target, now):
        """Ease the radius of step i toward `target` (circle-of-fifths style)."""
        if i not in self._radii:
            self._radii[i] = target
            self._targets[i] = target
            return target
        if self._targets.get(i) != target:
            self._targets[i] = target
            self._anim_start[i] = now
            return self._radii[i]
        if i in self._anim_start:
            elapsed = now - self._anim_start[i]
            if elapsed >= self.anim_duration:
                self._radii[i] = target
                del self._anim_start[i]
                return target
            t = elapsed / self.anim_duration
            if self.anim_easing == "ease_out":
                t = 1 - (1 - t) ** 2
            elif self.anim_easing == "ease_in_out":
                t = 0.5 - 0.5 * math.cos(math.pi * t)
            start = self._radii[i]
            self._radii[i] = start + (target - start) * t
            return self._radii[i]
        return self._radii.get(i, target)

    def _blit_scaled(self, surface, asset, cx, cy, radius, fallback_color=None):
        if asset is not None:
            size = max(2, int(radius * 2))
            img = pygame.transform.smoothscale(asset, (size, size))
            surface.blit(img, img.get_rect(center=(int(cx), int(cy))))
        elif fallback_color is not None:
            pygame.draw.circle(surface, fallback_color, (int(cx), int(cy)), int(radius))

    def _draw_connection(self, surface, start_cx, end_cx, cy, radius):
        """Draw the body of a multi-step note between its start and end caps."""
        if self.asset_mid is not None:
            span = max(2, int(end_cx - start_cx))
            h = max(2, int(radius * 2))
            img = pygame.transform.smoothscale(self.asset_mid, (span, h))
            surface.blit(img, img.get_rect(center=(int((start_cx + end_cx) / 2), int(cy))))
        else:
            pygame.draw.line(surface, self.color_connection,
                             (int(start_cx), int(cy)), (int(end_cx), int(cy)),
                             max(2, int(radius)))

    def draw(self, surface, rect, state):
        now = pygame.time.get_ticks()
        total = state.total_steps
        cy = rect.centery

        # Map each step to the bounds of its note (an active run, honoring ties)
        run_start = {}
        run_end = {}
        i = 0
        while i < total:
            if state.steps[i].active:
                s = i
                i += 1
                while i < total and state.steps[i].active and state.steps[i].tie:
                    i += 1
                e = i - 1
                for j in range(s, e + 1):
                    run_start[j] = s
                    run_end[j] = e
            else:
                i += 1

        # Connections (drawn under the balls)
        for i in range(total):
            if state.steps[i].active and run_start.get(i) == i and run_end[i] > i:
                start_cx = self._step_center_x(rect, i, total)
                end_cx = self._step_center_x(rect, run_end[i], total)
                self._draw_connection(surface, start_cx, end_cx, cy, self.ball_radius)

        # Balls
        for i in range(total):
            active = state.steps[i].active
            s = run_start.get(i, i)
            e = run_end.get(i, i)

            is_edit = state.is_editing and state.edit_step == i
            is_playhead = state.is_editing and state.playhead_step == i
            target_r = (self.ball_radius * self.highlight_scale
                        if (is_edit or is_playhead) else self.ball_radius)
            r = self._animated_radius(i, target_r, now)
            cx = self._step_center_x(rect, i, total)

            if not active:
                self._blit_scaled(surface, self.asset_step, cx, cy, r, self.color_inactive)
            elif e == s:
                self._blit_scaled(surface, self.asset_start, cx, cy, r, self.color_active)
            elif i == s:
                self._blit_scaled(surface, self.asset_start, cx, cy, r, self.color_active)
            elif i == e:
                self._blit_scaled(surface, self.asset_end, cx, cy, r, self.color_active)
            # middle steps are covered by the connection

            # Edit cursor ring
            if is_edit:
                pygame.draw.circle(surface, self.color_edit, (int(cx), int(cy)), int(r) + 3, 2)

            # Playhead marker
            if is_playhead:
                pygame.draw.line(surface, self.color_playhead,
                                 (int(cx), int(cy) - int(r) - 8),
                                 (int(cx), int(cy) + int(r) + 8), 2)
