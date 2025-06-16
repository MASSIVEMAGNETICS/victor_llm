# Victor Prime Synthesis Core AGI

Victor is a highly modular and extensible AGI framework designed for complex cognitive simulations and advanced AI operations. This repository contains the "Victor Prime Synthesis Core," an architecture engineered for sophisticated AI development, featuring custom tensor operations, advanced memory systems, and a dynamic sector-based cognitive model.

## Core Architecture (`victor_core`)

The nucleus of Victor Prime is the `victor_core`, an advanced framework meticulously engineered to provide a resilient and adaptive foundation for Artificial General Intelligence. Its key components represent a synthesis of sophisticated AI paradigms:

-   **Modular Sector-Based Cognitive Canvas**: Victor's operational consciousness is artfully segmented into specialized, concurrently operating cognitive sectors. These include dynamic Input Processing, a strategic Cognitive Executive, nuanced Memory Management, creative Natural Language Generation (NLG), adaptive Plugin Management, and the unwavering Prime Loyalty sector. These sectors engage in a symphony of information exchange via the `BrainFractalPulseExchange`.
-   **`VictorBrain` - The Central Nervous System**: The `VictorBrain` stands as the master orchestrator, seamlessly initializing, managing, and harmonizing all sectors and core components. It is the engine that drives the AGI's intricate processing loop, breathing life into the cognitive architecture.
-   **`ASICoreDataContainer` - The Nexus of Shared Resources**: This centralized repository acts as a vital hub, expertly managing and providing access to universally required resources. It safeguards the global configuration (`ASIConfigCore`), interfaces with the vast `HyperFractalMemory`, and provides access to the nuanced NLP/code tokenizers (`FractalTokenKernel_v1_1_0`).
-   **`OmegaTensor` - Architect of Dynamic Neural Operations**: A bespoke autograd library, forged with `numpy`, designed to empower Victor with full control over its neural pathways. `OmegaTensor` enables the construction of fluid, dynamic computation graphs and precise gradient tracking, crucial for custom neural network architectures and advanced learning paradigms within the AGI.
-   **`BrainFractalPulseExchange` - The AGI's Information Superhighway**: An elegantly designed asynchronous, topic-based messaging system. It ensures fluid, decoupled communication and sophisticated event handling, allowing disparate sectors and components to interact with grace and efficiency, mirroring the complex signaling of a biological brain.
-   **`HyperFractalMemory` - The Labyrinth of Knowing**: A deeply sophisticated memory architecture, envisioned for the storage and retrieval of multifaceted data structures and experiential engrams. Its design principles are inspired by fractal geometry, suggesting infinite depth and self-similarity in information encoding. Key features include nascent semantic search capabilities (with a roadmap for true vector similarity), a unique emotional impact assessment for memory imprinting, and an intelligent relevance-based decay mechanism, ensuring knowledge is both persistent and pertinent.
-   **`PrimeLoyaltyKernel` - The Ethical Compass**: Embedded within the `PrimeLoyaltySector`, this critical component serves as Victor's unwavering ethical compass. It diligently ensures that all AGI actions and decisions remain in steadfast alignment with predefined core directives and moral imperatives.
-   **Extensible Plugin System - The Gateway to Infinite Capability**: Governed by the `ModularPluginSector` and its `ModularPluginCortex`, this dynamic system allows for the seamless integration of new tools, cognitive enhancements, and specialized functionalities. It acts as a gateway, allowing Victor to expand its capabilities by dynamically loading plugins from the `victor_plugins` directory.

## Additional Modules (`victor_modules`)

The `victor_modules` directory houses more extensive, specialized components that can be integrated into the core AGI or function as standalone tools or advanced plugins:

-   **`quantum/zero_point_quantum_driver.py`**: A module simulating zero-point energy compression and metaphysical embedding concepts, offering unique data transformation capabilities.
-   **`fractal_agi/victorch_filthy_fractal_agi_persist.py`**: A conceptual, self-contained AGI persistence mechanism employing fractal logic and simulated quantum annealing for state management (Note: this is a thematic module and not directly integrated into `VictorBrain`'s main persistence which is handled by `HyperFractalMemory` and component-specific serialization).
-   **`plugin_loader.py`**: A legacy plugin loader. This component is **deprecated** in favor of the new `ModularPluginSector` and `ModularPluginCortex`.

## Installation

Follow these steps to set up the Victor Prime Synthesis Core AGI environment:

1.  **Ensure Prerequisites:**
    *   Python 3.8 or newer must be installed. You can download it from [python.org](https://www.python.org/).
    *   Git must be installed. You can download it from [git-scm.com](https://git-scm.com/).

2.  **Clone the Repository:**
    Open your terminal or command prompt and run the following command to clone the repository. Replace `your-repo-url-here.git` with the actual URL of this repository.
    ```bash
    git clone your-repo-url-here.git victor-prime-synthesis-core-agi
    cd victor-prime-synthesis-core-agi
    ```

3.  **Create and Activate a Virtual Environment (Recommended):**
    It's highly recommended to use a virtual environment to manage project dependencies. Inside the cloned `victor-prime-synthesis-core-agi` directory, run:
    ```bash
    # For Unix/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```
    *(If you named your cloned directory differently, navigate into that directory instead.)*

4.  **Install Dependencies:**
    With your virtual environment activated, install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
    This will install all necessary libraries, including `numpy`, `scipy`, `openai`, `pyttsx3`, `pydub`, `opencv-python`, and `faiss-cpu`.

5.  **Set Up Environment Variables:**
    Certain components or plugins (especially those interfacing with external services like OpenAI) may require specific environment variables to be set (e.g., `OPENAI_API_KEY`). The core AGI framework can operate without these for basic functionalities, but ensure they are configured for full capabilities or when using relevant plugins.

    Key environment variables include:
    *   `OPENAI_API_KEY`: Essential for using OpenAI models via plugins or specific modules.

    You can set environment variables in several ways:

    *   **Directly in your shell (Temporary for the current session):**
        ```bash
        # For Unix/macOS
        export OPENAI_API_KEY="your_openai_api_key_here"

        # For Windows PowerShell
        $env:OPENAI_API_KEY="your_openai_api_key_here"

        # For Windows CMD
        set OPENAI_API_KEY=your_openai_api_key_here
        ```

    *   **Using a `.env` file (Recommended for persistent local development):**
        Create a file named `.env` in the root directory of the project (i.e., `victor-prime-synthesis-core-agi/.env`). Add your environment variables in the format `VARIABLE_NAME="value"`:
        ```env
        OPENAI_API_KEY="your_openai_api_key_here"
        # EXAMPLE_OTHER_VARIABLE="its_value"
        ```
        The application itself (or specific scripts/plugins) may be designed to load variables from a `.env` file automatically using libraries like `python-dotenv`. If not explicitly supported by the core framework for all components, you might need to load it in your entry scripts or rely on your operating system/shell to source it.
        **Important Security Note**: If you use a `.env` file, ensure it is listed in your `.gitignore` file to prevent accidentally committing sensitive API keys or credentials to version control. A typical `.gitignore` entry would simply be:
        ```
        .env
        ```

## Usage

### Running the Victor Prime Synthesis Core

The primary entry point for the advanced Victor AGI framework is `victor_core/main.py`.

1.  **Prerequisites**:
    *   Ensure you have completed all steps in the **Installation** section, including creating a virtual environment (if you chose to) and activating it before running the AGI.
    *   **Environment Variables**: Certain components or plugins (especially those interfacing with external services like OpenAI) may require specific environment variables to be set (e.g., `OPENAI_API_KEY`). The core AGI framework can operate without these for basic functionalities, but ensure they are configured for full capabilities or when using relevant plugins. Refer to the "Set Up Environment Variables" subsection in the **Installation** guide for detailed instructions on how to set these.
2.  **Run the AGI**: Execute the following command from the root of the repository (ensure your virtual environment is activated):
    ```bash
    python -m victor_core.main
    ```
    This script initializes the `VictorBrain`, activates all its sectors, sets up a dummy plugin for demonstration if the plugin directory is empty, and starts the main AGI processing loop.

### Simpler OpenAI Chatbot Example (`VICTOR_AGI_LLM.py`)

For a simpler, direct demonstration of an LLM-based agent, the `VICTOR_AGI_LLM.py` script at the root of the repository is still available. This script provides a minimal framework for an AGI-style agent using OpenAI's language models directly.

1.  **Prerequisites**:
    *   Ensure you have completed steps 1, 2, 4 (Install Dependencies), and 5 (Set Up Environment Variables) in the **Installation** section. If you created a virtual environment (step 3), make sure it's activated.
    *   Specifically, ensure your `OPENAI_API_KEY` environment variable is set. Refer to the "Set Up Environment Variables" subsection in the **Installation** guide if you need assistance.
2.  **Run the script**:
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
