Circle of Fifths Module Documentation
Overview
The circle_of_fifths folder contains a complete, self-contained widget for displaying and interacting with the circle of fifths in the GAMIDI application. It supports two distinct modes:

Chromatic Circle – classic circle of fifths (note names, changes root/mode)

Degree Circle – diatonic circle (roman numerals, sets filter pivot without changing root)

Both modes share the same visual base (rings, colors, animations, input handling) but have different labeling and selection logic.

Folder Structure
text
circle_of_fifths/
├── __init__.py                 (empty, marks package)
├── base_circle.py              – abstract base class with shared drawing & input
├── chromatic_circle.py        – ChromaticCircle subclass
├── degree_circle.py           – DegreeCircle subclass
└── README.md                  – this file
Note: There are no separate *_controller.py or *_state.py files. Each circle widget is self-contained (MVC merged). This simplifies the code because the circle is a single interactive component.

Class Descriptions
BaseCircle (abstract)
File: base_circle.py

Provides all common functionality:

PNG caching and tinted circle surfaces

Radius animation (ease‑out/in‑out)

Theme colors (tonic, triad, diatonic, other, hover)

Input handling (right stick → angle → index, deadzone, grace timer)

Ring drawing (outer major, inner minor)

Event subscriptions (RIGHT_STICK_UPDATED, FOCUS_CHANGED, CHORD_QUALITIES_CHANGED)

Abstract methods (must be overridden):

get_gate_label(index, is_major_ring, chord_info) -> str

on_select(index) -> None

Optional overrides:

get_gate_style(...) – change colors/radii for selected gates

get_center_text() -> str – text drawn in the center (e.g., roman numeral)

toggle_ring() – custom behaviour when switching between major/minor rings

ChromaticCircle
File: chromatic_circle.py

Labels: note names (C, G, D, … outer; a, e, b, … inner)

Selection: changes root and mode, activates filter mode, highlights the new tonic

Center text: none

Ring toggle: clears selected index (highlight disappears)

DegreeCircle
File: degree_circle.py

Labels: roman numerals for diatonic chords that match the ring’s chord quality (major on outer, minor on inner, tonic on both); otherwise note names.

Selection: sets filter pivot without changing root; highlights the selected degree.

Center text: shows roman numeral of selected degree.

Ring toggle: clears selected index.

Selected gate uses a distinct color (gold by default, can be themed).

Shared Constants
The following are defined in base_circle.py and used by both subclasses:

python
MAJOR_NOTES   = ["C","G","D","A","E","B","F#","Db","Ab","Eb","Bb","F"]
MAJOR_PITCHES = [0,7,2,9,4,11,6,1,8,3,10,5]
MINOR_NAMES   = ["a","e","b","f#","db","ab","eb","bb","f","c","g","d"]
MINOR_PITCHES = [(p-3)%12 for p in MAJOR_PITCHES]
These map gate index (0‑11) to pitch class and display name for the two rings.

Integration with the Main Application
In interface.py:

python
from circle_of_fifths.chromatic_circle import ChromaticCircle
from circle_of_fifths.degree_circle import DegreeCircle

self.chromatic_circle = ChromaticCircle(self, theory_engine)
self.degree_circle = DegreeCircle(self, theory_engine)
self.active_circle = self.chromatic_circle   # start with chromatic

# Apply theme
self.chromatic_circle.apply_theme(self.theme)
self.degree_circle.apply_theme(self.theme)

# Listen to mode toggle event
bus.on("TOGGLE_CIRCLE_MODE", self._on_toggle_circle_mode)
In draw():

python
rect_circle = self.grid.get_rect(2, 5, 6, 5)
self.active_circle.draw(self.layer_content, rect_circle)
Switching between circles is done by emitting TOGGLE_CIRCLE_MODE (e.g., from a button mapped in action_mapper.py).

The Story – How We Ended Up Here
Initially, the circle of fifths was a single, monolithic file (circle_of_fifths.py) tightly coupled with the old logic.py and interface.py. It had a single mode (chromatic) and a half‑implemented degree mode hacked in with if state.degree_mode branches everywhere. The code was hard to read and buggy – diagonal selection was unreliable, center text disappeared, and toggling rings caused unexpected root changes.

We decided to refactor. First, we moved to an event‑driven architecture and created separate CircleController, CircleView, and CircleState files. That cleaned up the drawing and input but still suffered from mode‑specific conditionals scattered in both controller and view.

Then we tried a “mode strategy” pattern – ChromaticMode and DegreeMode classes that the controller delegated to. This was better but still felt over‑engineered. The view still contained if degree_mode logic, and the modes had to reach into the view for style getters.

Finally, we asked: “Why not make each mode its own widget?” They share 90% of the code – drawing, animations, input handling – but differ in labels, selection behavior, and center text. So we created a BaseCircle class with all shared code and two simple subclasses. No more mode flags, no more controllers. Each widget is self‑contained, easy to understand, and easy to extend (e.g., a “diminished” circle would be trivial to add).

The result is a clean, maintainable module that works reliably. The two widgets look identical to the user but behave completely differently under the hood – exactly what we wanted.

Future Extensions
Custom colors for selected degree – already supported via get_gate_style override in DegreeCircle.

Third circle type – e.g., “dominant” or “altered” – just subclass BaseCircle and implement the three abstract methods.

Different ring shapes – override _draw_ring in a subclass.

Center text animation – add a pulsing effect in get_center_text.

File List Summary
File	Responsibility
base_circle.py	Shared drawing, animations, input handling, theme
chromatic_circle.py	Chromatic mode (note names, change root)
degree_circle.py	Degree mode (roman numerals, filter pivot)
__init__.py	Package marker
No other files. The old circle_controller.py, circle_view.py, circle_state.py, circle_modes.py have been removed.

Happy coding!
– Future you, with thanks to the present you who wrote this doc.