# action_mapper.py
from event_bus import bus

class ActionMapper:
    def __init__(self):
        self.button_map = {
            14: "move_cursor_up",
            15: "move_cursor_down",
            5: "gate",
            7: "chord",
        }
        bus.on("BUTTON_PRESSED", self._on_button_event)
        bus.on("BUTTON_RELEASED", self._on_button_event)

    def _on_button_event(self, button, value):
        if button in self.button_map:
            bus.emit("INVOKE_ACTION", action_id=self.button_map[button], value=value)