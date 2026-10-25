# ui_components/sequencer_view.py
import pygame

class SequencerView:
    def __init__(self, parent):
        self.parent = parent
        self.font = parent.theme.fonts.get_mono_bold(14)
        self.color_bg = (*parent.theme.dark, 200) 
        self.color_group_bg = (255, 255, 255, 15)
        self.color_active = parent.theme.accent
        self.color_playhead = (255, 255, 255)
        self.color_edit = (255, 255, 0) # Yellow Edit Cursor
        self.radius = 10

    def draw(self, surface, rect, state):
        bg_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, self.color_bg, bg_surf.get_rect(), border_radius=8)
        surface.blit(bg_surf, rect)
        
        pad_x = 20
        pad_y = rect.height // 2
        num_groups = max(1, state.total_steps // 4)
        gap = 24
        usable_w = rect.width - (pad_x * 2) - ((num_groups - 1) * gap)
        step_w = usable_w / state.total_steps
        
        for i in range(state.total_steps):
            step = state.steps[i]
            group_idx = i // 4
            
            cx = rect.x + pad_x + (i * step_w) + (step_w / 2) + (group_idx * gap)
            cy = rect.y + pad_y
            
            box_rect = pygame.Rect(
                cx - (step_w * 2), 
                cy - (self.radius + 6), 
                step_w * 4, 
                (self.radius + 6) * 2
            )
            box_rect.x += step_w / 2
            box_rect.width = step_w * 3.5
            if i % 4 == 0:
                pygame.draw.rect(surface, self.color_group_bg, box_rect, border_radius=6)
            
            # Connection line
            if step.active:
                end_i = i
                while end_i < state.total_steps and state.steps[end_i].active:
                    end_i += 1
                end_i -= 1
                if end_i > i:
                    end_group_idx = end_i // 4
                    end_cx = rect.x + pad_x + (end_i * step_w) + (step_w / 2) + (end_group_idx * gap)
                    pygame.draw.line(surface, self.color_active, (cx, cy), (end_cx, cy), 5)
            
            # Note Circle
            color = self.color_active if step.active else (50, 50, 60)
            pygame.draw.circle(surface, color, (int(cx), int(cy)), self.radius)
            
            # Edit Cursor (Yellow Box)
            if state.is_editing and state.edit_step == i:
                pygame.draw.rect(surface, self.color_edit, box_rect, 2, border_radius=6)
            
            # Playhead (White Line)
            if state.is_editing and state.playhead_step == i:
                pygame.draw.line(surface, self.color_playhead, 
                                 (int(cx), cy - self.radius - 10), 
                                 (int(cx), cy + self.radius + 10), 2)