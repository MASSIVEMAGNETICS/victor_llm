# Victor Prime Synthesis Core AGI

Victor is a highly modular and extensible AGI framework designed for complex cognitive simulations and advanced AI operations. This repository contains the "Victor Prime Synthesis Core," an architecture engineered for sophisticated AI development, featuring custom tensor operations, advanced memory systems, and a dynamic sector-based cognitive model.

## Core Architecture (`victor_core`)

The heart of the system is the `victor_core`, which provides a robust foundation for AGI development. Key components include:

-   **Modular Sector-Based Design**: The AGI's operations are segmented into specialized, concurrently operating sectors. These include Input Processing, Cognitive Executive, Memory Management, Natural Language Generation (NLG), Plugin Management, and Prime Loyalty. Sectors communicate asynchronously via the `BrainFractalPulseExchange`.
-   **`VictorBrain`**: The central orchestrator that initializes, manages, and coordinates all sectors and core components, driving the main AGI processing loop.
-   **`ASICoreDataContainer`**: A centralized container that manages and provides access to shared resources such as global configuration (`ASIConfigCore`), the main memory system (`HyperFractalMemory`), and NLP/code tokenizers (`FractalTokenKernel_v1_1_0`).
-   **`OmegaTensor`**: A custom autograd library built with `numpy`, enabling dynamic computation graphs and gradient tracking for neural network operations within the AGI framework.
-   **`BrainFractalPulseExchange`**: An asynchronous, topic-based messaging system facilitating decoupled communication and event handling between different sectors and components.
-   **`HyperFractalMemory`**: A sophisticated memory system designed for storing complex data structures, featuring semantic search capabilities (placeholder for vector similarity), emotional impact assessment, and relevance-based decay.
-   **`PrimeLoyaltyKernel`**: A component integrated within the `PrimeLoyaltySector` to ensure the AGI's actions and decisions align with predefined core directives and ethical guidelines.
-   **Extensible Plugin System**: Managed by the `ModularPluginSector` and its `ModularPluginCortex`, allowing for the dynamic loading and integration of new capabilities and tools from the `victor_plugins` directory.

## Additional Modules (`victor_modules`)

The `victor_modules` directory houses more extensive, specialized components that can be integrated into the core AGI or function as standalone tools or advanced plugins:

-   **`quantum/zero_point_quantum_driver.py`**: A module simulating zero-point energy compression and metaphysical embedding concepts, offering unique data transformation capabilities.
-   **`fractal_agi/victorch_filthy_fractal_agi_persist.py`**: A conceptual, self-contained AGI persistence mechanism employing fractal logic and simulated quantum annealing for state management (Note: this is a thematic module and not directly integrated into `VictorBrain`'s main persistence which is handled by `HyperFractalMemory` and component-specific serialization).
-   **`plugin_loader.py`**: A legacy plugin loader. This component is **deprecated** in favor of the new `ModularPluginSector` and `ModularPluginCortex`.

## Models (`models`)

The `models` directory contains model configurations and pretrained model files for Victor:

-   **`blank_slate.json`**: A minimal, untrained model configuration that serves as a starting point for training or fine-tuning. Contains architecture configuration, training hyperparameters, and system settings.
-   **Pretrained GGUF Models**: Victor supports GGUF (GPT-Generated Unified Format) quantized models for efficient inference. Due to their large size, pretrained models must be downloaded separately. See `models/PRETRAINED_GGUF_DOWNLOAD.txt` for instructions.
-   **Model Utilities**: The `models` module provides Python utilities for loading and managing models. See `models/example_usage.py` for examples.

For detailed information about models, see `models/README.md`.

## Installation

1.  Ensure you have Python 3.8 or newer installed.
2.  Clone this repository to your local machine.
3.  Navigate to the repository's root directory and install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    This will install `numpy`, `scipy`, `openai`, `pyttsx3`, `pydub`, and `opencv-python`, among any other core requirements.
4.  (Optional) To use pretrained GGUF models, install llama-cpp-python:
    ```bash
    pip install llama-cpp-python
    ```
    See `models/PRETRAINED_GGUF_DOWNLOAD.txt` for instructions on obtaining pretrained models.

## Usage

### Running the Victor Prime Synthesis Core

The primary entry point for the advanced Victor AGI framework is `victor_core/main.py`.

1.  **Environment Variables**: Certain components or plugins (especially those interfacing with external services like OpenAI) may require specific environment variables to be set (e.g., `OPENAI_API_KEY`). The core AGI framework can operate without these for basic functionalities, but ensure they are configured for full capabilities or when using relevant plugins.
2.  **Run the AGI**: Execute the following command from the root of the repository:
    ```bash
    python -m victor_core.main
    ```
    This script initializes the `VictorBrain`, activates all its sectors, sets up a dummy plugin for demonstration if the plugin directory is empty, and starts the main AGI processing loop.

### Simpler OpenAI Chatbot Example (`VICTOR_AGI_LLM.py`)

For a simpler, direct demonstration of an LLM-based agent, the `VICTOR_AGI_LLM.py` script at the root of the repository is still available. This script provides a minimal framework for an AGI-style agent using OpenAI's language models directly.

1.  Ensure your `OPENAI_API_KEY` environment variable is set.
2.  Run the script:
    ```bash
    python VICTOR_AGI_LLM.py
    ```
    You can enable text-to-speech output by adding the `--voice` argument if you have the `pyttsx3` package installed and configured.

## Development

-   The core AGI framework logic resides primarily within the `victor_core` package.
-   New functionalities and tools can be added by creating plugins in the `victor_plugins` directory (the specific path is configured in `victor_core/config.py` via `ASIConfigCore.PLUGIN_DIR`).
-   Larger, more specialized modules or standalone conceptual systems can be developed within the `victor_modules` directory.
-   The system uses an asynchronous architecture; familiarity with Python's `asyncio` library is beneficial for development.
```
