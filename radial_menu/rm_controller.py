# radial_menu/rm_controller.py
import math
from event_bus import bus
from .rm_models import RadialState, Menu, Gate, GateType

class RadialMenuController:
    # radial_menu/rm_controller.py
    def __init__(self, root_menu: Menu):
        self.state = RadialState(stack=[root_menu])
        self.state.entry_grace_frames = 15   # 0.5 seconds at 60 fps
        self.state.exit_grace_frames = 65
        self.state.deadzone_grace_frames = 30
        self.axes = {"radial_menu_x": 0.0, "radial_menu_y": 0.0}
        self._active = True
        bus.on("AXIS_MOVED", self._on_axis_moved)
        bus.on("FOCUS_CHANGED", self._on_focus_changed)
        self.active_gates = {}  # action_id -> bool
        bus.on("ACTION_STATE_CHANGED", self._on_action_state_changed)

    def _on_action_state_changed(self, action_id, active):
        if action_id.startswith("toggle_"):
            self.active_gates[action_id] = active

    def is_gate_active(self, action_id):
        return self.active_gates.get(action_id, False)

    def _on_focus_changed(self, mode: str):
        self.set_active(mode == "radial")

    def set_active(self, active: bool):
        self._active = active
        # Optionally reset state when disabled? Keep as is.

    def is_active(self) -> bool:
        return self._active

    def get_axes(self) -> dict:
        return self.axes.copy()

    def get_state(self) -> RadialState:
        return self.state

    def _on_axis_moved(self, axis: str, value: float):
        if not self._active:
            return
        if axis in self.axes:
            self.axes[axis] = value
            self._update()

    def _update(self):
        """Update state based on current axes."""
        x = self.axes.get("radial_menu_x", 0.0)
        y = self.axes.get("radial_menu_y", 0.0)
        dist = math.hypot(x, y)
        top_menu = self.state.stack[-1]

        # Determine hovered direction (if any)
        if dist > self.state.gate_threshold:
            angle = math.degrees(math.atan2(y, x))
            angle = (angle + 360) % 360
            idx = int((angle + 22.5) // 45) % 8
            directions = ["E", "SE", "S", "SW", "W", "NW", "N", "NE"]
            new_hover = directions[idx]
        else:
            new_hover = None

        # Entry grace logic (sub-menu)
        if new_hover is not None and new_hover in top_menu.gates:
            gate = top_menu.gates[new_hover]
            if gate.sub_menu is not None:
                if new_hover == self.state.pending_entry_gate:
                    self.state.entry_timer += 1
                    if self.state.entry_timer >= self.state.entry_grace_frames:
                        # Push submenu
                        self.state.stack.append(gate.sub_menu)
                        self.state.hovered_direction = None
                        self.state.pending_entry_gate = None
                        self.state.entry_timer = 0
                        bus.emit("RADIAL_MENU_PUSH", menu=gate.sub_menu)
                else:
                    self.state.pending_entry_gate = new_hover
                    self.state.entry_timer = 1
            else:
                self.state.pending_entry_gate = None
                self.state.entry_timer = 0
        else:
            self.state.pending_entry_gate = None
            self.state.entry_timer = 0

        # Selection (exit grace)
                
        if new_hover is None:
            self.state.exit_timer += 1
            # Check if hovered gate has a submenu
            has_submenu = False
            if self.state.hovered_direction is not None:
                gate = top_menu.gates.get(self.state.hovered_direction)
                if gate and gate.sub_menu is not None:
                    has_submenu = True
            # For gates without submenu, require only one frame in deadzone (instant)
            required_frames = self.state.exit_grace_frames if has_submenu else 1
            if self.state.exit_timer >= required_frames and self.state.hovered_direction is not None:
                selected = self.state.hovered_direction
                gate = top_menu.gates.get(selected)
                if gate:
                    self._activate_gate(gate)
                # Pop stack if not root
                if len(self.state.stack) > 1:
                    self.state.stack.pop()
                    bus.emit("RADIAL_MENU_POP")
                self.state.hovered_direction = None
                self.state.exit_timer = 0
                self.state.deadzone_timer = 0
        else:
            self.state.exit_timer = 0
            self.state.hovered_direction = new_hover

        # Pop stack on deadzone (exit submenu without selecting)
        if dist <= self.state.gate_threshold:
            self.state.deadzone_timer += 1
            if self.state.deadzone_timer >= self.state.deadzone_grace_frames:
                if len(self.state.stack) > 1:
                    self.state.stack.pop()
                    bus.emit("RADIAL_MENU_POP")
                    self.state.deadzone_timer = 0
                    self.state.hovered_direction = None
        else:
            self.state.deadzone_timer = 0

        # Emit state change for UI
        bus.emit("RADIAL_STATE_CHANGED", state=self.state)

    def _activate_gate(self, gate: Gate):
        if gate.gate_type == GateType.ONE_SHOT:
            bus.emit("INVOKE_ACTION", action_id=gate.action_id, value=True)
        elif gate.gate_type == GateType.TOGGLE:
            bus.emit("INVOKE_ACTION", action_id=gate.action_id, value=True)  # toggle handled by ActionManager