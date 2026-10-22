# test_clock_sync_with_ui.py
import pygame
import os
from event_bus import bus
from midi_manager import MidiManager
from metronome import Metronome
from voice import Voice
from voice_manager import VoiceManager
from voice_editor import VoiceEditor                     # NEW
from radial_menu.dynamic_menu_provider import DynamicMenuProvider   # NEW
from theory_engine import TheoryEngine
from input_manager import InputManager
from axis_mapper import AxisMapper
from action_mapper import ActionMapper
from action_manager import ActionManager
from cursor_controller import CursorController
from focus_manager import FocusManager
from radial_menu.rm_controller import RadialMenuController
from radial_menu.rm_menus import root_menu
from ui_components.keyboard_state import KeyboardState
from ui_components.keyboard_controller import KeyboardController
from ui_components.piano_roll_state import PianoRollState
from ui_components.piano_roll_controller import PianoRollController
from ui_state import UIState
from interface import GamidiInterface
from ui_components.scale_hud_controller import ScaleHUDController
from ui_components.scale_hud_state import ScaleHUDState
from step_sequencer import StepSequencer

def main():
    os.environ['SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS'] = '1'
    
    pygame.init()
    screen = pygame.display.set_mode((736, 736))
    pygame.display.set_caption("GAMIDI Test")

    # ---- Backend Setup ----
    theory = TheoryEngine(root_note=60, mode="Major")

    input_name = "GAMIDI_SYNC"
    output_name = "Pypad"
    midi = MidiManager(input_name=input_name, output_name=output_name)

    bus.on("SEND_NOTE_ON", midi.send_note_on)
    bus.on("SEND_NOTE_OFF", midi.send_note_off)

    # ---- Metronome (Master Clock) ----
    metronome = Metronome()

    # ---- Cursor Controller ----
    cursor_ctrl = CursorController(theory, initial_note=60)
    vm = VoiceManager(theory)
    vm.cursor_note = cursor_ctrl.cursor_note

    # ---- Voice Editor (new) ----
    voice_editor = VoiceEditor(vm, theory)

    step_sequencer = StepSequencer(voice_editor, metronome)

    action_mgr = ActionManager(cursor_ctrl, vm, theory,
                               voice_editor=voice_editor,
                               sequencer=step_sequencer)

    # ---- Dynamic Menu Provider (new) ----
    menu_provider = DynamicMenuProvider(voice_manager=vm, theory_engine=theory)

    # ---- Radial Menu Controller (updated) ----
    radial_ctrl = RadialMenuController(root_menu, menu_provider=menu_provider)

    scale_hud_ctrl = ScaleHUDController(ScaleHUDState(root_note=60, mode="Major"))

    # ---- Input & Action System ----
    input_mgr = InputManager()
    axis_mapper = AxisMapper()
    action_mapper = ActionMapper()
    # ActionManager now receives voice_editor
    action_mgr = ActionManager(cursor_ctrl, vm, theory, voice_editor=voice_editor)

    # ---- Focus Manager ----
    focus_mgr = FocusManager()

    # ---- UI ----
    ui = GamidiInterface(screen, radial_ctrl, theory)

    # ---- UI Controllers ----
    legal_notes = theory.get_legal_notes()
    keyboard_state = KeyboardState(
        current_note=cursor_ctrl.cursor_note,
        legal_notes=legal_notes,
        active_notes=set(),
        root_note=60,
        last_trigger_time={}
    )
    
    keyboard_ctrl = KeyboardController(keyboard_state, theory)

    piano_roll_state = PianoRollState()
    piano_roll_ctrl = PianoRollController(piano_roll_state)

    ui_state = UIState(
        keyboard=keyboard_ctrl.get_state(),
        piano_roll=piano_roll_ctrl.get_state(),
        scale_hud=scale_hud_ctrl.get_state(),
        sequencer=step_sequencer.state
    )

    # ---- Main Loop ----
    clock = pygame.time.Clock()
    running = True

    bus.emit("ADD_LOG", text="Developed by busyneuron", color=(255,255,255))
    bus.emit("ADD_LOG", text="Welcome to GAMIDI v1.2 𝄞", color=(255,255,255))
    
    try:
        while running:
            pygame.event.pump()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            input_mgr.update()
            midi.process_incoming()
            ui.draw(ui_state)
            clock.tick(60)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        midi.close()
        pygame.quit()

if __name__ == "__main__":
    main()