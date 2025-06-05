# victor_llm

Victor AGI LLM is a minimal framework demonstrating an AGI-style agent built on top of OpenAI's language models. It keeps track of conversation history and can optionally reply using text-to-speech or hook into vision modules.

## Features

- Conversational interface using the OpenAI API.
- Maintains memory of previous messages.
- Optional speech synthesis with `pyttsx3`.
- Placeholder support for audio (`pydub`) and vision (`opencv-python`).

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

For speech synthesis or vision support you may also install the optional packages:

```bash
pip install pyttsx3 pydub opencv-python
```

## Usage

Set your `OPENAI_API_KEY` environment variable and run:

```bash
python VICTOR_AGI_LLM.py
```

Add `--voice` to enable text-to-speech if you have the `pyttsx3` package installed.
