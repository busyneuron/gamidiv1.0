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

    # Connect MIDI manager to send notes
    bus.on("SEND_NOTE_ON", midi.send_note_on)
    bus.on("SEND_NOTE_OFF", midi.send_note_off)

    # Voice manager
    vm = VoiceManager()
    vm.set_gate(True)
    vm.set_chord(True)

    # Create a voice (lead voice) playing quarter notes
    voice = Voice(voice_id=0, event_bus=bus, theory_engine=theory,
                  degree_offset=0, octave_offset=0, channel=0)
    voice.set_motif([("quarter", "normal")])
    vm.add_voice(voice)

    voice2 = Voice(voice_id=1, event_bus=bus, theory_engine=theory,
                  degree_offset=2, octave_offset=0, channel=0)
    voice2.set_motif([("eighth rest", ""), ("eighth", "normal"), ("eighth", "normal")])
    vm.add_voice(voice2)

    # ---- UI State Controller ----
    # Initial legal notes: all notes in C major scale from C4 to B5
    legal_notes = theory.get_legal_notes()
    initial_state = KeyboardState(
        current_note=theory.get_cursor_midi_pitch(),
        legal_notes=legal_notes,
        active_notes=set(),
        root_note=60,
        last_trigger_time={}
    )

    initial_state = KeyboardState(
        current_note=theory.get_cursor_midi_pitch(),
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
            # Process pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        theory.move_cursor(1)          # move up one degree
                        new_note = theory.get_cursor_midi_pitch()
                        bus.emit("CURSOR_MOVED", new_note=new_note)
                    elif event.key == pygame.K_DOWN:
                        theory.move_cursor(-1)         # move down one degree
                        new_note = theory.get_cursor_midi_pitch()
                        bus.emit("CURSOR_MOVED", new_note=new_note)
                # Inside the main loop, after processing other events:
                    elif event.key == pygame.K_m:
                        new_mode = "Minor" if theory.mode == "Major" else "Major"
                        theory.set_mode(new_mode)
                        legal_notes = theory.get_legal_notes()
                        new_cursor_note = theory.get_cursor_midi_pitch()
                        bus.emit("SCALE_CHANGED", legal_notes=legal_notes, root_note=theory.root_note, mode=new_mode)
                        bus.emit("CURSOR_MOVED", new_note=new_cursor_note)   # <-- add this
                        print(f"Switched to {new_mode} mode, cursor now at {new_cursor_note}")

            # Process incoming MIDI (clock)
            midi.process_incoming()

            # Update UI at 60 FPS
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