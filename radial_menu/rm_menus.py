# radial_menu/rm_menus.py
from .rm_models import Menu, Gate, GateType

# Create a submenu with two gates
test_submenu = Menu(
    name="test_sub",
    gates={
        "N": Gate(
            label="TEST 1",
            color=(255, 200, 100),
            action_id="test_action_1",
            gate_type=GateType.ONE_SHOT,
            description="Test action 1"
        ),
        "S": Gate(
            label="TEST 2",
            color=(255, 200, 100),
            action_id="test_action_2",
            gate_type=GateType.ONE_SHOT,
            description="Test action 2"
        ),
    }
)

# Root menu with GATE on west and submenu on north
root_menu = Menu(
    name="root",
    gates={
        "W": Gate(
            label="GATE",
            color=(0, 255, 100),
            action_id="toggle_gate",
            gate_type=GateType.TOGGLE,
            description="Toggle gate on/off"
        ),
        "N": Gate(
            label="SUB",
            color=(255, 100, 100),
            sub_menu=test_submenu,
            description="Enter test submenu"
        ),
    }
)