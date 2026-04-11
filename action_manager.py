# action_manager.py
from event_bus import bus

class ActionManager:
    def __init__(self, cursor_controller, voice_manager):
        self.cursor = cursor_controller
        self.vm = voice_manager
        # Actions that should react to both press (value=True) and release (value=False)
        self.momentary_actions = {"gate", "chord"}
        bus.on("INVOKE_ACTION", self._on_action)

    def _on_action(self, action_id, value):
        if action_id == "move_cursor_up" and value:
            self.cursor.move_up()
        elif action_id == "move_cursor_down" and value:
            self.cursor.move_down()
        elif action_id == "gate":
            self.vm.set_gate(value)
        elif action_id == "chord":
            self.vm.set_chord(value)
        elif action_id == "jump_to_voice2" and value:
            self.vm.jump_cursor_to_voice(1)