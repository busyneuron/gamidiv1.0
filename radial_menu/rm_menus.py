# radial_menu/rm_menus.py
from .rm_models import Menu, Gate, GateType

# Modes submenu
modes_menu = Menu(
    name="modes",
    gates={
        "N": Gate(label="DOR", color=(0, 180, 255), action_id="set_mode_dorian", gate_type=GateType.ONE_SHOT),
        "NE": Gate(label="PHR", color=(0, 180, 255), action_id="set_mode_phrygian", gate_type=GateType.ONE_SHOT),
        "NW": Gate(label="LYD", color=(0, 180, 255), action_id="set_mode_lydian", gate_type=GateType.ONE_SHOT),
        "SE": Gate(label="MIX", color=(0, 180, 255), action_id="set_mode_mixolydian", gate_type=GateType.ONE_SHOT),
        "S": Gate(label="MIN", color=(0, 180, 255), action_id="set_mode_minor", gate_type=GateType.ONE_SHOT),
        "SW": Gate(label="LOC", color=(0, 180, 255), action_id="set_mode_locrian", gate_type=GateType.ONE_SHOT),
        "W": Gate(label="MAJ", color=(0, 180, 255), action_id="set_mode_major", gate_type=GateType.ONE_SHOT),
        
    }
)

# Root menu
root_menu = Menu(
    name="root",
    gates={
        "W": Gate(label="GATE", color=(0, 255, 100), action_id="toggle_gate", gate_type=GateType.TOGGLE),
        "E": Gate(label="MODES", color=(0, 180, 255), sub_menu=modes_menu),
    }
)