# interface.py
import pygame
import os
from ui_utils import Grid, Theme
from ui_components.keyboard import Keyboard
from ui_components.piano_roll import PianoRoll
from radial_menu.rm_view import RadialMenuView
from ui_state import UIState

class GamidiInterface:
    def __init__(self, screen, radial_controller):
        self.screen = screen
        self.win_w, self.win_h = 736, 736
        self.grid = Grid(self.win_w)
        self.theme = Theme().hue_shift(50)
        
        self.layer_piano = pygame.Surface((736, 736), pygame.SRCALPHA)
        self.layer_plates = pygame.Surface((736, 736), pygame.SRCALPHA)
        self.layer_content = pygame.Surface((736, 736), pygame.SRCALPHA)

        self.grating_asset = self._load_asset("assets/grating.png", (736, 736))
        self.plates_asset = self._load_asset("assets/plates.png", (736, 736))
        self.background_image = self._load_background("assets/background.png")

        self.keyboard = Keyboard(self)
        self.piano_roll = PianoRoll(self)
        self.radial_view = RadialMenuView(self, radial_controller)

        self.font_status = pygame.font.SysFont("Arial", 11)
        self.font_label = pygame.font.SysFont("Arial", 10)
        self.font_lcd = pygame.font.SysFont("Consolas", 14)

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

    def draw(self, state: UIState):
        # Clear and draw background
        if self.background_image:
            self.screen.blit(self.background_image, (0, 0))
        else:
            self.screen.fill(self.theme.bg)

        self.layer_piano.fill((0, 0, 0, 0))
        self.layer_plates.fill((0, 0, 0, 0))
        self.layer_content.fill((0, 0, 0, 0))

        # Piano roll
        rect_piano = self.grid.get_rect(0, 0, 16, 11)
        self.piano_roll.draw(self.layer_piano, state.piano_roll, rect_piano)

        # Keyboard
        rect_kb = self.grid.get_rect(0, 11, 16, 2)
        self.keyboard.draw(self.layer_content, state.keyboard, rect_kb)

        # Radial menu (self-contained)
        rect_radial = self.grid.get_rect(8, 0, 8, 8)
        self.radial_view.draw(self.layer_content, rect_radial)

        # Composite
        self.screen.blit(self.layer_piano, (0, 0))
        if self.grating_asset:
            self.screen.blit(self.grating_asset, (0, 0))
        if self.plates_asset:
            self.screen.blit(self.plates_asset, (0, 0))
        self.screen.blit(self.layer_content, (0, 0))

        pygame.display.flip()