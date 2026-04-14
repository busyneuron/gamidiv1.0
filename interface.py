# interface.py
import pygame
import os
from ui_utils import Grid, Theme
from ui_components.keyboard import Keyboard
from ui_components.piano_roll import PianoRoll
from radial_menu.rm_view import RadialMenuView
from ui_state import UIState
from ui_components.scale_hud import ScaleHUD
from ui_components.console import Console
from circle_of_fifths.chromatic_circle import ChromaticCircle
from circle_of_fifths.degree_circle import DegreeCircle
from event_bus import bus

class GamidiInterface:
    def __init__(self, screen, radial_controller, theory_engine):
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
        self.scale_hud = ScaleHUD(self)
        self.console = Console(self)

        # Circle widgets
        self.chromatic_circle = ChromaticCircle(self, theory_engine)
        self.degree_circle = DegreeCircle(self, theory_engine)
        self.chromatic_circle.mode_active = True
        self.degree_circle.mode_active = False
        self.drawn_circle = self.chromatic_circle

        # Apply theme to both
        self.chromatic_circle.apply_theme(self.theme)
        self.degree_circle.apply_theme(self.theme)

        # Subscribe to circle mode toggle event
        bus.on("TOGGLE_CIRCLE_MODE", self._on_toggle_circle_mode)

        self.font_status = pygame.font.SysFont("Arial", 11)
        self.font_label = pygame.font.SysFont("Arial", 10)
        self.font_lcd = pygame.font.SysFont("Consolas", 14)

    def _on_toggle_circle_mode(self):
        if self.drawn_circle is self.chromatic_circle:
            self.chromatic_circle.mode_active = False
            self.drawn_circle = self.degree_circle
            self.degree_circle.mode_active = True
            bus.emit("ADD_LOG", text="Circle mode: DEGREE", color=(200,200,100))
        else:
            self.degree_circle.mode_active = False
            self.drawn_circle = self.chromatic_circle
            self.chromatic_circle.mode_active = True
            bus.emit("ADD_LOG", text="Circle mode: CHROMATIC", color=(200,200,100))
        self.drawn_circle.start_entry_animation()

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

        # Console
        rect_console = self.grid.get_rect(0, 13, 4, 3)
        self.console.draw(self.layer_content, rect_console)

        # Scale HUD
        rect_scale_hud = self.grid.get_rect(1, 2, 10, 3)
        self.scale_hud.draw(self.layer_content, state.scale_hud, rect_scale_hud)

        # Radial menu
        rect_radial = self.grid.get_rect(8, 0, 8, 8)
        self.radial_view.draw(self.layer_content, rect_radial)

        # Circle of Fifths (active widget)
        rect_circle = self.grid.get_rect(2, 5, 6, 5)
        self.drawn_circle.draw(self.layer_content, rect_circle)

        # Composite
        self.screen.blit(self.layer_piano, (0, 0))
        if self.grating_asset:
            self.screen.blit(self.grating_asset, (0, 0))
        if self.plates_asset:
            self.screen.blit(self.plates_asset, (0, 0))
        self.screen.blit(self.layer_content, (0, 0))

        pygame.display.flip()