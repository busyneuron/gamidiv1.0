# ui_components/sequencer_view.py
import pygame

class SequencerView:
    def __init__(self, parent):
        self.parent = parent
        self.font = parent.theme.fonts.get_mono_bold(14)
        self.color_bg = (*parent.theme.dark, 200) # Semi-transparent dark
        self.color_active = parent.theme.accent
        self.color_playhead = (255, 255, 255)
        self.radius = 8

    def draw(self, surface, rect, state):
        # Draw panel background
        bg_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, self.color_bg, bg_surf.get_rect(), border_radius=8)
        surface.blit(bg_surf, rect)
        
        # Padding
        pad_x = 20
        pad_y = rect.height // 2
        usable_w = rect.width - (pad_x * 2)
        step_w = usable_w / state.total_steps
        
        for i in range(state.total_steps):
            step = state.steps[i]
            cx = rect.x + pad_x + (i * step_w) + (step_w / 2)
            cy = rect.y + pad_y
            
            # Draw connection line for long notes
            if step.active and step.duration_steps > 1:
                end_x = cx + ((step.duration_steps - 1) * step_w)
                pygame.draw.line(surface, self.color_active, (cx, cy), (end_x, cy), 4)
            
            # Draw note circle
            color = self.color_active if step.active else (50, 50, 60)
            pygame.draw.circle(surface, color, (int(cx), int(cy)), self.radius)
            
            # Draw playhead
            if state.is_recording and state.current_step == i:
                pygame.draw.circle(surface, self.color_playhead, (int(cx), int(cy)), self.radius + 3, 2)