"""
VICTOR_AGI_LLM: a simple AGI framework example.

Features
--------
- Conversational interface using OpenAI's ChatCompletion API.
- Maintains conversation history (memory).
- Optional text‑to‑speech output via `pyttsx3`.
- Placeholder hooks for vision features using OpenCV.
"""

import argparse
import os
import openai
import numpy as np

try:
    import pyttsx3
except ImportError:  # voice output is optional
    pyttsx3 = None

# Optional import for vision functions. Not required to run basic chat.
try:
    import cv2  # type: ignore
except Exception:  # opencv might not be installed
    cv2 = None


class VictorAGI:
    def __init__(self, voice: bool = False):
        self.voice = bool(voice and pyttsx3)
        self.history = []
        if self.voice:
            self.engine = pyttsx3.init()
        else:
            self.engine = None

    def _speak(self, text: str) -> None:
        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()

    def respond(self, message: str) -> str:
        self.history.append({"role": "user", "content": message})
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=self.history,
        )
        reply = resp["choices"][0]["message"]["content"]
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def chat_loop(self) -> None:
        print("Type 'quit' or press Ctrl+C to exit.")
        while True:
            try:
                user_input = input("You: ")
            except (KeyboardInterrupt, EOFError):
                print()
                break
            if user_input.strip().lower() in {"quit", "exit"}:
                break
            reply = self.respond(user_input)
            print("Victor:", reply)
            self._speak(reply)


def main() -> None:
    parser = argparse.ArgumentParser(description="Victor AGI LLM demo")
    parser.add_argument(
        "--voice", action="store_true", help="Enable text-to-speech replies"
    )
    args = parser.parse_args()

    if "OPENAI_API_KEY" not in os.environ:
        raise EnvironmentError(
            "Please set the OPENAI_API_KEY environment variable before running."
        )
    openai.api_key = os.environ["OPENAI_API_KEY"]

    agent = VictorAGI(voice=args.voice)
    agent.chat_loop()


if __name__ == "__main__":
    main()
