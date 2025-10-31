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

## Installation

1.  Ensure you have Python 3.8 or newer installed.
2.  Clone this repository to your local machine.
3.  Navigate to the repository's root directory and install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    This will install `numpy`, `scipy`, `openai`, `pyttsx3`, `pydub`, and `opencv-python`, among any other core requirements.

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

## Contributing

We welcome contributions to the Victor AGI Framework! Please follow these guidelines:

1. **Read the Contributing Guide**: Check out [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions
2. **Code of Conduct**: Please review our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
3. **Fork and Branch**: Create a feature branch from `main`
4. **Follow Standards**: Adhere to PEP 8 style guidelines and existing code patterns
5. **Write Tests**: Add tests for new features or bug fixes
6. **Submit PR**: Use the PR template and fill it out completely

### Quick Start for Contributors

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/victor_llm.git
cd victor_llm

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pytest pytest-cov flake8 black isort

# Make your changes, then test
python -m pytest test_bando_copilot.py -v

# Format your code
black .
isort .
flake8 .

# Commit and push
git add .
git commit -m "feat: Your descriptive commit message"
git push origin your-feature-branch
```

For more details, see our [Contributing Guide](CONTRIBUTING.md).

## CI/CD

This project uses GitHub Actions for continuous integration and deployment:

- **CI Workflow**: Runs tests, linting, and security checks on all PRs and pushes
- **Release Workflow**: Automatically creates releases when version tags are pushed
- **PR Checklist**: Validates PR descriptions and adds size labels
- **Auto-labeling**: Automatically labels issues and PRs based on content
- **Dependency Review**: Checks for security vulnerabilities in dependencies
- **Stale Bot**: Automatically closes inactive issues and PRs

## License

This project is proprietary - Massive Magnetics / Ethica AI / BHeard Network.

```
