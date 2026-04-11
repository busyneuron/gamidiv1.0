import pygame
import os
from ui_utils import Grid, Theme
from ui_components.keyboard import Keyboard
from ui_components.keyboard_state import KeyboardState

class GamidiInterface:
    def __init__(self, screen):
        self.screen = screen
        self.win_w, self.win_h = 736, 736
        self.grid = Grid(self.win_w)
        self.theme = Theme().hue_shift(50)
        
        # --- LAYER SURFACES ---
        self.layer_piano = pygame.Surface((736, 736), pygame.SRCALPHA)
        self.layer_plates = pygame.Surface((736, 736), pygame.SRCALPHA)
        self.layer_content = pygame.Surface((736, 736), pygame.SRCALPHA)

        # --- ASSET LOADING ---
        self.grating_asset = self._load_asset("assets/grating.png", (736, 736))
        self.plates_asset = self._load_asset("assets/plates.png", (736, 736))
        self.background_image = self._load_background("assets/background.png")

        # --- KEYBOARD COMPONENT ---
        self.keyboard = Keyboard(self)

    def _load_asset(self, path, size):
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, size)
        return None

    def _load_background(self, path):
        if os.path.exists(path):
            img = pygame.image.load(path).convert()
            return pygame.transform.scale(img, (self.win_w, self.win_h))
        return None

    def draw(self, state: KeyboardState):
        # 1. Clear and draw background
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            self.screen.fill(self.theme.bg)

        # Clear layers
        self.layer_piano.fill((0, 0, 0, 0))
        self.layer_plates.fill((0, 0, 0, 0))
        self.layer_content.fill((0, 0, 0, 0))

        # 2. Piano roll layer (empty for now, but kept for future)
        # self.piano_roll.draw(...) would go here

        # 3. Draw keyboard onto content layer
        rect_kb = self.grid.get_rect(0, 11, 16, 2)
        self.keyboard.draw(self.layer_content, state, rect_kb)

        # 4. Composite layers in correct order
        self.screen.blit(self.layer_piano, (0, 0))   # piano roll (bottom)
        if self.grating_asset:
            self.screen.blit(self.grating_asset, (0, 0))  # grating overlay
        if self.plates_asset:
            self.screen.blit(self.plates_asset, (0, 0))   # plates overlay
        self.screen.blit(self.layer_content, (0, 0))      # content (keyboard on top)

        pygame.display.flip()