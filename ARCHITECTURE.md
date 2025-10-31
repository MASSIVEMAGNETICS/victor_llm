# Victor Prime AGI - Architecture Documentation

## Overview

Victor Prime AGI is a modular, extensible Artificial General Intelligence framework built with Python. The architecture follows a sector-based design pattern where specialized cognitive components operate concurrently and communicate asynchronously via a message-passing system.

## Core Architectural Principles

1. **Modularity**: Each component is self-contained and replaceable
2. **Asynchronous Communication**: Components interact via publish/subscribe messaging
3. **Extensibility**: Plugin system allows adding new capabilities
4. **Persistence**: State management with fractal memory systems
5. **Graceful Degradation**: Optional features fail gracefully
6. **Security**: PrimeLoyalty system ensures ethical constraints

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    VictorBrain                          │
│  (Main Orchestrator & Coordinator)                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │      BrainFractalPulseExchange                │   │
│  │  (Async Message Bus / Event System)           │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │      ASICoreDataContainer                     │   │
│  │  - Configuration                               │   │
│  │  - Memory System                               │   │
│  │  - NLP Tokenizers                              │   │
│  └────────────────────────────────────────────────┘   │
│                                                          │
│  ┌────────────────────────────────────────────────┐   │
│  │         Cognitive Sectors                      │   │
│  │  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │Input         │  │Cognitive     │           │   │
│  │  │Processing    │  │Executive     │           │   │
│  │  └──────────────┘  └──────────────┘           │   │
│  │  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │Memory        │  │NLG Output    │           │   │
│  │  │Sector        │  │Sector        │           │   │
│  │  └──────────────┘  └──────────────┘           │   │
│  │  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │Prime         │  │Modular       │           │   │
│  │  │Loyalty       │  │Plugin        │           │   │
│  │  └──────────────┘  └──────────────┘           │   │
│  └────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. VictorBrain (victor_core/brain.py)

**Purpose**: Main orchestrator and lifecycle manager

**Responsibilities**:
- Initialize all cognitive sectors
- Manage startup/shutdown sequences
- Coordinate inter-sector communication
- Monitor system health
- Handle main processing loop

**Key Methods**:
- `start()`: Initialize and activate all sectors
- `stop()`: Graceful shutdown of all components
- `inject_raw_input()`: Entry point for external stimuli
- `activate_all_sectors()`: Activate cognitive sectors
- `deactivate_all_sectors()`: Deactivate cognitive sectors

### 2. BrainFractalPulseExchange (victor_core/messaging/pulse_exchange.py)

**Purpose**: Asynchronous message bus for inter-component communication

**Features**:
- Topic-based publish/subscribe pattern
- Async event processing
- Queue-based message delivery
- Graceful start/stop mechanisms

**Key Methods**:
- `publish(topic, message, sender_id)`: Broadcast message to topic
- `subscribe(topic, callback)`: Register listener for topic
- `unsubscribe(topic, callback)`: Remove listener
- `start_pulse()`: Begin message processing
- `stop_pulse()`: Shutdown message system

**Communication Patterns**:
```
Publisher → Topic → Subscribers
   ↓         ↓         ↓
Async    Event Q   Callbacks
```

### 3. ASICoreDataContainer (victor_core/brain.py)

**Purpose**: Centralized resource container for shared components

**Contains**:
- **Configuration** (ASIConfigCore): System-wide settings
- **Memory** (HyperFractalMemory): Persistent storage with semantic search
- **NLP Tokenizer** (FractalTokenKernel): Text processing
- **Code Tokenizer**: Specialized for code analysis
- **Pulse Exchange**: Reference to message bus

**Design Pattern**: Dependency Injection Container

### 4. Cognitive Sectors

All sectors inherit from `VictorSector` base class and follow standard lifecycle:

#### InputProcessingSector (victor_core/sectors/input_processing.py)

**Purpose**: Process raw input and normalize for system consumption

**Functionality**:
- Text tokenization
- Code parsing
- Metadata extraction
- Input validation

**Topics**:
- Subscribes: `input.raw_text`, `input.raw_code`
- Publishes: `input.processed`, `input.tokenized`

#### CognitiveExecutiveSector (victor_core/sectors/cognitive_executive.py)

**Purpose**: High-level reasoning and decision making

**Components**:
- DirectiveCoreEngine: Command processing
- VictorCognitiveLoop: Main reasoning loop

**Functionality**:
- Parse directives/commands
- Execute reasoning processes
- Coordinate complex operations
- Decision validation

**Topics**:
- Subscribes: `input.processed`, `directive.execute`
- Publishes: `directive.completed`, `decision.made`

#### MemorySector (victor_core/sectors/memory_sector.py)

**Purpose**: Memory management and retrieval

**Functionality**:
- Store experiences and knowledge
- Semantic search with FAISS
- Memory consolidation
- Relevance-based retrieval

**Topics**:
- Subscribes: `memory.store_request`, `memory.search_request`
- Publishes: `memory.operation_success`, `memory.search_results`

#### NLGOutputSector (victor_core/sectors/nlg_output.py)

**Purpose**: Generate natural language responses

**Functionality**:
- Template-based generation
- Context-aware responses
- Output formatting

**Topics**:
- Subscribes: `nlg.generate_text_request`
- Publishes: `nlg.text_generated`

#### PrimeLoyaltySector (victor_core/sectors/prime_loyalty_sector.py)

**Purpose**: Enforce ethical constraints and loyalty protocols

**Functionality**:
- Pre-execution validation
- Ethical assessment
- Loyalty verification
- Critical decision oversight

**Security Features**:
- Creator signature validation
- Approved entity verification
- Action auditing

**Topics**:
- Subscribes: `directive.pre_execution`, `system.critical_decision_request`
- Publishes: `alert.loyalty_conflict`, `event.loyalty_affirmed`

#### ModularPluginSector (victor_core/sectors/modular_plugin_sector.py)

**Purpose**: Dynamic plugin loading and management

**Functionality**:
- Scan plugin directory
- Load plugin manifests
- Initialize plugin modules
- Manage plugin lifecycle

**Plugin Structure**:
```
victor_plugins/
└── plugin_name/
    ├── __init__.py
    ├── manifest.json
    └── [additional modules]
```

### 5. Memory System (victor_core/memory/hyper_fractal_memory.py)

**Purpose**: Sophisticated memory storage with semantic search

**Features**:
- FAISS vector indexing
- Emotional impact tracking
- Relevance-based decay
- Concept induction
- Persistent storage (JSON + FAISS index)

**Key Operations**:
- `store_memory()`: Add new memory
- `search()`: Semantic search by query
- `retrieve_recent()`: Time-based retrieval
- `decay_memory()`: Relevance-based forgetting
- `save_to_disk()`: Persistence

**Memory Entry Structure**:
```python
{
    "id": "unique_id",
    "content": "memory content",
    "timestamp": 1234567890.0,
    "context": {},
    "emotional_impact": 0.5,
    "relevance_score": 1.0,
    "access_count": 0,
    "tags": [],
    "embedding": [...]  # Vector for semantic search
}
```

### 6. NLP System (victor_core/nlp/fractal_tokenizer.py)

**Purpose**: Natural language processing and tokenization

**Features**:
- Custom vocabulary training
- Text normalization
- Keyword extraction
- Fractal dimension calculation
- Token hashing

**Key Methods**:
- `train(corpus)`: Build vocabulary from text
- `tokenize(text)`: Convert text to tokens
- `detokenize(tokens)`: Reconstruct text
- `get_keyword_hashes()`: Extract and hash keywords

## Advanced Modules (victor_modules/)

### Quantum Module (victor_modules/quantum/zero_point_quantum_driver.py)

Simulates zero-point energy compression and metaphysical embedding concepts for unique data transformations.

### Fractal AGI Module (victor_modules/fractal_agi/)

Conceptual self-contained AGI persistence with fractal logic and simulated quantum annealing.

## GUI Interfaces

### VICTOR_AGI_LLM.py

**Features**:
- Interactive command center
- Module management
- Variable inspection
- Timeline/state management
- Code execution
- System diagnostics

**Architecture**:
```
InfiniteDevUI (Main Window)
├── Chat Interface
├── Module Manager
├── Variable Inspector
├── Timeline Controls
├── Code Editor
└── Diagnostics Panel
```

### Dataset Trainer GUI

Specialized interface for model training with:
- Dataset loading
- Training configuration
- Progress monitoring
- Live metrics display

## Data Flow

### Input Processing Flow

```
External Input
    ↓
VictorBrain.inject_raw_input()
    ↓
Publish to "input.raw_text"
    ↓
InputProcessingSector.handle_raw_text_input()
    ↓
Tokenization + Metadata
    ↓
Publish to "input.processed"
    ↓
CognitiveExecutiveSector receives
    ↓
Process and generate response
    ↓
Publish to "nlg.generate_text_request"
    ↓
NLGOutputSector generates response
    ↓
Output to user
```

### Memory Storage Flow

```
Experience/Knowledge
    ↓
Publish to "memory.store_request"
    ↓
MemorySector.handle_store_request()
    ↓
HyperFractalMemory.store_memory()
    ↓
Generate embedding
    ↓
Store in FAISS index
    ↓
Save to JSON
    ↓
Publish "memory.operation_success"
```

## Configuration (victor_core/config.py)

**ASIConfigCore** provides system-wide settings:

- `DIMENSIONS`: Embedding dimensionality (128)
- `ATTENTION_MAX_DEPTH`: Attention mechanism depth (3)
- `MEMORY_RETENTION_THRESHOLD`: Memory decay threshold (0.05)
- `MAX_CONTEXT_WINDOW`: Context size (10)
- `MAX_TOKENIZER_KEYWORDS`: Keyword extraction limit (3)
- `PLUGIN_DIR`: Plugin directory path ("victor_plugins")
- `MIN_EMOTIONAL_RELEVANCE`: Emotional filtering (0.25)
- `CONCEPT_INDUCTION_THRESHOLD`: Concept learning (3)
- `CONCEPT_SIMILARITY_THRESHOLD`: Concept matching (0.65)

## Logging System (victor_core/logger.py)

**VictorLoggerStub** provides structured logging:

**Features**:
- Component-based logging
- Timestamp formatting (ISO 8601)
- Log level filtering (DEBUG, INFO, WARN, ERROR, CRITICAL)
- Stack trace capture
- Thread-safe operations

**Usage**:
```python
logger = VictorLoggerStub(component="ComponentName")
logger.info("Message")
logger.error("Error", exc_info=True)
```

## Async Architecture

The system is built on Python's `asyncio` for concurrent operations:

**Benefits**:
- Non-blocking I/O
- Concurrent sector operations
- Efficient event processing
- Scalable message handling

**Patterns Used**:
- Async/await for coroutines
- Task creation for concurrent ops
- Queue-based message passing
- Event-driven architecture

## Extension Points

### Creating a Custom Sector

1. Inherit from `VictorSector`
2. Override `activate()` and `deactivate()`
3. Subscribe to relevant topics
4. Implement event handlers
5. Publish results to output topics

Example:
```python
class CustomSector(VictorSector):
    def __init__(self, pulse_exchange, name, asi_core_ref):
        super().__init__(pulse_exchange, name, asi_core_ref)
        
    async def activate(self):
        await super().activate()
        self.pulse_exchange.subscribe("custom.input", self.handle_input)
        
    async def handle_input(self, message, sender_id):
        # Process message
        result = self.process(message)
        await self.pulse_exchange.publish("custom.output", result)
```

### Creating a Plugin

1. Create directory in `victor_plugins/`
2. Add `__init__.py` with initialization
3. Create `manifest.json` with metadata
4. Implement entry point functions

manifest.json:
```json
{
    "name": "my_plugin",
    "version": "1.0.0",
    "description": "Plugin description",
    "author": "Your Name",
    "entry_points": {
        "main_function": "function_name"
    }
}
```

## Performance Considerations

### Memory Management

- FAISS for efficient vector search
- Relevance-based memory decay
- Configurable retention thresholds
- Lazy loading of large datasets

### Scalability

- Async processing for I/O operations
- Decoupled sector communication
- Pluggable architecture
- Configurable resource limits

### Optimization Tips

1. Adjust `MAX_CONTEXT_WINDOW` for memory usage
2. Tune `MEMORY_RETENTION_THRESHOLD` for performance
3. Use `VICTOR_LOG_LEVEL=WARN` in production
4. Clear old memory periodically
5. Monitor sector health metrics

## Security Features

### PrimeLoyalty System

- Creator signature verification
- Approved entity validation
- Action auditing
- Ethical constraint enforcement

### Best Practices

1. Never commit API keys
2. Use environment variables for secrets
3. Validate plugin code before loading
4. Review sector permissions
5. Monitor loyalty alerts

## Future Enhancements

Planned improvements include:

1. **Distributed Sectors**: Multi-process/machine deployment
2. **Enhanced NLP**: Transformer-based models
3. **Visual Processing**: Computer vision integration
4. **Reinforcement Learning**: Self-improvement loops
5. **Multi-Agent**: Sector specialization and collaboration
6. **Real-time Adaptation**: Dynamic configuration updates
7. **Advanced Memory**: Hierarchical memory structures
8. **Federated Learning**: Privacy-preserving training

## Glossary

- **Sector**: Specialized cognitive module
- **Pulse**: Message/event in the system
- **ASI**: Artificial Super Intelligence
- **NLP**: Natural Language Processing
- **NLG**: Natural Language Generation
- **FAISS**: Facebook AI Similarity Search
- **Fractal**: Self-similar recursive structure
- **Tokenizer**: Text-to-token converter

## References

- Main README: [README.md](README.md)
- Quick Start: [QUICKSTART.md](QUICKSTART.md)
- Performance Tuning: [docs/perf_tuning.md](docs/perf_tuning.md)

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-10-31  
**Maintained By**: Victor Prime Development Team
