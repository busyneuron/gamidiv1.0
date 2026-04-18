# action_manager.py
from event_bus import bus

class ActionManager:
    def __init__(self, cursor_controller, voice_manager, theory_engine, voice_editor=None):
        self.cursor = cursor_controller
        self.vm = voice_manager
        self.theory = theory_engine
        self.voice_editor = voice_editor
        self.momentary_actions = {"gate", "chord"}
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

        # Accidentals
        elif action_id == "sharpen_note" and value:
            cursor_note = self.cursor.cursor_note
            self.theory.modify_degree_by_note(cursor_note, 1)
        elif action_id == "flatten_note" and value:
            cursor_note = self.cursor.cursor_note
            self.theory.modify_degree_by_note(cursor_note, -1)
        elif action_id == "clear_accidentals" and value:
            self.theory.reset_accidentals()
            bus.emit("ADD_LOG", text="Cleared all accidentals", color=(200,200,100))

        # Add voice (existing)
        elif action_id == "add_voice_2nd" and value:
            self.vm.stack_new_voice(1)
        elif action_id == "add_voice_3rd" and value:
            self.vm.stack_new_voice(2)
        elif action_id == "add_voice_4th" and value:
            self.vm.stack_new_voice(3)
        elif action_id == "add_voice_5th" and value:
            self.vm.stack_new_voice(4)
        elif action_id == "add_voice_6th" and value:
            self.vm.stack_new_voice(5)
        elif action_id == "add_voice_7th" and value:
            self.vm.stack_new_voice(6)
        elif action_id == "add_voice_8ve" and value:
            self.vm.stack_new_voice(7)

        # Extensions (existing)
        elif action_id == "toggle_extension_6" and value:
            self.theory.toggle_extension(6)
        elif action_id == "toggle_extension_8" and value:
            self.theory.toggle_extension(8)
        elif action_id == "toggle_extension_10" and value:
            self.theory.toggle_extension(10)
        elif action_id == "toggle_extension_12" and value:
            self.theory.toggle_extension(12)
        elif action_id == "toggle_omit_third" and value:
            self.theory.toggle_omission(2)
        elif action_id == "toggle_omit_fifth" and value:
            self.theory.toggle_omission(4)

        # Mode setting (existing)
        elif action_id.startswith("set_mode_") and value:
            mode_name = action_id.replace("set_mode_", "").capitalize()
            self.theory.set_mode(mode_name)

        # ----- NEW VOICE EDITING ACTIONS -----
        elif action_id.startswith("select_voice_") and value and self.voice_editor:
            voice_id = int(action_id.split("_")[-1])
            self.voice_editor.select_voice(voice_id)
        elif action_id == "select_all_voices" and value and self.voice_editor:
            self.voice_editor.select_all_voices()
        elif action_id == "clear_selected_voices" and value and self.voice_editor:
            self.voice_editor.clear_selected_voices()
        elif action_id == "clear_all_voices" and value and self.voice_editor:
            self.voice_editor.clear_all_voices()
        elif action_id == "channel_up" and value and self.voice_editor:
            self.voice_editor.change_selected_voice_channel(1)
        elif action_id == "channel_down" and value and self.voice_editor:
            self.voice_editor.change_selected_voice_channel(-1)
        elif action_id.startswith("set_motif_preset_") and value and self.voice_editor:
            preset_name = action_id.replace("set_motif_preset_", "")
            self.voice_editor.set_selected_voice_motif(preset_name)
        
                # ----- Voice mode and sustain quantization -----
        elif action_id == "set_voice_mode_ostinato" and value and self.voice_editor:
            self.voice_editor.set_selected_voice_mode("ostinato")
        elif action_id == "set_voice_mode_sustain" and value and self.voice_editor:
            self.voice_editor.set_selected_voice_mode("sustain")
        elif action_id == "set_sustain_quant_quarter" and value and self.voice_editor:
            self.voice_editor.set_selected_voice_sustain_quantization(24)
        elif action_id == "set_sustain_quant_eighth" and value and self.voice_editor:
            self.voice_editor.set_selected_voice_sustain_quantization(12)


        # Momentary actions (held)
        elif action_id in self.momentary_actions:
            if action_id == "gate":
                self.vm.set_gate(value)
            elif action_id == "chord":
                self.vm.set_chord(value)

        # Fallback
        else:
            #print(f"Unknown action: {action_id}")
            pass