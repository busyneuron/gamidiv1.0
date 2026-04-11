# input_manager.py
import pygame
from event_bus import bus

class InputManager:
    def __init__(self):
        if pygame.joystick.get_count() == 0:
            print("No joystick found!")
            return
        self.joy = pygame.joystick.Joystick(0)
        self.joy.init()
        self.num_buttons = self.joy.get_numbuttons()
        self.DEADZONE = 0.01

    def _apply_deadzone(self, val, threshold=None):
        if threshold is None:
            threshold = self.DEADZONE
        return 0.0 if abs(val) < threshold else val

    def get_raw_buttons(self):
        """Return set of currently pressed button indices."""
        pressed = set()
        for i in range(self.num_buttons):
            if self.joy.get_button(i):
                pressed.add(i)
        # Convert hat to buttons 12-15
        hat = self.joy.get_hat(0)
        if hat[0] == -1: pressed.add(12)
        elif hat[0] == 1: pressed.add(13)
        if hat[1] == 1: pressed.add(14)
        elif hat[1] == -1: pressed.add(15)
        return pressed

    def get_axis(self, axis):
        return self._apply_deadzone(self.joy.get_axis(axis))

    # input_manager.py (update the update method)
    def update(self):
        """Poll and emit events for button presses/releases."""
        current = self.get_raw_buttons()
        if not hasattr(self, '_prev_buttons'):
            self._prev_buttons = set()
        pressed = current - self._prev_buttons
        released = self._prev_buttons - current
        for btn in pressed:
            bus.emit("BUTTON_PRESSED", button=btn, value=True)
        for btn in released:
            bus.emit("BUTTON_RELEASED", button=btn, value=False)
        self._prev_buttons = current