# midi_manager.py
import mido
import threading
from event_bus import bus

class MidiManager:
    def __init__(self, input_name=None, output_name=None):
        def find_port(name, port_list):
            for p in port_list:
                if name in p:
                    return p
            return None

        try:
            self.output_port = mido.open_output(find_port(output_name, mido.get_output_names()))
            self.input_port = mido.open_input(find_port(input_name, mido.get_input_names()))
        except Exception as e:
            print(f"MIDI Error: {e}")
            exit()

    def send_note_on(self, note, velocity, channel=0):
        if self.output_port:
            msg = mido.Message('note_on', note=note, velocity=velocity, channel=channel)
            self.output_port.send(msg)
        bus.emit("NOTE_ON_SENT", note=note, velocity=velocity, channel=channel)

    def send_note_off(self, note, channel=0):
        if self.output_port:
            msg = mido.Message('note_off', note=note, velocity=0, channel=channel)
            self.output_port.send(msg)
        bus.emit("NOTE_OFF_SENT", note=note, channel=channel)

    def process_incoming(self):
        """Call this regularly in the main loop."""
        if not self.input_port:
            return
        for msg in self.input_port.iter_pending():
            if msg.type == 'clock':
                bus.emit("CLOCK_TICK")
            elif msg.type in ('start', 'continue'):
                bus.emit("CLOCK_RESET")
            # You can handle other messages later

    def close(self):
        self.running = False
        if self.input_port:
            self.input_port.close()
        if self.output_port:
            self.output_port.close()