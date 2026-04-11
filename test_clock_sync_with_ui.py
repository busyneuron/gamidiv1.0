# test_clock_sync_with_ui.py
import pygame
import time
import mido
from event_bus import bus
from midi_manager import MidiManager
from voice import Voice
from voice_manager import VoiceManager
from theory_engine import TheoryEngine
from ui_components.keyboard import Keyboard
from ui_components.keyboard_state import KeyboardState
from ui_components.keyboard_controller import KeyboardController
from interface import GamidiInterface

def main():
    pygame.init()
    screen = pygame.display.set_mode((736, 736))
    ui = GamidiInterface(screen)

    # ---- Backend Setup ----
    theory = TheoryEngine(root_note=60, mode="Major")

    # MIDI ports
    input_name = "GAMIDI_SYNC"
    output_name = "Pypad"
    midi = MidiManager(input_name=input_name, output_name=output_name)

    bus.on("SEND_NOTE_ON", midi.send_note_on)
    bus.on("SEND_NOTE_OFF", midi.send_note_off)

    vm = VoiceManager()
    vm.set_gate(True)
    vm.set_chord(True)

    # Create lead voice (degree offset 0)
    voice = Voice(voice_id=0, event_bus=bus, theory_engine=theory,
                  degree_offset=0, octave_offset=0, channel=0)
    voice.set_motif([("quarter", "normal")])
    vm.add_voice(voice)

    voice2 = Voice(voice_id=1, event_bus=bus, theory_engine=theory,
                  degree_offset=2, octave_offset=0, channel=0)
    voice2.set_motif([("quarter rest", "normal"),("sixteenth", "normal"), ("sixteenth", "normal"), ("eighth rest", "normal"), ("eighth", "normal")])
    vm.add_voice(voice2)

    voice3 = Voice(voice_id=2, event_bus=bus, theory_engine=theory,
                  degree_offset=4, octave_offset=0, channel=0)
    voice3.set_motif([("eighth rest", ""), ("eighth", "normal")])
    vm.add_voice(voice3)

    # Initial UI state
    legal_notes = theory.get_legal_notes()
    initial_state = KeyboardState(
        current_note=vm.cursor_note,
        legal_notes=legal_notes,
        active_notes=set(),
        root_note=60,
        last_trigger_time={}
    )
    keyboard_ctrl = KeyboardController(initial_state)

    # ---- Main Loop ----
    clock = pygame.time.Clock()
    running = True

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        new_note = theory.get_next_note(vm.cursor_note, 1, jump=1, chromatic=False)
                        if new_note != vm.cursor_note:
                            vm.cursor_note = new_note
                            bus.emit("CURSOR_MOVED", new_note=new_note)
                    elif event.key == pygame.K_DOWN:
                        new_note = theory.get_next_note(vm.cursor_note, -1, jump=1, chromatic=False)
                        if new_note != vm.cursor_note:
                            vm.cursor_note = new_note
                            bus.emit("CURSOR_MOVED", new_note=new_note)
                    elif event.key == pygame.K_m:
                        # Toggle mode
                        new_mode = "Minor" if theory.mode == "Major" else "Major"
                        theory.set_mode(new_mode)
                        legal_notes = theory.get_legal_notes()
                        # Cursor note may need adjustment? We'll keep same absolute note; if it's not in new scale, voices will not play.
                        # Optionally, snap cursor to nearest legal note:
                        if vm.cursor_note not in legal_notes:
                            new_cursor = theory.get_next_note(vm.cursor_note, 0)  # finds nearest
                            vm.cursor_note = new_cursor
                            bus.emit("CURSOR_MOVED", new_note=new_cursor)
                        # No need to emit SCALE_CHANGED again because set_mode already does

            # Process incoming MIDI (clock)
            midi.process_incoming()

            

            # Update UI
            ui.draw(keyboard_ctrl.get_state())

            clock.tick(60)
            time.sleep(0.001)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        midi.close()
        pygame.quit()

if __name__ == "__main__":
    main()