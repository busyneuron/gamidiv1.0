# metronome.py
from event_bus import bus

class Metronome:
    def __init__(self, ticks_per_bar=96):
        self.master_tick = 0
        self.ticks_per_bar = ticks_per_bar  # 24 PPQN * 4/4 = 96
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

    def set_ticks_per_bar(self, ticks_per_bar):
        if ticks_per_bar > 0:
            self.ticks_per_bar = ticks_per_bar

    def _emit_master_tick(self):
        bar = self.master_tick // self.ticks_per_bar
        tick_in_bar = self.master_tick % self.ticks_per_bar
        bus.emit("MASTER_TICK", tick=self.master_tick,
                 bar=bar, tick_in_bar=tick_in_bar)

    def _on_clock_tick(self):
        # Preserve existing kickstart behavior (double-emit on very first tick)
        if not self._first_tick_received and not self.playing:
            self.playing = True
            self._emit_master_tick()
        self._first_tick_received = True

        self.master_tick += 1
        if self.playing:
            self._emit_master_tick()

    def _on_start(self):
        self.playing = True
        self.was_playing = False
        self._emit_master_tick()

    def _on_continue(self):
        self.playing = True
        self.was_playing = False
        self._emit_master_tick()

    def _on_stop(self):
        self.was_playing = self.playing
        self.playing = False

    def _on_song_position(self, pos):
        new_tick = pos * 6
        self.master_tick = new_tick
        if self.was_playing:
            self.playing = True
            self.was_playing = False
            self._emit_master_tick()
        elif self.playing:
            self._emit_master_tick()