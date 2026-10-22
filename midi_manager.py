# midi_manager.py
import os
import mido
from event_bus import bus

DEFAULT_SYNTH_HINTS = ["wavetable", "gs wavetable", "microsoft gs"]


class MidiManager:
    def __init__(self, input_name=None, output_name=None):
        self.requested_input = os.environ.get("GAMIDI_MIDI_IN", input_name)
        self.requested_output = os.environ.get("GAMIDI_MIDI_OUT", output_name)
        self.output_port = None
        self.input_port = None
        self._warned_no_output = False
        self._warned_no_input = False
        self.open_ports()
        self._log_open_ports()

    # --- Port discovery ---
    @staticmethod
    def _find_port(name, port_list):
        if not name:
            return None
        for p in port_list:
            if name in p:
                return p
        return None

    @classmethod
    def _choose_output(cls, requested, output_names):
        port = cls._find_port(requested, output_names)
        if port:
            return port
        for hint in DEFAULT_SYNTH_HINTS:
            port = cls._find_port(hint, output_names)
            if port:
                return port
        return output_names[0] if output_names else None

    @classmethod
    def _choose_input(cls, requested, input_names):
        port = cls._find_port(requested, input_names)
        if port:
            return port
        return input_names[0] if input_names else None

    def open_ports(self):
        """Open the requested ports, falling back to any available device.
        Never raises: missing hardware just leaves the port as None."""
        try:
            output_names = mido.get_output_names()
        except Exception as e:
            print(f"[MIDI] Could not enumerate outputs: {e}")
            output_names = []
        try:
            input_names = mido.get_input_names()
        except Exception as e:
            print(f"[MIDI] Could not enumerate inputs: {e}")
            input_names = []

        if not self.output_port:
            chosen = self._choose_output(self.requested_output, output_names)
            if chosen:
                try:
                    self.output_port = mido.open_output(chosen)
                    print(f"[MIDI] Output: {chosen}")
                    bus.emit("ADD_LOG", text=f"[MIDI] OUT: {chosen}", color=(100, 200, 100))
                except Exception as e:
                    print(f"[MIDI] Could not open output '{chosen}': {e}")
            elif not self._warned_no_output:
                self._warned_no_output = True
                print("[MIDI] No MIDI output devices found (no sound).")

        if not self.input_port:
            chosen = self._choose_input(self.requested_input, input_names)
            if chosen:
                try:
                    self.input_port = mido.open_input(chosen)
                    print(f"[MIDI] Input: {chosen}")
                    bus.emit("ADD_LOG", text=f"[MIDI] IN: {chosen}", color=(100, 200, 100))
                except Exception as e:
                    print(f"[MIDI] Could not open input '{chosen}': {e}")
            elif not self._warned_no_input:
                self._warned_no_input = True
                print("[MIDI] No MIDI input devices found (using internal clock).")

    def retry_ports(self):
        """Call periodically to hot-plug ports that were missing at startup."""
        if self.input_port is None or self.output_port is None:
            self.open_ports()

    def _log_open_ports(self):
        if self.output_port:
            bus.emit("ADD_LOG", text=f"[MIDI] OUT: {self.output_port.name}", color=(100, 200, 100))
        else:
            bus.emit("ADD_LOG", text="[MIDI] No output device", color=(200, 100, 100))
        if self.input_port:
            bus.emit("ADD_LOG", text=f"[MIDI] IN: {self.input_port.name}", color=(100, 200, 100))
        else:
            bus.emit("ADD_LOG", text="[MIDI] No input device - internal clock", color=(200, 100, 100))

    # --- Sending ---
    def send_note_on(self, note, velocity, channel=0):
        if self.output_port:
            try:
                msg = mido.Message('note_on', note=note, velocity=velocity, channel=channel)
                self.output_port.send(msg)
            except Exception as e:
                print(f"[MIDI] note_on failed: {e}")
        bus.emit("NOTE_ON_SENT", note=note, velocity=velocity, channel=channel)

    def send_note_off(self, note, channel=0):
        if self.output_port:
            try:
                msg = mido.Message('note_off', note=note, velocity=0, channel=channel)
                self.output_port.send(msg)
            except Exception as e:
                print(f"[MIDI] note_off failed: {e}")
        bus.emit("NOTE_OFF_SENT", note=note, channel=channel)

    def panic(self):
        """Silence everything: note_off on all notes and channels."""
        if not self.output_port:
            return
        try:
            for channel in range(16):
                self.output_port.send(mido.Message('all_sound_off', channel=channel))
                self.output_port.send(mido.Message('all_notes_off', channel=channel))
        except Exception as e:
            print(f"[MIDI] panic failed: {e}")

    # --- Receiving ---
    def process_incoming(self):
        """Call this regularly in the main loop."""
        if not self.input_port:
            return
        for msg in self.input_port.iter_pending():
            if msg.type == 'clock':
                bus.emit("CLOCK_TICK")
            elif msg.type == 'start':
                bus.emit("TRANSPORT_START")
            elif msg.type == 'continue':
                bus.emit("TRANSPORT_CONTINUE")
            elif msg.type == 'stop':
                bus.emit("TRANSPORT_STOP")
            elif msg.type == "songpos":
                bus.emit("SONG_POSITION", pos=msg.pos)
            else:
                print(f"[MIDI IN] {msg.type} (data: {msg.dict() if hasattr(msg, 'dict') else msg})")

    def close(self):
        self.running = False
        self.panic()
        if self.input_port:
            try:
                self.input_port.close()
            except Exception:
                pass
        if self.output_port:
            try:
                self.output_port.close()
            except Exception:
                pass
