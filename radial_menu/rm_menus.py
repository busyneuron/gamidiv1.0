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


add_voice_menu = Menu(
    name="intervals",
    gates={
        "N":  Gate(label="2nd", color=(255,100,100), action_id="add_voice_2nd"),
        "NE": Gate(label="3rd", color=(255,100,100), action_id="add_voice_3rd"),
        "E":  Gate(label="4th", color=(255,100,100), action_id="add_voice_4th"),
        "SE": Gate(label="5th", color=(255,100,100), action_id="add_voice_5th"),
        "S":  Gate(label="6th", color=(255,100,100), action_id="add_voice_6th"),
        "SW": Gate(label="7th", color=(255,100,100), action_id="add_voice_7th"),
        "W":  Gate(label="8ve", color=(255,100,100), action_id="add_voice_8ve"),
        # You can add more directions if needed, e.g., "NW": ...
    }
)

extensions_menu = Menu(
    name="extensions",
    gates={
        "N":  Gate(label="7th", color=(255,100,100), action_id="toggle_extension_6"),
        "NE": Gate(label="9th/2nd", color=(255,100,100), action_id="toggle_extension_8"),
        "E":  Gate(label="11th/4th", color=(255,100,100), action_id="toggle_extension_10"),
        "SE": Gate(label="13th/6th", color=(255,100,100), action_id="toggle_extension_12"),
        "SW": Gate(label="no3", color=(255,100,100), action_id="toggle_omit_third"),
        "W":  Gate(label="no5", color=(255,100,100), action_id="toggle_omit_fifth"),
    }
)

scale_menu = Menu(
    name="scale",
    gates={
        "N":  Gate(label="SHARP", color=(255,180,50), action_id="sharpen_note"),
        "NE": Gate(label="FLAT",  color=(50,200,255), action_id="flatten_note"),
        "E":  Gate(label="CLEAR", color=(200,200,100), action_id="clear_accidentals"),
        
    }
)

# Root menu
root_menu = Menu(
    name="root",
    gates={
        "W": Gate(label="GATE", color=(0, 255, 100), action_id="toggle_gate", gate_type=GateType.TOGGLE),
        "E": Gate(label="MODES", color=(0, 180, 255), sub_menu=modes_menu),
        "S": Gate(label="EXT", color=(255,100,100), sub_menu=extensions_menu),
        "N": Gate(label="SCALE", color=(255,180,50), sub_menu=scale_menu),
        "NW":Gate(label="ADD", color=(255,180,50), sub_menu=add_voice_menu ),
    }
)



