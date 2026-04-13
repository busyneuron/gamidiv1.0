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
        self.DEADZONE = 0.1   # increased for stability

    def _apply_deadzone(self, val):
        return 0.0 if abs(val) < self.DEADZONE else val

    def get_raw_buttons(self):
        pressed = set()
        for i in range(self.num_buttons):
            if self.joy.get_button(i):
                pressed.add(i)
        # hat to buttons (optional, keep if needed)
        hat = self.joy.get_hat(0)
        if hat[0] == -1: pressed.add(12)
        elif hat[0] == 1: pressed.add(13)
        if hat[1] == 1: pressed.add(14)
        elif hat[1] == -1: pressed.add(15)
        return pressed

    def get_axis(self, axis):
        return self._apply_deadzone(self.joy.get_axis(axis))

    def get_left_stick(self):
        """Return (x, y) for left stick, with deadzone applied."""
        return (self.get_axis(0), self.get_axis(1))

    def get_right_stick(self):
        """Return (x, y) for right stick, with deadzone applied."""
        return (self.get_axis(2), self.get_axis(3))

    def update(self):
        """Call once per frame. Emits button events and stick events."""
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

        # Emit combined stick events
        lx, ly = self.get_left_stick()
        rx, ry = self.get_right_stick()
        bus.emit("LEFT_STICK_UPDATED", x=lx, y=ly)
        bus.emit("RIGHT_STICK_UPDATED", x=rx, y=ry)