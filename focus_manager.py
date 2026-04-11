# focus_manager.py
from event_bus import bus

class FocusManager:
    def __init__(self):
        self.modes = ["radial", "none"]  # add "circle", "fader" later
        self.current_index = 0
        bus.on("FOCUS_NEXT", self.next_mode)

    def next_mode(self):
        self.current_index = (self.current_index + 1) % len(self.modes)
        bus.emit("FOCUS_CHANGED", mode=self.current_mode)

    @property
    def current_mode(self):
        return self.modes[self.current_index]