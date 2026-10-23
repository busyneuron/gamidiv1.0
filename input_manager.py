# input_manager.py
import pygame
from event_bus import bus

try:
    from pygame._sdl2 import controller as sdl2controller
    HAS_SDL2_CONTROLLER = True
except ImportError:
    HAS_SDL2_CONTROLLER = False

# Logical button indices (Xbox-style layout used across the app):
#   0-3 face buttons, 4 LB, 5 RB, 6 back, 7 start, 8 L3, 9 R3,
#   12-15 dpad left/right/up/down
SDL_BUTTON_MAP = {
    pygame.CONTROLLER_BUTTON_A: 0,
    pygame.CONTROLLER_BUTTON_B: 1,
    pygame.CONTROLLER_BUTTON_X: 2,
    pygame.CONTROLLER_BUTTON_Y: 3,
    pygame.CONTROLLER_BUTTON_LEFTSHOULDER: 4,
    pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: 5,
    pygame.CONTROLLER_BUTTON_BACK: 6,
    pygame.CONTROLLER_BUTTON_START: 7,
    pygame.CONTROLLER_BUTTON_LEFTSTICK: 10,   # L3 -> cycle focus (radial <-> circle)
    pygame.CONTROLLER_BUTTON_RIGHTSTICK: 8,   # R3 -> toggle circle mode
    pygame.CONTROLLER_BUTTON_DPAD_LEFT: 12,
    pygame.CONTROLLER_BUTTON_DPAD_RIGHT: 13,
    pygame.CONTROLLER_BUTTON_DPAD_UP: 14,
    pygame.CONTROLLER_BUTTON_DPAD_DOWN: 15,
    pygame.CONTROLLER_BUTTON_GUIDE: 6,
}

# DualSense raw (SDL joystick) indices -> logical indices
PS5_BUTTON_MAP = {
    0: 0,    # cross      -> A
    1: 1,    # circle     -> B
    2: 2,    # square     -> X
    3: 3,    # triangle   -> Y
    9: 4,    # L1         -> LB
    10: 5,   # R1         -> RB
    4: 6,    # share      -> back
    6: 7,    # options    -> start
    7: 10,   # L3         -> cycle focus (radial <-> circle)
    8: 8,    # R3         -> toggle circle mode
    11: 14,  # dpad up
    12: 15,  # dpad down
    13: 12,  # dpad left
    14: 13,  # dpad right
}

# Keyboard fallback: key -> logical button
KEYBOARD_MAP = {
    pygame.K_UP: 14,
    pygame.K_DOWN: 15,
    pygame.K_LEFT: 12,
    pygame.K_RIGHT: 13,
    pygame.K_a: 0,
    pygame.K_s: 1,
    pygame.K_d: 2,
    pygame.K_f: 3,
    pygame.K_q: 4,
    pygame.K_e: 8,
    pygame.K_z: 5,   # gate (also tap-record)
    pygame.K_x: 7,   # chord
    pygame.K_m: 6,
    pygame.K_c: 10,  # cycle focus (radial <-> circle)
    pygame.K_v: 8,   # toggle circle mode
}


class InputManager:
    def __init__(self):
        self.DEADZONE = 0.1
        self.mode = "keyboard"
        self.controller = None
        self.joy = None
        self.raw_button_map = None
        self._prev_buttons = set()
        self._prev_keys = set()

        if HAS_SDL2_CONTROLLER:
            try:
                sdl2controller.init()
                if sdl2controller.get_count() > 0:
                    self.controller = sdl2controller.Controller(0)
                    self.mode = "sdl"
            except Exception as e:
                print(f"[INPUT] SDL controller init failed: {e}")
                self.controller = None

        if self.mode != "sdl" and pygame.joystick.get_count() > 0:
            try:
                self.joy = pygame.joystick.Joystick(0)
                self.joy.init()
                name = self.joy.get_name().lower()
                if "dual" in name or "ps5" in name or "dualsense" in name:
                    self.raw_button_map = PS5_BUTTON_MAP
                self.num_buttons = self.joy.get_numbuttons()
                self.mode = "raw"
            except Exception as e:
                print(f"[INPUT] Joystick init failed: {e}")
                self.joy = None

        print(f"[INPUT] Controller mode: {self.mode} ({self._controller_name()})")

    def _controller_name(self):
        if self.mode == "sdl" and self.controller:
            try:
                return self.controller.as_joystick().get_name()
            except Exception:
                return "SDL controller"
        if self.mode == "raw" and self.joy:
            return self.joy.get_name()
        return "keyboard fallback"

    def _apply_deadzone(self, val):
        return 0.0 if abs(val) < self.DEADZONE else val

    def get_raw_buttons(self):
        """Logical button indices currently pressed."""
        pressed = set()

        if self.mode == "sdl" and self.controller:
            for raw, logical in SDL_BUTTON_MAP.items():
                if self.controller.get_button(raw):
                    pressed.add(logical)
            # Triggers are axes on gamepads: map them to momentary logical buttons
            # R2 -> gate + chord (play all voices), L2 -> chord (layering)
            if self.controller.get_axis(pygame.CONTROLLER_AXIS_TRIGGERRIGHT) > 16384:
                pressed.update((5, 7))
            if self.controller.get_axis(pygame.CONTROLLER_AXIS_TRIGGERLEFT) > 16384:
                pressed.add(7)

        elif self.mode == "raw" and self.joy:
            for i in range(self.num_buttons):
                if self.joy.get_button(i):
                    pressed.add(self.raw_button_map.get(i, i) if self.raw_button_map else i)
            if self.joy.get_axis(5) > 0.5:   # R2
                pressed.update((5, 7))
            if self.joy.get_axis(4) > 0.5:   # L2
                pressed.add(7)
            if self.joy.get_numhats() > 0:
                hat = self.joy.get_hat(0)
                if hat[0] == -1:
                    pressed.add(12)
                elif hat[0] == 1:
                    pressed.add(13)
                if hat[1] == 1:
                    pressed.add(14)
                elif hat[1] == -1:
                    pressed.add(15)

        return pressed

    def _get_axis(self, axis):
        if self.mode == "sdl" and self.controller:
            # SDL controller axes are raw int16 (-32768..32767); normalize to -1..1
            return self._apply_deadzone(self.controller.get_axis(axis) / 32768.0)
        if self.mode == "raw" and self.joy:
            return self._apply_deadzone(self.joy.get_axis(axis))
        return 0.0

    def get_left_stick(self):
        if self.mode == "sdl":
            return (self._get_axis(pygame.CONTROLLER_AXIS_LEFTX),
                    self._get_axis(pygame.CONTROLLER_AXIS_LEFTY))
        return (self._get_axis(0), self._get_axis(1))

    def get_right_stick(self):
        if self.mode == "sdl":
            return (self._get_axis(pygame.CONTROLLER_AXIS_RIGHTX),
                    self._get_axis(pygame.CONTROLLER_AXIS_RIGHTY))
        return (self._get_axis(2), self._get_axis(3))

    def _emit_edges(self, current, previous):
        for btn in current - previous:
            bus.emit("BUTTON_PRESSED", button=btn, value=True)
        for btn in previous - current:
            bus.emit("BUTTON_RELEASED", button=btn, value=False)

    def update(self):
        """Call once per frame. Emits button events and stick events."""
        if self.mode in ("sdl", "raw"):
            current = self.get_raw_buttons()
            self._emit_edges(current, self._prev_buttons)
            self._prev_buttons = current

        # Keyboard fallback (always active)
        keys_pressed = pygame.key.get_pressed()
        current_keys = {logical for key, logical in KEYBOARD_MAP.items() if keys_pressed[key]}
        self._emit_edges(current_keys, self._prev_keys)
        self._prev_keys = current_keys

        lx, ly = self.get_left_stick()
        rx, ry = self.get_right_stick()
        bus.emit("LEFT_STICK_UPDATED", x=lx, y=ly)
        bus.emit("RIGHT_STICK_UPDATED", x=rx, y=ry)
