# circle_of_fifths/circle_state.py
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class PulseInfo:
    """Information about a note that triggered a pulse animation."""
    pitch_class: int
    timestamp_ms: int

@dataclass
class CircleState:
    """All mutable state for the Circle of Fifths widget."""
    active_ring: str = "major"           # "major" or "minor"
    hovered_index: Optional[int] = None   # 0-11 or None
    exit_timer: int = 0                   # frames since last stick movement
    pulse: Optional[PulseInfo] = None     # current pulse effect data

    degree_mode: bool = False                # True = degree mode active
    selected_degree_index: Optional[int] = None
    # Animation state for radius changes (managed by view, but can be stored here if needed)
    # We'll keep animation state inside the view to avoid polluting the state model.
    # The view will have its own dictionaries for current/target radii and timers.

    # Configuration constants (can be overridden)
    EXIT_GRACE_FRAMES: int = 10   # frames of deadzone before selecting
    DEADZONE: float = 0.01         # stick magnitude threshold
    PULSE_DURATION_MS: int = 200   # milliseconds pulse lasts