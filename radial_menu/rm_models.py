# radial_menu/rm_models.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum

class GateType(Enum):
    ONE_SHOT = "one_shot"
    TOGGLE = "toggle"
    # MOMENTARY = "momentary"  # future

@dataclass
class Gate:
    label: str
    color: tuple  # (r,g,b)
    action_id: Optional[str] = None
    sub_menu: Optional['Menu'] = None
    gate_type: GateType = GateType.ONE_SHOT
    description: str = ""

@dataclass
class Menu:
    name: str
    gates: Dict[str, Gate]  # direction string -> Gate
    # directions are fixed: "N", "NE", "E", "SE", "S", "SW", "W", "NW"

@dataclass
class RadialState:
    stack: List[Menu] = field(default_factory=list)
    hovered_direction: Optional[str] = None
    entry_timer: int = 0           # frames hovered on submenu gate
    exit_timer: int = 0            # frames in deadzone after hover
    deadzone_timer: int = 0        # frames in deadzone (for pop)
    pending_entry_gate: Optional[str] = None  # gate that started entry grace

    # configuration (can be moved to controller)
    entry_grace_frames: int = 120   # ~2 seconds at 60 fps
    exit_grace_frames: int = 30     # ~0.5 seconds
    deadzone_grace_frames: int = 60 # ~1 second
    gate_threshold: float = 0.5     # minimum stick magnitude to consider hover