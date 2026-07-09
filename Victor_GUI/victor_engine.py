import sys
import os
from pathlib import Path

from model_adapter import ModelAdapter
from memory.sdr_memory import SDRMemory
from memory.dream_cycle import DreamCycle
from training.learning_queue import LearningQueue
from training.auto_train import AutoTrainer

class VictorEngine:
    def __init__(self):
        self.model_adapter = ModelAdapter()
        self.sdr_memory = SDRMemory()
        self.dream_cycle = DreamCycle(self.sdr_memory)
        self.learning_queue = LearningQueue()
        self.auto_trainer = AutoTrainer()

    def chat(self, message):
        """
        Main chat interface for the GUI.
        1. Infers response, intent, and emotion.
        2. Logs interaction to learning queue.
        3. Stores interaction to SDR memory.
        """
        response, intent, emotion = self.model_adapter.infer(message)

        # Log to learning queue for potential auto-training
        self.learning_queue.add_interaction(message, response)

        # Store in SDR memory for long term patterns
        self.sdr_memory.store(intent, emotion, message)

        return response

    def trigger_dream_cycle(self):
        """Manually trigger the REM dream cycle to compress memories."""
        return self.dream_cycle.run_rem()

    def generate_training_proposals(self):
        """Read pending interactions and generate upgrade proposals."""
        return self.auto_trainer.propose_updates(self.learning_queue, self.sdr_memory)

    def get_ledger(self):
        """Retrieve the approval ledger."""
        return self.auto_trainer.get_ledger()

    def approve_proposal(self, timestamp):
        """Approve a specific proposal by timestamp."""
        success = self.auto_trainer.approve_proposal(timestamp)
        if success:
            return f"Proposal {timestamp} approved and applied successfully."
        return f"Failed to approve proposal {timestamp}."

    def get_memories(self):
        """Retrieve all SDR memories for viewing."""
        return self.sdr_memory.retrieve_all()

    def run_self_test(self):
        """Run a quick assertion to check all modules are functional."""
        try:
            assert self.model_adapter is not None, "Model Adapter missing"
            assert self.sdr_memory is not None, "SDR Memory missing"
            assert self.dream_cycle is not None, "Dream Cycle missing"
            assert self.learning_queue is not None, "Learning Queue missing"
            assert self.auto_trainer is not None, "Auto Trainer missing"

            # Non-mutating read tests
            _ = self.sdr_memory.retrieve(limit=1)
            _ = self.learning_queue.get_pending_interactions()
            _ = self.auto_trainer.get_ledger()

            return "Self-Test PASSED: All core modules are initialized and readable."
        except Exception as e:
            return f"Self-Test FAILED: {e}"
