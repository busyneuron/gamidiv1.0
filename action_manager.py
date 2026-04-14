# action_manager.py
from event_bus import bus

class ActionManager:
    def __init__(self, cursor_controller, voice_manager, theory_engine):
        self.cursor = cursor_controller
        self.vm = voice_manager
        self.theory = theory_engine
        self.momentary_actions = {"gate", "chord"}  # add others as needed
        bus.on("INVOKE_ACTION", self._on_action)
        

    def _on_action(self, action_id, value):
        # Cursor movement
        if action_id == "move_cursor_up" and value:
            self.cursor.move_up()
        elif action_id == "move_cursor_down" and value:
            self.cursor.move_down()

        # Toggle actions
        elif action_id == "toggle_gate" and value:
            self.vm.set_gate(not self.vm.gate)
            
        elif action_id == "toggle_chord" and value:
            self.vm.set_chord(not self.vm.chord)
            
        
        elif action_id == "toggle_circle_mode" and value:
            bus.emit("TOGGLE_CIRCLE_MODE")

        elif action_id == "toggle_circle_ring" and value:
            bus.emit("TOGGLE_CIRCLE_RING")


        # In _on_action method, add:

        elif action_id == "sharpen_note" and value:
            cursor_note = self.cursor.cursor_note  
            self.theory.modify_degree_by_note(cursor_note, 1)
            

        elif action_id == "flatten_note" and value:
            cursor_note = self.cursor.cursor_note
            self.theory.modify_degree_by_note(cursor_note, -1)
            

        elif action_id == "clear_accidentals" and value:
            self.theory.reset_accidentals()
            bus.emit("ADD_LOG", text="Cleared all accidentals", color=(200,200,100))

        #extensions
        elif action_id == "toggle_extension_6" and value:
            self.theory.toggle_extension(6)
        elif action_id == "toggle_extension_8" and value:
            self.theory.toggle_extension(8)
        elif action_id == "toggle_extension_10" and value:
            self.theory.toggle_extension(10)
        elif action_id == "toggle_extension_12" and value:
            self.theory.toggle_extension(12)
        elif action_id == "toggle_omit_third" and value:
            self.theory.toggle_omission(2)   # interval 2 = third
        elif action_id == "toggle_omit_fifth" and value:
            self.theory.toggle_omission(4)   # interval 4 = fifth

        # Mode setting
        elif action_id.startswith("set_mode_") and value:
            mode_name = action_id.replace("set_mode_", "").capitalize()
            self.theory.set_mode(mode_name)
            

        # Momentary actions (held)
        elif action_id in self.momentary_actions:
            if action_id == "gate":
                self.vm.set_gate(value)
                
            elif action_id == "chord":
                self.vm.set_chord(value)

        # Fallback for unknown actions
        else:
            print(f"Unknown action: {action_id}")