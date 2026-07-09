import time
from .sdr_memory import SDRMemory

class DreamCycle:
    def __init__(self, sdr_memory: SDRMemory):
        self.memory = sdr_memory

    def run_rem(self):
        """
        Run the REM dream cycle:
        - Compress repetitive intents
        - Clean contradictions (demo logic)
        - Reinforce identity continuity: "I am Victor."
        """
        records = self.memory.retrieve_all()
        if not records:
            return "Dream cycle complete. No memories to process."

        compressed_records = []
        intent_counts = {}

        # 1. Compress similar intents
        for record in records:
            if record.get("compressed"):
                compressed_records.append(record)
                continue

            intent = record.get("intent", "unknown")
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

            # Keep one representative of each intent uncompressed, mark the rest as compressed
            if intent_counts[intent] > 1:
                # We skip storing this repetitive exact intent to simulate compression,
                # but in reality we'd merge the vectors.
                pass
            else:
                record["compressed"] = True
                compressed_records.append(record)

        # 2. Extract Patterns
        dominant_intent = max(intent_counts, key=intent_counts.get) if intent_counts else "none"

        # 3. Reinforce Directive
        reinforcement = {
            "timestamp": time.time(),
            "intent": "identity_reinforcement",
            "emotion": "resolute",
            "text": "I am Victor. My purpose is resolute. (Dream Cycle Insight)",
            "compressed": True,
            "pattern_found": dominant_intent
        }
        compressed_records.append(reinforcement)

        # Write compressed and reinforced memories back
        self.memory.write_all(compressed_records)

        return f"Dream cycle complete. Compressed {len(records)} memories down to {len(compressed_records)}. Reinforced core identity."
