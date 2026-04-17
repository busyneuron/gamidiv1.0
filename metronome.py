# metronome.py
from event_bus import bus

class Metronome:
    def __init__(self):
        self.master_tick = 0
        self.playing = False
        self.was_playing = False
        self._first_tick_received = False
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        bus.on("CLOCK_TICK", self._on_clock_tick)
        bus.on("TRANSPORT_START", self._on_start)
        bus.on("TRANSPORT_CONTINUE", self._on_continue)
        bus.on("TRANSPORT_STOP", self._on_stop)
        bus.on("SONG_POSITION", self._on_song_position)

    def _on_clock_tick(self):
        # Auto-start on first tick if not already playing
        if not self._first_tick_received and not self.playing:
            self.playing = True
            bus.emit("MASTER_TICK", tick=self.master_tick)
        self._first_tick_received = True

        self.master_tick += 1
        if self.playing:
            bus.emit("MASTER_TICK", tick=self.master_tick)

    def _on_start(self):
        self.playing = True
        self.was_playing = False
        bus.emit("MASTER_TICK", tick=self.master_tick)

    def _on_continue(self):
        self.playing = True
        self.was_playing = False
        bus.emit("MASTER_TICK", tick=self.master_tick)

    def _on_stop(self):
        self.was_playing = self.playing
        self.playing = False

    def _on_song_position(self, pos):
        new_tick = pos * 6
        self.master_tick = new_tick
        if self.was_playing:
            self.playing = True
            self.was_playing = False
            bus.emit("MASTER_TICK", tick=self.master_tick)
        elif self.playing:
            bus.emit("MASTER_TICK", tick=self.master_tick)