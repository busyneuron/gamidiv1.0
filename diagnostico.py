# diagnostico.py
"""Diagnostic tool: shows pygame version, controllers, MIDI ports.
Usage:
    python diagnostico.py          list environment
    python diagnostico.py --probe  show live button/axis events (15s)
"""
import sys
import time

import pygame

def main():
    pygame.init()

    print("=" * 60)
    print(f"pygame {pygame.version.ver} (SDL {pygame.get_sdl_version()})")
    print(f"Python {sys.version.split()[0]}")
    print("=" * 60)

    # MIDI ports
    try:
        import mido
        print("\n[MIDI OUTPUTS]")
        outputs = mido.get_output_names()
        for name in outputs:
            print(f"  OUT: {name}")
        if not outputs:
            print("  (ninguna)")
        print("[MIDI INPUTS]")
        inputs = mido.get_input_names()
        for name in inputs:
            print(f"  IN : {name}")
        if not inputs:
            print("  (ninguna)")
    except Exception as e:
        print(f"[MIDI] error: {e}")

    # Joysticks (raw)
    print("\n[JOYSTICKS (raw)]")
    count = pygame.joystick.get_count()
    print(f"  count={count}")
    for i in range(count):
        joy = pygame.joystick.Joystick(i)
        joy.init()
        print(f"  [{i}] {joy.get_name()} | axes={joy.get_numaxes()} buttons={joy.get_numbuttons()} hats={joy.get_numhats()}")

    # SDL2 game controllers
    try:
        from pygame._sdl2 import controller as sdl2controller
        sdl2controller.init()
        print("[GAME CONTROLLERS (SDL2)]")
        ccount = sdl2controller.get_count()
        print(f"  count={ccount}")
        for i in range(ccount):
            c = sdl2controller.Controller(i)
            try:
                name = c.as_joystick().get_name()
            except Exception:
                name = "SDL controller"
            print(f"  [{i}] {name}")
        if ccount == 0:
            print("  (ninguno)")
    except ImportError:
        print("[GAME CONTROLLERS] pygame._sdl2.controller no disponible")

    if "--probe" in sys.argv:
        print("\n[PROBE] Mueve sticks y pulsa botones durante 15 segundos...")
        from event_bus import bus
        from input_manager import InputManager

        mgr = InputManager()

        def on_button(button, value):
            state = "PRESS " if value else "RELEASE"
            print(f"  button {button:2d} {state}")

        def on_left(x, y):
            if abs(x) > 0.05 or abs(y) > 0.05:
                print(f"  LEFT  x={x:+.2f} y={y:+.2f}")

        def on_right(x, y):
            if abs(x) > 0.05 or abs(y) > 0.05:
                print(f"  RIGHT x={x:+.2f} y={y:+.2f}")

        bus.on("BUTTON_PRESSED", on_button)
        bus.on("BUTTON_RELEASED", on_button)
        bus.on("LEFT_STICK_UPDATED", on_left)
        bus.on("RIGHT_STICK_UPDATED", on_right)

        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            pygame.event.pump()
            mgr.update()
            time.sleep(0.016)

    pygame.quit()


if __name__ == "__main__":
    main()
