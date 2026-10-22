# ui_state.py
from dataclasses import dataclass
from ui_components.keyboard_state import KeyboardState
from ui_components.piano_roll_state import PianoRollState
from ui_components.scale_hud_state import ScaleHUDState
from step_sequencer import SequencerState

@dataclass
class UIState:
    keyboard: KeyboardState
    piano_roll: PianoRollState
    scale_hud: ScaleHUDState
    sequencer: SequencerState