# step_sequencer.py
from dataclasses import dataclass, field
from typing import List, Optional
from event_bus import bus
from rhythm_engine import MotifStep

@dataclass
class Step:
    active: bool = False
    duration_steps: int = 1  # How many 16th steps this note lasts

@dataclass
class SequencerState:
    total_steps: int = 16
    start_tick: int = 0
    steps: List[Step] = field(default_factory=lambda: [Step() for _ in range(16)])
    current_step: int = 0
    is_recording: bool = False
    target_voice_id: Optional[int] = None

class StepSequencer:
    def __init__(self, voice_editor, metronome):
        self.voice_editor = voice_editor
        self.metronome = metronome
        self.state = SequencerState()
        
        self._press_tick = 0
        self._active_tap = False
        
        bus.on("MASTER_TICK", self._on_master_tick)
        bus.on("BUTTON_PRESSED", self._on_button)
        bus.on("BUTTON_RELEASED", self._on_button)

    def start_recording(self, length_bars: float):
        # 1 bar = 16 steps (16th notes)
        self.state.total_steps = int(16 * length_bars)
        self.state.start_tick = self.metronome.master_tick
        self.state.steps = [Step() for _ in range(self.state.total_steps)]
        self.state.is_recording = True
        self._active_tap = False
        
        # Pick target voice
        selected = self.voice_editor.get_selected_ids()
        if selected:
            self.state.target_voice_id = list(selected)[0]
        elif len(self.voice_editor.vm.voices) == 1:
            self.state.target_voice_id = list(self.voice_editor.vm.voices.keys())[0]
        else:
            self.state.target_voice_id = None
            bus.emit("ADD_LOG", text="[SEQ] No voice selected!", color=(255, 100, 100))
            self.state.is_recording = False
            return
            
        bus.emit("ADD_LOG", text=f"[SEQ] Recording {length_bars} bar(s)...", color=(255, 100, 100))

    def stop_recording(self):
        self.state.is_recording = False
        bus.emit("ADD_LOG", text="[SEQ] Recording stopped", color=(200, 200, 100))

    def clear(self):
        self.state.is_recording = False
        self.state.steps = [Step() for _ in range(self.state.total_steps)]
        self._push_to_voice()
        bus.emit("ADD_LOG", text="[SEQ] Cleared", color=(200, 100, 100))

    def _on_master_tick(self, tick, **kwargs):
        elapsed = max(0, tick - self.state.start_tick)
        self.state.current_step = (elapsed // 6) % self.state.total_steps

    def _on_button(self, button, value):
        if not self.state.is_recording or button != 5:
            return
            
        tick = self.metronome.master_tick
        if value: # Press
            self._press_tick = tick
            self._active_tap = True
        elif self._active_tap: # Release
            self._active_tap = False
            self._commit_note(self._press_tick, tick)

    def _commit_note(self, press_tick, release_tick):
        # Calculate which step was hit
        elapsed = max(0, press_tick - self.state.start_tick)
        step_idx = (elapsed // 6) % self.state.total_steps
        
        # Calculate duration in steps (minimum 1 step)
        held_ticks = max(1, release_tick - press_tick)
        held_steps = max(1, round(held_ticks / 6))
        held_steps = min(held_steps, self.state.total_steps - step_idx)

        # Clear or trim overlapping notes
        for i in range(self.state.total_steps):
            if not self.state.steps[i].active:
                continue
            note_end = i + self.state.steps[i].duration_steps
            new_end = step_idx + held_steps
            
            if i < new_end and note_end > step_idx:
                # Overlap! Trim or remove.
                if i < step_idx:
                    # Starts before new note, trim its end
                    self.state.steps[i].duration_steps = step_idx - i
                else:
                    # Starts inside or after, remove it
                    self.state.steps[i].active = False

        # Write the new note
        self.state.steps[step_idx].active = True
        self.state.steps[step_idx].duration_steps = held_steps
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
                dur = step.duration_steps * 6
                motif.append(MotifStep(total_ticks=dur, gate_ticks=int(dur * 0.85), is_rest=False))
                i += step.duration_steps
            else:
                rest_ticks = 6
                i += 1
                while i < self.state.total_steps and not self.state.steps[i].active:
                    rest_ticks += 6
                    i += 1
                motif.append(MotifStep(total_ticks=rest_ticks, gate_ticks=0, is_rest=True))
                
        voice.set_motif(motif)