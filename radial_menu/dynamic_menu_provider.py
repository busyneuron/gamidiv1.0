# dynamic_menu_provider.py
from radial_menu.rm_models import Menu, Gate, GateType

class DynamicMenuProvider:
    """Centralized provider for dynamic radial submenus."""
    
    def __init__(self, voice_manager=None, theory_engine=None):
        self.voice_manager = voice_manager
        self.theory_engine = theory_engine

    def get_menu(self, menu_id: str):
        if menu_id == "voices":
            return self._build_voice_menu()
        # Add more dynamic menus here later
        return None

    def _build_voice_menu(self):
        """Build a menu with up to 8 voice selection gates."""
        if not self.voice_manager:
            return None
        gates = {}
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        voices = list(self.voice_manager.voices.values())
        for i, voice in enumerate(voices[:8]):
            dir_key = directions[i]
            action_id = f"select_voice_{voice.id}"
            gate = Gate(
                label=f"V{voice.degree_offset}",
                color=(200, 200, 200),
                action_id=action_id,
                gate_type=GateType.ONE_SHOT
            )
            gates[dir_key] = gate
        if not gates:
            return None
        return Menu(name="select_voice", gates=gates)