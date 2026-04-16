# metronome.py
from event_bus import bus

class Metronome:
    def __init__(self):
        self.master_tick = 0
        self.playing = False
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        bus.on("CLOCK_TICK", self._on_clock_tick)
        bus.on("TRANSPORT_START", self._on_start)
        bus.on("TRANSPORT_CONTINUE", self._on_continue)
        bus.on("TRANSPORT_STOP", self._on_stop)
        bus.on("SONG_POSITION", self._on_song_position)

    def _on_clock_tick(self):
        if self.playing:
            self.master_tick += 1
            bus.emit("MASTER_TICK", tick=self.master_tick)

    def _on_start(self):
        # Start from beginning: reset tick to 0
        self.master_tick = 0
        self.playing = True
        bus.emit("MASTER_TICK", tick=self.master_tick)

    def _on_continue(self):
        # Continue from current position
        self.playing = True
        bus.emit("MASTER_TICK", tick=self.master_tick)

    def _on_stop(self):
        self.playing = False
        # Do NOT reset tick; just stop advancing

    def _on_song_position(self, pos):
        # pos is the raw SPP value (0-16383)
        # Convert to ticks: 1 SPP = 6 MIDI clocks (since PPQN=24)
        new_tick = pos * 6
        self.master_tick = new_tick
        # Even if stopped, we reposition so that when continue is hit, it starts from correct place
        bus.emit("MASTER_TICK", tick=self.master_tick)