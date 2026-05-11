import os
import sys
import torch
from pathlib import Path

# Add project root to path so we can import models
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from models.transformer_model import VictorTransformerModel
    from models import load_blank_slate, load_pretrained_checkpoint
    HAS_MODEL = True
except ImportError as e:
    print(f"Warning: Could not import Victor components: {e}")
    HAS_MODEL = False

class ModelAdapter:
    def __init__(self, use_mock=False):
        self.use_mock = use_mock or not HAS_MODEL
        self.model = None
        self.tokenizer = None

        if not self.use_mock:
            try:
                # Load dummy model configuration
                config = load_blank_slate()
                # If a tokenizer or specific loading is required, it could be done here
                pass
            except Exception as e:
                print(f"Failed to load model config, falling back to mock: {e}")
                self.use_mock = True

    def infer(self, text):
        """
        Run inference on the text.
        Returns a tuple: (response_text, extracted_intent, detected_emotion)
        """
        # A simple keyword-based intent/emotion extraction for the demo
        intent = "general_chat"
        emotion = "neutral"

        lower_text = text.lower()
        if "help" in lower_text or "how to" in lower_text:
            intent = "request_help"
        elif "train" in lower_text or "learn" in lower_text:
            intent = "train_command"

        if "angry" in lower_text or "mad" in lower_text or "!" in text:
            emotion = "agitated"
        elif "happy" in lower_text or "good" in lower_text or "thanks" in lower_text:
            emotion = "positive"

        if self.use_mock:
            response = self._mock_infer(text, intent, emotion)
            return response, intent, emotion

        # If we had a real model hooked up to real generation code, we would use it here
        return self._mock_infer(text, intent, emotion), intent, emotion

    def _mock_infer(self, text, intent, emotion):
        if intent == "request_help":
            return "I am Victor. I am here to help. What specific assistance do you require?"
        elif intent == "train_command":
            return "I have logged your request. My learning queue will process this."

        return f"I am Victor. I received your input: '{text}'. My systems are operating normally."
