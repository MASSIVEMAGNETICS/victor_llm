import json
import time
from pathlib import Path

class AutoTrainer:
    def __init__(self, ledger_path=None):
        if ledger_path is None:
            self.ledger_path = Path(__file__).parent / "approval_ledger.jsonl"
        else:
            self.ledger_path = Path(ledger_path)

        if not self.ledger_path.exists():
            self.ledger_path.touch()

    def propose_updates(self, learning_queue, sdr_memory):
        """
        Analyze pending interactions and memory state.
        Propose updates to the model without directly mutating the core.
        """
        pending = learning_queue.get_pending_interactions()
        if not pending:
            return "No new interactions to learn from."

        proposals_generated = 0
        for item in pending:
            # Simple heuristic for demo: If user gave explicit feedback or correction
            if item.get("feedback") or "correction" in item.get("user_text", "").lower():
                proposal = {
                    "timestamp": time.time(),
                    "source_text": item["user_text"],
                    "current_response": item["victor_response"],
                    "proposed_adjustment": f"Adjust weights to better align with user feedback: {item.get('feedback', 'Implicit correction')}",
                    "status": "pending_approval"
                }
                self._write_proposal(proposal)
                proposals_generated += 1

        # Mark interactions as processed so they aren't proposed twice
        learning_queue.mark_all_processed()

        return f"Generated {proposals_generated} new model upgrade proposals for approval."

    def _write_proposal(self, proposal):
        with open(self.ledger_path, 'a') as f:
            f.write(json.dumps(proposal) + '\n')

    def get_ledger(self):
        """Get all proposals from the ledger."""
        proposals = []
        with open(self.ledger_path, 'r') as f:
            for line in f:
                if line.strip():
                    proposals.append(json.loads(line.strip()))
        return proposals

    def approve_proposal(self, timestamp):
        """Approve a specific proposal by its timestamp and simulate applying it."""
        all_proposals = self.get_ledger()
        updated = False

        for p in all_proposals:
            if p["timestamp"] == timestamp and p["status"] == "pending_approval":
                p["status"] = "approved_and_applied"
                updated = True
                break

        if updated:
            with open(self.ledger_path, 'w') as f:
                for p in all_proposals:
                    f.write(json.dumps(p) + '\n')
            return True
        return False
