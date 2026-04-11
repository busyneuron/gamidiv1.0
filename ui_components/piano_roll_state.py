# ui_components/piano_roll_state.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class NoteHistoryEntry:
    note: int
    start_pulse: int
    end_pulse: Optional[int] = None
    channel: int = 0

@dataclass
class PianoRollState:
    pulse_count: int = 0
    history: List[NoteHistoryEntry] = field(default_factory=list)
    max_history: int = 200  # keep last 200 notes

    def add_note_on(self, note, channel, pulse):
        entry = NoteHistoryEntry(note=note, start_pulse=pulse, channel=channel)
        self.history.append(entry)
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def add_note_off(self, note, channel, pulse):
        # find the most recent matching note-on without an end
        for entry in reversed(self.history):
            if entry.note == note and entry.channel == channel and entry.end_pulse is None:
                entry.end_pulse = pulse
                break