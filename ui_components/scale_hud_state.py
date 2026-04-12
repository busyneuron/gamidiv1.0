# ui_components/scale_hud_state.py
from dataclasses import dataclass

@dataclass
class ScaleHUDState:
    root_note: int          # MIDI note number (e.g., 60 for C4)
    mode: str               # full mode name: "Major", "Dorian", etc.
    pentatonic_active: bool = False