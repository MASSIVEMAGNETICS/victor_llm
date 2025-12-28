import asyncio
import time # For main loop timing, integrity checks etc.
import uuid # For generating instance IDs if needed
from pathlib import Path

from victor_core.messaging.pulse_exchange import BrainFractalPulseExchange
from victor_core.logger import VictorLoggerStub
from victor_core.config import ASIConfigCore
from victor_core.memory.hyper_fractal_memory import HyperFractalMemory
from victor_core.nlp.fractal_tokenizer import FractalTokenKernel_v1_1_0

# Import all sector classes
from victor_core.sectors.base import VictorSector # Though not directly instantiated, good for type hints
from victor_core.sectors.input_processing import InputProcessingSector
from victor_core.sectors.cognitive_executive import CognitiveExecutiveSector
from victor_core.sectors.memory_sector import MemorySector
from victor_core.sectors.nlg_output import NLGOutputSector
from victor_core.sectors.prime_loyalty_sector import PrimeLoyaltySector
from victor_core.sectors.modular_plugin_sector import ModularPluginSector

# A container for shared core components accessible by sectors via asi_core_ref
class ASICoreDataContainer:
    def __init__(self, pulse_exchange_instance, logger_parent_component="ASICore"):
        self.instance_id = str(uuid.uuid4())
        self.logger = VictorLoggerStub(component=f"{logger_parent_component}_DataContainer")
        self.config = ASIConfigCore() # Global configuration settings

        # Initialize core components that sectors will use
        self.memory = HyperFractalMemory(
            storage_path=f"{self.config.PLUGIN_DIR.replace('plugins','bando_persistent')}/main_memory_bank.json", # Example path construction
            config=self.config
        )
        self.memory.logger.component = f"{logger_parent_component}_HyperFractalMemory" # Standardize logger component name

        self.pulse_exchange = pulse_exchange_instance # Shared pulse exchange

        self.nlp_tokenizer = FractalTokenKernel_v1_1_0(
            pulse_exchange=self.pulse_exchange,
            config=self.config
        )
        self.nlp_tokenizer.logger.component = f"{logger_parent_component}_NLPTokenizer"

        # Example: separate tokenizer for code, could be the same class or specialized
        self.code_tokenizer = FractalTokenKernel_v1_1_0(
            pulse_exchange=self.pulse_exchange,
            config=self.config
        )
        self.code_tokenizer.logger.component = f"{logger_parent_component}_CodeTokenizer"

        tokenizer_dir = Path(self.config.TOKENIZER_DIR)
        tokenizer_dir.mkdir(parents=True, exist_ok=True)

        nlp_tokenizer_path = tokenizer_dir / "nlp_tokenizer.json"
        code_tokenizer_path = tokenizer_dir / "code_tokenizer.json"

        loaded_nlp = self.nlp_tokenizer.load_from_file(str(nlp_tokenizer_path))
        loaded_code = self.code_tokenizer.load_from_file(str(code_tokenizer_path))

        # Train tokenizers with some basic data if they are empty (example)
        if not loaded_nlp and not self.nlp_tokenizer.vocabulary:
            self.nlp_tokenizer.train(["hello world example", "victor agi system online"])
        if not loaded_code and not self.code_tokenizer.vocabulary:
            self.code_tokenizer.train(["def func(): pass", "import sys", "print('code example')"])

        # Reference to the main asyncio loop if needed by components (usually not directly)
        # self.async_loop = asyncio.get_running_loop() # This can only be called if loop is running
        self.logger.info(f"ASICoreDataContainer (Instance: {self.instance_id}) initialized with core components.")


class VictorBrain:
    def __init__(self, creator_signature_for_plk="DefaultVictorCreator", approved_entities_for_plk=None):
        self.brain_instance_id = str(uuid.uuid4())
        self.logger = VictorLoggerStub(component=f"VictorBrain_{self.brain_instance_id[:8]}")

        self.pulse_exchange = BrainFractalPulseExchange()
        self.pulse_exchange.logger.component = "VictorBrain_PulseExchange" # Standardize logger name

        # Initialize the ASI Core Data Container which holds shared components
        # The logger component name for ASICoreDataContainer and its sub-components will reflect this brain instance
        self.asi_core_data_container = ASICoreDataContainer(
            pulse_exchange_instance=self.pulse_exchange,
            logger_parent_component=f"VictorBrain_{self.brain_instance_id[:8]}"
        )
        # For convenience, make config directly accessible
        self.config = self.asi_core_data_container.config

        self.sectors = {} # Dictionary to hold sector instances
        self._register_sectors(creator_signature_for_plk, approved_entities_for_plk or ["VictorInternalOps"])

        self._is_running = False
        self._main_loop_task = None
        self.last_integrity_check_time = time.monotonic()
        self.last_memory_decay_time = time.monotonic()

        self.logger.info(f"VictorBrain (Instance: {self.brain_instance_id}) initialized. ASI Core ID: {self.asi_core_data_container.instance_id}")

    def _register_sectors(self, creator_signature, approved_entities):
        self.logger.info("Registering core sectors...")
        sector_definitions = [
            {"name": "InputProcessing", "class": InputProcessingSector, "args": []},
            {"name": "CognitiveExecutive", "class": CognitiveExecutiveSector, "args": []},
            {"name": "Memory", "class": MemorySector, "args": []},
            {"name": "NLGOutput", "class": NLGOutputSector, "args": []},
            {"name": "PrimeLoyalty", "class": PrimeLoyaltySector, "args": [creator_signature, approved_entities]},
            {"name": "ModularPlugin", "class": ModularPluginSector, "args": []}, # Will use config from asi_core_data_container
        ]

        for sector_def in sector_definitions:
            name = sector_def["name"]
            SectorClass = sector_def["class"]
            args = sector_def["args"]
            try:
                sector_instance = SectorClass(self.pulse_exchange, name, self.asi_core_data_container, *args)
                # Standardize logger component names for sectors too
                sector_instance.logger.component = f"VictorBrain_{self.brain_instance_id[:8]}_Sector_{name}"
                self.sectors[name] = sector_instance
                self.logger.info(f"Sector '{name}' registered successfully.")
            except Exception as e:
                self.logger.error(f"Failed to register sector '{name}': {e}", exc_info=True)
                # Depending on criticality, might re-raise or handle

        # Make specific sectors easily accessible if needed often (though asi_core_data_container is the primary route for shared components)
        # self.asi_core_data_container.input_sector = self.sectors.get("InputProcessing")
        # self.asi_core_data_container.cognitive_sector = self.sectors.get("CognitiveExecutive")
        # self.asi_core_data_container.memory_sector = self.sectors.get("Memory") # MemorySector itself, not HyperFractalMemory
        # ... and so on. This provides sectors a way to reference other sectors via asi_core if absolutely necessary,
        # but primary communication should be via pulse_exchange.


    async def activate_all_sectors(self):
        self.logger.info("Activating all registered sectors...")
        for sector_name, sector_instance in self.sectors.items():
            try:
                await sector_instance.activate()
                self.logger.info(f"Sector '{sector_name}' activated.")
            except Exception as e:
                self.logger.error(f"Error activating sector '{sector_name}': {e}", exc_info=True)
        self.logger.info("All sectors have been requested to activate.")

    async def deactivate_all_sectors(self):
        self.logger.info("Deactivating all registered sectors...")
        for sector_name, sector_instance in self.sectors.items():
            try:
                await sector_instance.deactivate()
                self.logger.info(f"Sector '{sector_name}' deactivated.")
            except Exception as e:
                self.logger.error(f"Error deactivating sector '{sector_name}': {e}", exc_info=True)
        self.logger.info("All sectors have been requested to deactivate.")

    async def inject_raw_input(self, text_input: str, input_type: str = "text", metadata=None):
        """Injects raw input into the InputProcessingSector via the pulse exchange."""
        if not self._is_running:
            self.logger.warn("Brain is not running. Cannot inject input.")
            return

        if not text_input:
            self.logger.warn("Received empty text input for injection.")
            return

        metadata = metadata if metadata is not None else {}
        metadata["injection_timestamp"] = time.time()
        metadata["source"] = metadata.get("source", "external_injection")

        topic = "input.raw_text"
        payload = {"text": text_input, "metadata": metadata}

        if input_type == "code":
            topic = "input.raw_code"
            payload = {"code": text_input, "language": metadata.get("language", "unknown"), "metadata": metadata}

        elif input_type != "text":
            self.logger.warn(f"Unknown input_type '{input_type}'. Defaulting to 'text'.")
            topic = "input.raw_text" # ensure it's set

        self.logger.info(f"Injecting raw {input_type} input: '{text_input[:100]}...'")
        await self.pulse_exchange.publish(topic, payload, sender_id=f"VictorBrain_InputInjector_{self.brain_instance_id[:8]}")


    async def _a_main_loop(self):
        """The main asynchronous processing loop for VictorBrain."""
        self.logger.info(f"VictorBrain main loop starting. Brain ID: {self.brain_instance_id}")
        self._is_running = True

        try:
            while self._is_running:
                current_time = time.monotonic()

                # 1. Sector Processing (Sectors primarily operate via pulse, this loop is for periodic tasks)
                #    Most sector work is event-driven via the pulse_exchange.
                #    This loop can orchestrate periodic tasks within sectors if needed,
                #    or sectors can manage their own internal periodic tasks using asyncio.create_task.

                # 2. Memory Decay and Maintenance (Periodic)
                if current_time - self.last_memory_decay_time >= self.config.PULSE_LOG_MAXLEN: # Using PULSE_LOG_MAXLEN as a stand-in for a proper interval config
                    self.logger.debug("Performing periodic memory maintenance.")
                    if hasattr(self.asi_core_data_container.memory, 'perform_maintenance'):
                        try:
                            # perform_maintenance should be relatively quick or async itself.
                            # If it's blocking, it needs to be run in an executor.
                            # For now, assuming it's designed to be non-blocking or very fast.
                            self.asi_core_data_container.memory.perform_maintenance()
                        except Exception as e:
                            self.logger.error(f"Error during periodic memory maintenance: {e}", exc_info=True)
                    self.last_memory_decay_time = current_time

                # 3. System Integrity Checks (Periodic)
                if current_time - self.last_integrity_check_time >= 60: # Example: every 60 seconds
                    self.logger.debug("Performing periodic system integrity checks.")
                    # Example: Check status of all sectors
                    for sector_name, sector in self.sectors.items():
                        if not sector.is_active or sector.status != "active":
                            self.logger.warn(f"Integrity Check: Sector '{sector_name}' is not active or in a non-active status ('{sector.status}'). Attempting to report.")
                            if hasattr(sector, 'report_status'): # report_status is async
                                asyncio.create_task(sector.report_status()) # Fire and forget status report
                    # Add more integrity checks as needed (e.g., pulse exchange health, resource usage)
                    self.last_integrity_check_time = current_time

                # Yield control to other asyncio tasks. This determines the "tick rate" of the main loop.
                await asyncio.sleep(self.config.MAX_CONTEXT_WINDOW / 100.0 if self.config.MAX_CONTEXT_WINDOW > 0 else 0.1) # Example interval calculation

        except asyncio.CancelledError:
            self.logger.info("VictorBrain main loop was cancelled.")
        except Exception as e:
            self.logger.critical(f"Critical error in VictorBrain main loop: {e}", exc_info=True)
            # This might be a place to trigger a graceful shutdown or restart sequence
        finally:
            self.logger.info("VictorBrain main loop finished.")
            self._is_running = False # Ensure flag is cleared

    async def start(self):
        """Starts the VictorBrain's main processing loop and activates components."""
        if self._is_running:
            self.logger.warn("VictorBrain is already running.")
            return

        self.logger.info("VictorBrain starting...")
        await self.pulse_exchange.start_pulse() # Start the pulse exchange's own processing loop
        await self.activate_all_sectors()

        self._main_loop_task = asyncio.create_task(self._a_main_loop())
        self.logger.info("VictorBrain started successfully.")

    async def stop(self):
        """Stops the VictorBrain's main processing loop and deactivates components."""
        if not self._is_running and (not self._main_loop_task or self._main_loop_task.done()):
            self.logger.warn("VictorBrain is not running or already stopped.")
            return

        self.logger.info("VictorBrain stopping...")
        self._is_running = False # Signal the main loop to stop

        if self._main_loop_task and not self._main_loop_task.done():
            self.logger.debug("Attempting to cancel main loop task...")
            self._main_loop_task.cancel()
            try:
                await self._main_loop_task # Wait for the loop to finish cancellation
                self.logger.info("Main loop task cancelled successfully.")
            except asyncio.CancelledError:
                self.logger.info("Main loop task was indeed cancelled (caught here too).")
            except Exception as e:
                self.logger.error(f"Exception while waiting for main loop task to cancel: {e}", exc_info=True)

        await self.deactivate_all_sectors()
        await self.pulse_exchange.stop_pulse() # Stop the pulse exchange's processing

        # Persist memory one last time
        if hasattr(self.asi_core_data_container.memory, '_save_memory'):
            try:
                self.logger.info("Saving memory state before final shutdown...")
                self.asi_core_data_container.memory._save_memory()
            except Exception as e:
                self.logger.error(f"Error saving memory during shutdown: {e}", exc_info=True)

        self.logger.info("VictorBrain stopped successfully.")

    def get_status(self):
        return {
            "brain_instance_id": self.brain_instance_id,
            "is_running": self._is_running,
            "asi_core_id": self.asi_core_data_container.instance_id,
            "sectors_count": len(self.sectors),
            "sector_statuses": {name: sector.status for name, sector in self.sectors.items()},
            "pulse_exchange_active": self.pulse_exchange.pulse_active,
        }
