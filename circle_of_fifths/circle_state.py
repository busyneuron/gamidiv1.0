from dataclasses import dataclass
from typing import Optional

# Constants for note names and pitch classes
MAJOR_NOTES = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
MAJOR_PITCHES = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5]
MINOR_NAMES = ["a", "e", "b", "f#", "db", "ab", "eb", "bb", "f", "c", "g", "d"]
MINOR_PITCHES = [(p - 3) % 12 for p in MAJOR_PITCHES]

@dataclass
class CircleState:
    active_ring: str = "major"          # "major" or "minor"
    hovered_index: Optional[int] = None
    exit_timer: int = 0
    degree_mode: bool = False
    selected_index: Optional[int] = None   # index of selected gate (0-11), shared by both modes

    EXIT_GRACE_FRAMES: int = 10
    DEADZONE: float = 0.01