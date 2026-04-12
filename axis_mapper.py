# axis_mapper.py
from event_bus import bus

class AxisMapper:
    def __init__(self):
        # Hardcoded mapping: physical axis index -> logical name
        self.axis_map = {
            2: "radial_menu_x",
            3: "radial_menu_y",
            # Additional axes can be added later:
            # 0: "pitch_x", 1: "pitch_y", etc.
        }
        # Subscribe to raw axis events
        bus.on("RAW_AXIS_MOVED", self._on_raw_axis)

    def _on_raw_axis(self, axis: int, value: float):
        if axis in self.axis_map:
            logical_name = self.axis_map[axis]
            bus.emit("AXIS_MOVED", axis=logical_name, value=value)