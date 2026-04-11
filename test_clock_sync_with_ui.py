# test_clock_sync_with_ui.py
import pygame
import time
import mido
import os
from event_bus import bus
from midi_manager import MidiManager
from voice import Voice
from voice_manager import VoiceManager
from theory_engine import TheoryEngine
from input_manager import InputManager
from action_mapper import ActionMapper
from action_manager import ActionManager
from cursor_controller import CursorController
from ui_components.keyboard_state import KeyboardState
from ui_components.keyboard_controller import KeyboardController
from ui_components.piano_roll_state import PianoRollState
from ui_components.piano_roll_controller import PianoRollController
from ui_state import UIState
from interface import GamidiInterface

def main():
    # Allow joystick events when window not focused
    os.environ['SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS'] = '1'

    pygame.init()
    # Use RESIZABLE to allow window management; background events still work
    screen = pygame.display.set_mode((736, 736))
    pygame.display.set_caption("GAMIDI Test")
    ui = GamidiInterface(screen)

    # ---- Backend Setup ----
    theory = TheoryEngine(root_note=60, mode="Major")

    # MIDI ports
    input_name = "GAMIDI_SYNC"
    output_name = "Pypad"
    midi = MidiManager(input_name=input_name, output_name=output_name)

    bus.on("SEND_NOTE_ON", midi.send_note_on)
    bus.on("SEND_NOTE_OFF", midi.send_note_off)

    vm = VoiceManager(theory) 
    

    # Voices
    voice = Voice(voice_id=0, event_bus=bus, theory_engine=theory,
                  degree_offset=0, octave_offset=0, channel=0)
    voice.set_motif([("eighth", "normal"),("sixteenth", "normal"),("sixteenth", "normal")])
    vm.add_voice(voice)

    voice2 = Voice(voice_id=1, event_bus=bus, theory_engine=theory,
                   degree_offset=2, octave_offset=0, channel=0)
    voice2.set_motif([("quarter rest", "normal"), ("sixteenth", "normal"),
                      ("sixteenth", "normal"), ("eighth rest", "normal"),
                      ("eighth", "normal")])
    vm.add_voice(voice2)

    voice3 = Voice(voice_id=2, event_bus=bus, theory_engine=theory,
                   degree_offset=4, octave_offset=0, channel=0)
    voice3.set_motif([("eighth rest", ""), ("eighth", "normal")])
    vm.add_voice(voice3)

    # ---- Cursor Controller ----
    cursor_ctrl = CursorController(theory, initial_note=60)
    vm.cursor_note = cursor_ctrl.cursor_note

    # ---- Input & Action System ----
    input_mgr = InputManager()
    action_mapper = ActionMapper()
    action_mgr = ActionManager(cursor_ctrl, vm)

    # ---- UI Controllers ----
    legal_notes = theory.get_legal_notes()
    keyboard_state = KeyboardState(
        current_note=cursor_ctrl.cursor_note,
        legal_notes=legal_notes,
        active_notes=set(),
        root_note=60,
        last_trigger_time={}
    )
    keyboard_ctrl = KeyboardController(keyboard_state)

    piano_roll_state = PianoRollState()
    piano_roll_ctrl = PianoRollController(piano_roll_state)

    # Combine into UIState
    ui_state = UIState(keyboard=keyboard_ctrl.get_state(), piano_roll=piano_roll_ctrl.get_state())

    # ---- Main Loop ----
    clock = pygame.time.Clock()
    running = True

    try:
        while running:
            # Pump events to keep window responsive
            pygame.event.pump()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            input_mgr.update()
            midi.process_incoming()

            # Redraw UI with current state
            ui.draw(ui_state)

            clock.tick(60)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        midi.close()
        pygame.quit()

if __name__ == "__main__":
    main()