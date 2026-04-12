# ui_components/scale_hud_controller.py
from event_bus import bus
from .scale_hud_state import ScaleHUDState

class ScaleHUDController:
    def __init__(self, initial_state: ScaleHUDState = None):
        self.state = initial_state or ScaleHUDState(root_note=60, mode="Major")
        bus.on("SCALE_CHANGED", self._on_scale_changed)
        bus.on("PENTATONIC_TOGGLED", self._on_pentatonic_toggled)

    def _on_scale_changed(self, legal_notes, root_note, mode):
        self.state.root_note = root_note
        self.state.mode = mode
        # legal_notes not needed for HUD, but we store root and mode

    def _on_pentatonic_toggled(self, active):
        self.state.pentatonic_active = active

    def get_state(self) -> ScaleHUDState:
        return self.state