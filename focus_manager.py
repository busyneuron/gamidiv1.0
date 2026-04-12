# focus_manager.py
from enum import Enum
from event_bus import bus

class FocusMode(Enum):
    RADIAL = "radial"
    CIRCLE = "circle"
    FADER = "fader"
    NONE = "none"

class FocusManager:
    def __init__(self):
        self.modes = [FocusMode.RADIAL, FocusMode.CIRCLE, FocusMode.FADER, FocusMode.NONE]
        self.current_index = 0  # RADIAL
        self.current_mode = self.modes[self.current_index]

        bus.on("BUTTON_PRESSED", self._on_button_pressed)

    def _on_button_pressed(self, button: int, value: bool):
        if button == 10 and value:
            self.cycle_mode()

    def cycle_mode(self):
        self.current_index = (self.current_index + 1) % len(self.modes)
        self.current_mode = self.modes[self.current_index]
        bus.emit("FOCUS_CHANGED", mode=self.current_mode.value)  # emit string value

    def set_mode(self, mode: FocusMode):
        if mode in self.modes:
            self.current_mode = mode
            self.current_index = self.modes.index(mode)
            bus.emit("FOCUS_CHANGED", mode=self.current_mode.value)

    def is_active(self, mode: FocusMode) -> bool:
        return self.current_mode == mode