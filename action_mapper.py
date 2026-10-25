# action_mapper.py
from event_bus import bus

class ActionMapper:
    def __init__(self):
        self.button_map = {
            14: "move_cursor_up",
            15: "move_cursor_down",
            12: "seq_cursor_left",   # NEW
            13: "seq_cursor_right",
            5: "gate",
            7: "chord",
            6: "radial_menu_back",
            4: "toggle_circle_ring",
            8: "toggle_circle_mode",
            
            0: "jump_interval_3",   # X button
            1: "jump_interval_4",   # Circle
            2: "jump_interval_5",   # Triangle
            3: "jump_interval_6",   # Square
        }
        bus.on("BUTTON_PRESSED", self._on_button_event)
        bus.on("BUTTON_RELEASED", self._on_button_event)

    def _on_button_event(self, button, value):
        if button in self.button_map:
            bus.emit("INVOKE_ACTION", action_id=self.button_map[button], value=value)