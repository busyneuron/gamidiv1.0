# ui_components/keyboard_state.py
from dataclasses import dataclass, field
from typing import Set, Dict, Optional

@dataclass
class KeyboardState:
    current_note: int
    legal_notes: Set[int]
    active_notes: Set[int]
    root_note: int
    last_trigger_time: Dict[int, float] = field(default_factory=dict)
    reachable_notes: Optional[Set[int]] = None

    def __post_init__(self):
        self.root_pc = self.root_note % 12