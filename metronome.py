# metronome.py
from event_bus import bus


class Metronome:
    """MIDI clock slave.

    Converts incoming MIDI clock (24 PPQN) and transport messages into
    MASTER_TICK events. The master tick only advances while the transport is
    running, so stray clock messages (which some DAWs keep sending even while
    stopped, purely as a tempo reference) can't corrupt the pattern phase, and
    every fresh start begins at the downbeat (tick 0).
    """

    def __init__(self, ticks_per_bar=96):
        self.master_tick = 0
        self.ticks_per_bar = ticks_per_bar  # 24 PPQN * 4/4 = 96
        self.playing = False
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
        # Ignore MIDI clock unless the transport is running.
        if not self.playing:
            return
        self._emit_master_tick()
        self.master_tick += 1

    def _on_start(self):
        # A fresh start always begins at the downbeat (tick 0). Previously the
        # master tick was not reset here, so every pattern after a stop/restart
        # was phase-shifted by however many clock ticks had accumulated.
        self.master_tick = 0
        self.playing = True

    def _on_continue(self):
        # Resume from the current song position (set via SONG_POSITION).
        self.playing = True

    def _on_stop(self):
        self.playing = False

    def _on_song_position(self, pos):
        # Song Position Pointer is in 16th notes; 24 PPQN -> 6 ticks per 16th.
        self.master_tick = pos * 6
