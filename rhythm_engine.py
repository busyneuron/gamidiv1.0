import math
from dataclasses import dataclass

# The absolute standard for MIDI clock resolution. 
# 24 Pulses Per Quarter Note.
PPQN = 24 

# Base tick values for standard musical durations
BASE_DURATIONS = {
    "whole": PPQN * 4,        # 96
    "half": PPQN * 2,         # 48
    "quarter": PPQN,          # 24
    "eighth": PPQN // 2,      # 12
    "sixteenth": PPQN // 4,   # 6
    "thirty-second": PPQN // 8 # 3
}

# Articulation defines the "gate length" of a note.
# It is a multiplier representing what percentage of the total duration the note is held.
ARTICULATIONS = {
    "legato": 1.0,         # 100% (Note releases exactly as the next begins)
    "tenuto": 0.95,        # 95%  (Slightly detached)
    "normal": 0.85,        # 85%  (Standard playing)
    "staccato": 0.5,       # 50%  (Short and punchy)
    "staccatissimo": 0.25, # 25%  (Very short)
}

@dataclass
class MotifStep:
    """
    A single step in a rhythm sequence. 
    A Voice will read this to know exactly what to do when its internal tick counter hits 0.
    """
    total_ticks: int   # How many ticks until we move to the next step
    gate_ticks: int    # How many ticks the note is held before sending note_off
    is_rest: bool      # If True, no note_on is sent for this step

class RhythmEngine:
    @staticmethod
    def parse_duration(duration_str: str) -> tuple[int, bool]:
        """
        Parses a string like "quarter dotted" or "eighth triplet rest" 
        Returns: (total_ticks: int, is_rest: bool)
        """
        words = duration_str.lower().split()
        
        # 1. Find the base duration
        base_ticks = PPQN # Default fallback
        for word in words:
            if word in BASE_DURATIONS:
                base_ticks = BASE_DURATIONS[word]
                break
                
        # 2. Apply modifiers (dots and triplets)
        if "dotted" in words:
            base_ticks = math.ceil(base_ticks * 1.5)
        elif "triplet" in words:
            # A triplet fits 3 notes in the space of 2.
            # E.g., an eighth triplet = (12 * 2) / 3 = 8 ticks.
            base_ticks = math.ceil(base_ticks * (2 / 3))
            
        # 3. Check if it's a rest
        is_rest = "rest" in words
        
        return int(base_ticks), is_rest

    @staticmethod
    def parse_articulation(articulation_str: str) -> float:
        """
        Parses an articulation string into a float multiplier.
        Falls back to 'normal' if the string is empty or unrecognized.
        """
        art = articulation_str.lower().strip()
        return ARTICULATIONS.get(art, ARTICULATIONS["normal"])

    @staticmethod
    def compile_motif(motif: list[tuple[str, str]]) -> list[MotifStep]:
        """
        Takes a human-readable motif list and compiles it into a list of MotifSteps.
        Example Input: 
            [("quarter", "staccato"), ("eighth", "legato"), ("eighth rest", "")]
        """
        compiled = []
        for duration_str, art_str in motif:
            total_ticks, is_rest = RhythmEngine.parse_duration(duration_str)
            
            if is_rest:
                gate_ticks = 0 # Rests have no gate length
            else:
                art_multiplier = RhythmEngine.parse_articulation(art_str)
                # Ensure a note is held for at least 1 tick
                gate_ticks = max(1, math.floor(total_ticks * art_multiplier))
                
            compiled.append(MotifStep(
                total_ticks=total_ticks,
                gate_ticks=gate_ticks,
                is_rest=is_rest
            ))
            
        return compiled

# --- Example Usage (Just for demonstration, this won't run in the main app yet) ---
if __name__ == "__main__":
    # Example 1: A straight rhythm
    sample_motif = [
        ("quarter", "staccato"),
        ("eighth", "legato"),
        ("eighth", "legato")
    ]
    
    # Example 2: SYNCOPATION / OFF-BEATS
    # Here, we rest on the downbeat, play on the "and", rest on beat 2, play on the "and"
    syncopated_motif = [
        ("eighth rest", ""),       # 1
        ("eighth", "staccato"),    # & (Off-beat!)
        ("eighth rest", ""),       # 2
        ("eighth", "staccato"),    # & (Off-beat!)
        ("quarter", "normal")      # 3, 4 (Lands on the downbeat)
    ]
    
    # Example 3: THE GALLOP (Long-short-short)
    gallop_motif = [
        ("eighth", "staccato"),    # 12 ticks
        ("sixteenth", "staccato"), # 6 ticks
        ("sixteenth", "staccato")  # 6 ticks
    ]
    
    print("--- Straight Motif ---")
    for i, step in enumerate(RhythmEngine.compile_motif(sample_motif)):
        print(f"Step {i+1}: {step}")
        
    print("\n--- Syncopated Motif ---")
    for i, step in enumerate(RhythmEngine.compile_motif(syncopated_motif)):
        print(f"Step {i+1}: {step}")

    print("\n--- Gallop Motif ---")
    for i, step in enumerate(RhythmEngine.compile_motif(gallop_motif)):
        print(f"Step {i+1}: {step}")