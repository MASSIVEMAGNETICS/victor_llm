import json
import time
from pathlib import Path

class SDRMemory:
    def __init__(self, storage_path=None):
        if storage_path is None:
            self.storage_path = Path(__file__).parent / "memory_store.jsonl"
        else:
            self.storage_path = Path(storage_path)

        # Ensure file exists
        if not self.storage_path.exists():
            self.storage_path.touch()

    def store(self, intent, emotion, text):
        """Store a new memory item."""
        memory_item = {
            "timestamp": time.time(),
            "intent": intent,
            "emotion": emotion,
            "text": text,
            "compressed": False
        }

        with open(self.storage_path, 'a') as f:
            f.write(json.dumps(memory_item) + '\n')

    def retrieve_all(self):
        """Retrieve all memory records."""
        records = []
        with open(self.storage_path, 'r') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line.strip()))
        return records

    def retrieve(self, query=None, limit=10):
        """Retrieve memories matching a query, or the most recent."""
        records = self.retrieve_all()
        # In a real SDR, this would perform a vector or symbolic search.
        # For demo purposes, we return the most recent entries.
        return records[-limit:]

    def write_all(self, records):
        """Overwrite the memory store with the given records."""
        with open(self.storage_path, 'w') as f:
            for record in records:
                f.write(json.dumps(record) + '\n')
