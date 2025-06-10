import asyncio
import numpy as np # For potential future use with embeddings, decisions
from victor_core.sectors.base import VictorSector
from victor_core.messaging.pulse_exchange import BrainFractalPulseExchange

# Placeholder for DirectiveCoreEngine if not detailed
class DirectiveCoreEngine:
    def __init__(self, asi_core_ref=None, logger=None):
        self.asi_core = asi_core_ref
        self.logger = logger if logger else VictorLoggerStub(component="DirectiveCoreEngine")
        self.logger.info("DirectiveCoreEngine initialized.")

    def generate_directive(self, processed_input):
        """
        Analyzes processed input and generates a directive for action.
        This is a core part of the AGI's "thinking" process.
        Placeholder implementation.
        """
        self.logger.debug(f"Generating directive for input: {processed_input.get('original_text', 'N/A')[:50]}")

        # Example logic: if input contains "urgent", create a high-priority task
        action_type = "process_information" # Default action
        priority = 0.5 # Default priority
        details = {"summary": processed_input.get('original_text', 'Input received'),
                   "input_hash": processed_input.get('content_hash', None)} # Assuming input has a hash

        if "urgent" in processed_input.get('original_text', '').lower():
            priority = 0.9
            action_type = "immediate_action_query" # Fictitious action type
            self.logger.info("High priority 'urgent' task identified.")

        elif "question" in processed_input.get('original_text', '').lower() or \
             processed_input.get('original_text', '').endswith("?"):
            action_type = "answer_query"
            priority = 0.7
            self.logger.info("Question identified, routing to answer_query.")

        directive = {
            "action": action_type,
            "details": details,
            "priority": priority,
            "source_input_id": processed_input.get("processor_id"), # ID of the InputProcessingSector message
            "origin_sender_id": processed_input.get("sender_id") # Original publisher to input.processed_text
        }
        self.logger.info(f"Generated directive: {directive['action']} with priority {directive['priority']:.2f}")
        return directive

# Placeholder for VictorCognitiveLoop if not detailed
class VictorCognitiveLoop:
    def __init__(self, logger=None):
        self.host_sector = None # The CognitiveExecutiveSector instance
        self.directive_queue = asyncio.Queue() # Using asyncio.Queue for async operations
        self.is_running = False
        self.logger = logger if logger else VictorLoggerStub(component="VictorCognitiveLoop")
        self._processing_task = None
        self.logger.info("VictorCognitiveLoop initialized.")

    def register_host(self, host_sector_instance):
        self.host_sector = host_sector_instance
        self.logger.info(f"Cognitive loop registered to host sector: {host_sector_instance.name}")

    async def pulse_directive(self, directive):
        """Receives a new directive and adds it to the queue."""
        await self.directive_queue.put(directive)
        self.logger.debug(f"Directive pulsed into cognitive loop: {directive.get('action')}")

    async def start(self):
        if not self.is_running:
            self.is_running = True
            self._processing_task = asyncio.create_task(self._process_directives())
            self.logger.info("Cognitive loop started processing.")
        else:
            self.logger.info("Cognitive loop is already running.")

    async def stop(self):
        if self.is_running:
            self.is_running = False
            if self._processing_task:
                # Signal the loop to stop by putting a None sentinel, or just cancel
                await self.directive_queue.put(None) # Sentinel to stop the loop gracefully
                try:
                    await asyncio.wait_for(self._processing_task, timeout=5.0)
                    self.logger.info("Cognitive loop processing task stopped gracefully.")
                except asyncio.TimeoutError:
                    self.logger.warn("Cognitive loop processing task did not stop gracefully, cancelling.")
                    self._processing_task.cancel()
                except asyncio.CancelledError:
                     self.logger.info("Cognitive loop processing task was cancelled.")
            self.logger.info("Cognitive loop stopped.")


    async def _process_directives(self):
        """Continuously processes directives from the queue."""
        while self.is_running:
            try:
                directive = await self.directive_queue.get()
                if directive is None: # Sentinel value to stop
                    self.logger.info("Cognitive loop received stop sentinel.")
                    break

                self.logger.info(f"Cognitive loop processing directive: {directive.get('action')} (Priority: {directive.get('priority', 0)})")

                if self.host_sector:
                    # The host sector (CognitiveExecutiveSector) is responsible for acting on the directive
                    await self.host_sector.execute_directive(directive)
                else:
                    self.logger.warn("No host sector registered to execute directive.")

                self.directive_queue.task_done() # Mark task as complete
            except asyncio.CancelledError:
                self.logger.info("Cognitive loop processing task was cancelled during get/process.")
                break
            except Exception as e:
                self.logger.error(f"Error in cognitive loop while processing directive: {e}", exc_info=True)
                # Potentially requeue, or send to error handling topic
        self.logger.info("Cognitive loop processing ended.")


class CognitiveExecutiveSector(VictorSector):
    def __init__(self, pulse_exchange_instance: BrainFractalPulseExchange, name: str, asi_core_ref):
        super().__init__(pulse_exchange_instance, name, asi_core_ref)
        self.dce = DirectiveCoreEngine(asi_core_ref=self.asi_core, logger=self.logger) # Pass logger
        self.focus_loop = VictorCognitiveLoop(logger=self.logger) # Pass logger
        self.focus_loop.register_host(self) # Cognitive loop needs reference to its host sector
        self.logger.info("CognitiveExecutiveSector initialized with DirectiveCoreEngine and VictorCognitiveLoop.")

    async def activate(self):
        await super().activate()
        # Subscribe to processed inputs that need decision making
        await self.pulse_exchange.subscribe("input.processed_text", self.handle_processed_input)
        await self.pulse_exchange.subscribe("input.processed_code", self.handle_processed_input) # Can handle both
        await self.focus_loop.start()
        self.logger.info("CognitiveExecutiveSector activated and subscribed to processed inputs.")

    async def deactivate(self):
        await self.pulse_exchange.unsubscribe("input.processed_text", self.handle_processed_input)
        await self.pulse_exchange.unsubscribe("input.processed_code", self.handle_processed_input)
        await self.focus_loop.stop()
        await super().deactivate()
        self.logger.info("CognitiveExecutiveSector deactivated.")

    async def handle_processed_input(self, message_data, sender_id):
        """Receives processed input, generates a directive, and pulses it to the cognitive loop."""
        self.logger.debug(f"CognitiveExecutive received processed input from {sender_id}.")

        # Use Directive Core Engine to analyze input and create a plan/directive
        directive = self.dce.generate_directive(message_data)

        if directive:
            # Pulse the directive into the cognitive loop for execution scheduling
            await self.focus_loop.pulse_directive(directive)
            self.logger.info(f"Directive for action '{directive['action']}' pulsed to cognitive loop.")
        else:
            self.logger.warn("DCE did not generate a directive for the input.")

    async def execute_directive(self, directive):
        """
        Executes a directive from the cognitive loop.
        This involves coordinating with other sectors/components via asi_core_ref or pulse_exchange.
        """
        action = directive.get("action")
        details = directive.get("details")
        priority = directive.get("priority", 0.5)
        self.logger.info(f"Executing directive: {action} with priority {priority:.2f}. Details: {details}")

        # Example actions:
        if action == "store_memory":
            if self.asi_core and hasattr(self.asi_core, 'memory_sector'):
                # This implies memory_sector has a method like handle_store_directive
                await self.pulse_exchange.publish(
                    topic=f"sector.{self.asi_core.memory_sector.name}.command", # Send to Memory Sector
                    message={"command": "store_from_directive", "data": details},
                    sender_id=self.sector_id
                )
            else:
                self.logger.warn("Memory sector not available in asi_core_ref to store memory.")

        elif action == "retrieve_memory_query":
            # ... similar logic to publish to memory sector ...
            pass

        elif action == "answer_query":
            # This might involve retrieving info from memory, then generating text via NLG sector
            self.logger.info(f"Query received: {details.get('summary')}. Needs memory retrieval and NLG.")
            # 1. Formulate memory search query based on `details`
            # 2. Send to MemorySector
            # 3. On memory_sector response, send to NLGOutputSector
            # This is a multi-step process, might need a small state machine or sub-directives
            await self.pulse_exchange.publish(
                topic="task.chain.start_query_answering", # Example of a complex task topic
                message={"directive": directive},
                sender_id=self.sector_id
            )

        elif action == "process_information":
            # This might be a simpler form of memory storage or analysis
            self.logger.info(f"Processing information: {details.get('summary')}")
            # For now, let's just log it. Could involve deeper analysis or learning.
            if self.asi_core and hasattr(self.asi_core, 'memory') and hasattr(self.asi_core.memory, 'store_memory_entry'):
                 # Simplified direct storage for "process_information"
                 # This assumes 'details' contains enough for store_memory_entry or it's adapted
                 text_summary = details.get('summary', 'Generic information')
                 content_data = {"raw_details": details, "source": directive.get("origin_sender_id")}
                 # keyword_hashes might come from the input processing earlier, or re-derived
                 # For now, using placeholder keywords based on summary
                 keyword_hashes_from_summary = [word.lower() for word in text_summary.split()[:3]]


                 # This is a direct call for simplicity in this example.
                 # In a full system, this would likely still go via MemorySector through pulse.
                 try:
                    self.asi_core.memory.store_memory_entry(
                        content_data=content_data,
                        text_summary=text_summary,
                        keyword_hashes=keyword_hashes_from_summary,
                        emotional_tags={"importance": priority} # map priority to an emotion
                    )
                    self.logger.info(f"Information '{text_summary[:30]}' processed and stored in memory directly by CogExec.")
                 except Exception as e:
                    self.logger.error(f"CogExec failed to directly store info in memory: {e}", exc_info=True)


            else:
                self.logger.warn("Memory or store_memory_entry not available for 'process_information'.")


        elif action == "idle":
            self.logger.debug("Cognitive loop directive: idle. No action taken.")

        else:
            self.logger.warn(f"Unknown directive action: {action}. No execution routine defined.")

        # After execution, potentially publish completion or result
        await self.pulse_exchange.publish(
            topic=f"directive.executed.{action}",
            message={"directive": directive, "status": "completed"}, # Add more result details if any
            sender_id=self.sector_id
        )


# Example of how asi_core_ref might be structured for CognitiveExecutive
class MockASICoreForCognitive:
    def __init__(self, pulse_exchange):
        from victor_core.memory.hyper_fractal_memory import HyperFractalMemory # Example
        self.pulse_exchange = pulse_exchange
        self.memory = HyperFractalMemory(storage_path="bando_agi_persistent/cog_exec_test_memory.json") # Example memory
        # self.nlp_tokenizer = ... # If DCE needs it directly (passed to DCE constructor)
        # self.memory_sector = ... # If CogExec sends directives to MemorySector (placeholder for now)
        self.logger = VictorLoggerStub(component="MockASICoreForCognitive")

async def main_cognitive_sector_example():
    from victor_core.logger import VictorLoggerStub
    example_logger = VictorLoggerStub(component="CognitiveSectorExample")
    example_logger.log_level_str = "DEBUG"
    example_logger.current_log_level_int = example_logger.log_levels_map.get(example_logger.log_level_str, 1)

    pulse_exchange = BrainFractalPulseExchange()
    await pulse_exchange.start_pulse()

    # Mock subscriber to see directives being executed
    async def directive_executed_subscriber(message, sender_id):
        example_logger.info(f"Directive Executed Subscriber GOT: {message.get('directive', {}).get('action')} from {sender_id}")

    await pulse_exchange.subscribe("directive.executed.*", directive_executed_subscriber) # Wildcard for all actions

    asi_core = MockASICoreForCognitive(pulse_exchange)
    # Clean up test memory file from previous runs if any
    import os
    if os.path.exists("bando_agi_persistent/cog_exec_test_memory.json"):
        os.remove("bando_agi_persistent/cog_exec_test_memory.json")
    asi_core.memory = HyperFractalMemory(storage_path="bando_agi_persistent/cog_exec_test_memory.json") # re-init for clean test
    asi_core.memory.logger = example_logger # use verbose logger

    cognitive_sector = CognitiveExecutiveSector(pulse_exchange, "CognitiveExec", asi_core)
    cognitive_sector.logger = example_logger # use more verbose logger for example
    cognitive_sector.dce.logger = example_logger
    cognitive_sector.focus_loop.logger = example_logger

    await cognitive_sector.activate()

    # Simulate a processed text input message
    sample_processed_input = {
        "original_text": "This is an important question: what is the meaning of life? And it is urgent.",
        "tokens": [1,2,3,4,5,6,7,8,9,10,11,12,13,14], # Dummy tokens
        "token_count": 14,
        "keyword_hashes": ["important", "question", "meaning_of_life", "urgent"],
        "fractal_dimension": 0.75,
        "processor_id": "input_processor_dummy_id",
        "sender_id": "input_processor_dummy_id" # In reality, this is the ID of the InputProcessingSector instance
    }
    await pulse_exchange.publish("input.processed_text", sample_processed_input, "InputProcessingSectorMock")

    await asyncio.sleep(1) # Allow time for processing

    await cognitive_sector.deactivate()
    await pulse_exchange.stop_pulse()

    # Check memory content (optional)
    # results = asi_core.memory.search_memories(keyword_hashes=["question"])
    # example_logger.info(f"Memory search for 'question' yielded {len(results)} results.")
    # if results:
    #     example_logger.info(f"First result: {results[0]['text_summary']}")


if __name__ == "__main__":
    # asyncio.run(main_cognitive_sector_example())
    print("CognitiveExecutiveSector class defined. Example can be run by uncommenting asyncio.run.")
