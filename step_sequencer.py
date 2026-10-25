# step_sequencer.py
from dataclasses import dataclass, field
from typing import List, Optional
from event_bus import bus
from rhythm_engine import MotifStep

@dataclass
class Step:
    active: bool = False
    tie: bool = False   # tied to the previous step (same sustained note)

@dataclass
class SequencerState:
    total_steps: int = 16
    start_tick: int = 0
    steps: List[Step] = field(default_factory=lambda: [Step() for _ in range(16)])
    playhead_step: int = 0
    edit_step: int = 0
    is_editing: bool = False
    target_voice_id: Optional[int] = None

class StepSequencer:
    def __init__(self, voice_editor, metronome):
        self.voice_editor = voice_editor
        self.metronome = metronome
        self.state = SequencerState()
        
        self._paint_mode = False
        self._paint_value = True
        
        bus.on("MASTER_TICK", self._on_master_tick)
        bus.on("BUTTON_PRESSED", self._on_button)
        bus.on("BUTTON_RELEASED", self._on_button)

    def start_editing(self, length_bars: float):
        self.state.total_steps = int(16 * length_bars)
        
        bar_len = self.metronome.ticks_per_bar
        current_tick = self.metronome.master_tick
        self.state.start_tick = (current_tick // bar_len) * bar_len
        
        self.state.steps = [Step() for _ in range(self.state.total_steps)]
        self.state.is_editing = True
        self.state.edit_step = 0
        self._paint_mode = False
        
        # Pick target voice
        selected = self.voice_editor.get_selected_ids()
        if selected:
            self.state.target_voice_id = list(selected)[0]
        elif len(self.voice_editor.vm.voices) == 1:
            self.state.target_voice_id = list(self.voice_editor.vm.voices.keys())[0]
        else:
            self.state.target_voice_id = None
            bus.emit("ADD_LOG", text="[SEQ] No voice selected!", color=(255, 100, 100))
            self.state.is_editing = False
            return
            
        bus.emit("ADD_LOG", text=f"[SEQ] Editing {length_bars} bar(s)...", color=(255, 100, 100))
        if self.state.target_voice_id is not None:
            v = self.voice_editor.vm.voices.get(self.state.target_voice_id)
            if v: v.ignore_gate = True
        self._push_to_voice()

    def stop_editing(self):
        self.state.is_editing = False
        bus.emit("ADD_LOG", text="[SEQ] Editing stopped", color=(200, 200, 100))
        if self.state.target_voice_id is not None:
            v = self.voice_editor.vm.voices.get(self.state.target_voice_id)
            if v: v.ignore_gate = False

    def clear(self):
        self.state.steps = [Step() for _ in range(self.state.total_steps)]
        self._push_to_voice()
        bus.emit("ADD_LOG", text="[SEQ] Cleared", color=(200, 100, 100))

    def move_cursor(self, direction: int):
        if not self.state.is_editing:
            return
        self.state.edit_step = (self.state.edit_step + direction) % self.state.total_steps
        # If holding gate, paint the steps as we move
        if self._paint_mode:
            self._paint_step(self.state.edit_step, self._paint_value)
            self._push_to_voice()

    def _paint_step(self, idx, value):
        """Set a step's on/off state (used while painting with gate held)."""
        step = self.state.steps[idx]
        if value:
            step.active = True
            step.tie = (idx > 0 and self.state.steps[idx - 1].active)
        else:
            step.active = False
            step.tie = False

    def _on_master_tick(self, tick, **kwargs):
        elapsed = max(0, tick - self.state.start_tick)
        self.state.playhead_step = round(elapsed / 6) % self.state.total_steps

    def _on_button(self, button, value):
        if not self.state.is_editing or button != 5:
            return

        if value: # Press
            self._paint_mode = True
            self._cycle_step(self.state.edit_step)
            self._paint_value = self.state.steps[self.state.edit_step].active
        else: # Release
            self._paint_mode = False

    def _cycle_step(self, idx):
        """Cycle a step: off -> on (tied to previous) -> detached -> off."""
        step = self.state.steps[idx]
        if not step.active:
            step.active = True
            step.tie = (idx > 0 and self.state.steps[idx - 1].active)
        elif step.tie:
            step.tie = False   # detach from the previous note
        else:
            step.active = False
            step.tie = False   # off
        self._push_to_voice()

    def _push_to_voice(self):
        if self.state.target_voice_id is None:
            return
        voice = self.voice_editor.vm.voices.get(self.state.target_voice_id)
        if not voice:
            return

        motif = []
        i = 0
        while i < self.state.total_steps:
            step = self.state.steps[i]
            if step.active:
                dur = 6
                i += 1
                while (i < self.state.total_steps and self.state.steps[i].active
                       and self.state.steps[i].tie):
                    dur += 6
                    i += 1
                motif.append(MotifStep(total_ticks=dur, gate_ticks=int(dur * 0.85), is_rest=False))
            else:
                rest_ticks = 6
                i += 1
                while i < self.state.total_steps and not self.state.steps[i].active:
                    rest_ticks += 6
                    i += 1
                motif.append(MotifStep(total_ticks=rest_ticks, gate_ticks=0, is_rest=True))
                
        voice.set_motif(motif)