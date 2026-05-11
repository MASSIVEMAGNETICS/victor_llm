import json
import time
from pathlib import Path

class LearningQueue:
    def __init__(self, queue_path=None):
        if queue_path is None:
            self.queue_path = Path(__file__).parent / "learning_queue.jsonl"
        else:
            self.queue_path = Path(queue_path)

        if not self.queue_path.exists():
            self.queue_path.touch()

    def add_interaction(self, user_text, victor_response, feedback=None):
        """Add an interaction to the pending learning queue."""
        item = {
            "timestamp": time.time(),
            "user_text": user_text,
            "victor_response": victor_response,
            "feedback": feedback,
            "processed": False
        }
        with open(self.queue_path, 'a') as f:
            f.write(json.dumps(item) + '\n')

    def get_pending_interactions(self):
        """Retrieve all unprocessed interactions."""
        pending = []
        with open(self.queue_path, 'r') as f:
            for line in f:
                if line.strip():
                    item = json.loads(line.strip())
                    if not item.get("processed", False):
                        pending.append(item)
        return pending

    def mark_all_processed(self):
        """Mark all pending items as processed."""
        all_items = []
        with open(self.queue_path, 'r') as f:
            for line in f:
                if line.strip():
                    all_items.append(json.loads(line.strip()))

        for item in all_items:
            item["processed"] = True

        with open(self.queue_path, 'w') as f:
            for item in all_items:
                f.write(json.dumps(item) + '\n')
