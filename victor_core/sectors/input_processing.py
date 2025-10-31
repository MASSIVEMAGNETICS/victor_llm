import asyncio
import numpy as np # If tokenizers deal with numpy arrays for embeddings, or for future use
from victor_core.sectors.base import VictorSector
from victor_core.messaging.pulse_exchange import BrainFractalPulseExchange
# Assuming FractalTokenKernel_v1_1_0 is in fractal_tokenizer.py
# from victor_core.nlp.fractal_tokenizer import FractalTokenKernel_v1_1_0

class InputProcessingSector(VictorSector):
    def __init__(self, pulse_exchange_instance: BrainFractalPulseExchange, name: str, asi_core_ref):
        super().__init__(pulse_exchange_instance, name, asi_core_ref)
        # These tokenizers are expected to be attributes of asi_core_ref
        # e.g., self.asi_core.nlp_tokenizer and self.asi_core.code_tokenizer
        # They should be instances of FractalTokenKernel_v1_1_0 or similar.
        self.nlp_tokenizer = getattr(self.asi_core, 'nlp_tokenizer', None)
        self.code_tokenizer = getattr(self.asi_core, 'code_tokenizer', None) # Example for code

        if not self.nlp_tokenizer:
            self.logger.warn("NLP tokenizer not found in asi_core_ref. Input processing might be limited.")
        # Optional: check for code_tokenizer if it's critical
        # if not self.code_tokenizer:
        #     self.logger.warn("Code tokenizer not found in asi_core_ref.")

        self.logger.info(f"InputProcessingSector initialized. NLP Tokenizer: {'Present' if self.nlp_tokenizer else 'Absent'}")

    async def activate(self):
        await super().activate()
        # Subscribe to raw input topics
        self.pulse_exchange.subscribe("input.raw_text", self.handle_raw_text_input)
        self.pulse_exchange.subscribe("input.raw_code", self.handle_raw_code_input)
        self.logger.info("InputProcessingSector activated and subscribed to raw input topics.")

    async def deactivate(self):
        self.pulse_exchange.unsubscribe("input.raw_text", self.handle_raw_text_input)
        self.pulse_exchange.unsubscribe("input.raw_code", self.handle_raw_code_input)
        await super().deactivate()
        self.logger.info("InputProcessingSector deactivated and unsubscribed from raw input topics.")

    async def handle_raw_text_input(self, message_data, sender_id):
        """Processes raw text input, tokenizes it, and publishes structured data."""
        text = message_data.get("text")
        metadata = message_data.get("metadata", {})
        if not text:
            self.logger.warn("Received empty text input.")
            return

        self.logger.debug(f"Processing raw text input from {sender_id}: '{text[:100]}...'")

        if not self.nlp_tokenizer:
            self.logger.error("NLP Tokenizer not available. Cannot process text input.")
            await self.pulse_exchange.publish(
                topic="system.error",
                message={"error": "NLP_TOKENIZER_MISSING", "details": "InputProcessingSector cannot process text."},
                sender_id=self.sector_id
            )
            return

        try:
            tokens = self.nlp_tokenizer.tokenize(text)
            # keyword_hashes = self.nlp_tokenizer.get_keyword_hashes(text) # Assuming this method exists
            # fractal_dimension = self.nlp_tokenizer.calculate_fractal_dimension(text) # Assuming this

            # For now, let's simulate these if not fully implemented in the placeholder tokenizer
            keyword_hashes = [f"kw_hash_{i}" for i in range(min(3, len(tokens)))] if tokens else []
            fractal_dimension = 0.5 # Dummy value

            processed_input_data = {
                "original_text": text,
                "tokens": tokens,
                "token_count": len(tokens),
                "keyword_hashes": keyword_hashes,
                "fractal_dimension": fractal_dimension,
                "source_metadata": metadata,
                "processed_by": self.name,
                "processor_id": str(self.sector_id)
            }

            await self.pulse_exchange.publish(
                topic="input.processed_text", # Or a more generic "input.processed"
                message=processed_input_data,
                sender_id=self.sector_id
            )
            self.logger.info(f"Successfully processed and published text input. Tokens: {len(tokens)}")

        except Exception as e:
            self.logger.error(f"Error processing text input: {e}", exc_info=True)
            await self.pulse_exchange.publish(
                topic="system.error",
                message={"error": "TEXT_PROCESSING_FAILED", "details": str(e)},
                sender_id=self.sector_id
            )

    async def handle_raw_code_input(self, message_data, sender_id):
        """Processes raw code input, tokenizes it, and publishes structured data."""
        code = message_data.get("code")
        language = message_data.get("language", "unknown")
        metadata = message_data.get("metadata", {})

        if not code:
            self.logger.warn("Received empty code input.")
            return

        self.logger.debug(f"Processing raw code input ({language}) from {sender_id}: '{code[:100]}...'")

        if not self.code_tokenizer:
            self.logger.warn("Code Tokenizer not available. Treating code as plain text.")
            # Fallback to NLP tokenizer or a generic handler if code_tokenizer is absent
            if self.nlp_tokenizer:
                # Process as text but flag that it was code
                metadata["original_type"] = "code"
                metadata["code_language_hint"] = language
                await self.handle_raw_text_input({"text": code, "metadata": metadata}, sender_id)
            else:
                self.logger.error("No tokenizer available to process code input as fallback.")
                await self.pulse_exchange.publish(
                    topic="system.error",
                    message={"error": "CODE_TOKENIZER_MISSING", "details": "InputProcessingSector cannot process code and no NLP fallback."},
                    sender_id=self.sector_id
                )
            return

        try:
            # Assuming code_tokenizer has a similar interface to nlp_tokenizer
            tokens = self.code_tokenizer.tokenize(code)
            # keyword_hashes = self.code_tokenizer.get_keyword_hashes(code)
            # For now, simulate these:
            keyword_hashes = [f"code_kw_hash_{i}" for i in range(min(3, len(tokens)))] if tokens else []

            processed_code_data = {
                "original_code": code,
                "language": language,
                "tokens": tokens,
                "token_count": len(tokens),
                "keyword_hashes": keyword_hashes, # Or specific code structure hashes
                "source_metadata": metadata,
                "processed_by": self.name,
                "processor_id": str(self.sector_id)
            }

            await self.pulse_exchange.publish(
                topic="input.processed_code",
                message=processed_code_data,
                sender_id=self.sector_id
            )
            self.logger.info(f"Successfully processed and published code input ({language}). Tokens: {len(tokens)}")

        except Exception as e:
            self.logger.error(f"Error processing code input: {e}", exc_info=True)
            await self.pulse_exchange.publish(
                topic="system.error",
                message={"error": "CODE_PROCESSING_FAILED", "details": str(e)},
                sender_id=self.sector_id
            )


# Example of how asi_core_ref might be structured (simplified)
class MockASICoreForInput:
    def __init__(self, pulse_exchange):
        from victor_core.nlp.fractal_tokenizer import FractalTokenKernel_v1_1_0 # For example
        from victor_core.config import ASIConfigCore

        self.config = ASIConfigCore()
        # Initialize actual tokenizers or mocks
        self.nlp_tokenizer = FractalTokenKernel_v1_1_0(pulse_exchange=pulse_exchange, config=self.config)
        # self.code_tokenizer = FractalTokenKernel_v1_1_0(pulse_exchange=pulse_exchange, config=self.config) # If you have a separate one
        self.code_tokenizer = None # For this example, assume not present to test fallback

        # Train the tokenizer if it's empty for the example to work
        if self.nlp_tokenizer and not self.nlp_tokenizer.vocabulary:
             self.nlp_tokenizer.train(["sample text for nlp tokenizer", "another example"])


async def main_input_sector_example():
    from victor_core.logger import VictorLoggerStub
    # Setup logger for example
    example_logger = VictorLoggerStub(component="InputSectorExample")
    example_logger.log_level_str = "DEBUG"
    example_logger.current_log_level_int = example_logger.log_levels_map.get(example_logger.log_level_str, 1)


    pulse_exchange = BrainFractalPulseExchange()
    await pulse_exchange.start_pulse()

    # Mock subscriber to see processed output
    async def processed_text_subscriber(message, sender_id):
        example_logger.info(f"Processed Text Subscriber GOT: {message.get('original_text')} from {sender_id}")
        example_logger.debug(f"Full processed data: {message}")

    pulse_exchange.subscribe("input.processed_text", processed_text_subscriber)

    asi_core = MockASICoreForInput(pulse_exchange)
    input_sector = InputProcessingSector(pulse_exchange, "InputProcessor", asi_core)
    input_sector.logger = example_logger # use more verbose logger for example
    await input_sector.activate()

    # Test text input
    await pulse_exchange.publish("input.raw_text", {"text": "Hello world, this is a test.", "metadata": {"source": "test_user"}}, "TestPublisher")

    # Test code input (will use NLP tokenizer as fallback in this example setup)
    await pulse_exchange.publish("input.raw_code", {"code": "def hello(): print('world')", "language": "python", "metadata": {"source": "test_coder"}}, "TestPublisher")


    await asyncio.sleep(0.5) # Allow time for processing and publishing

    await input_sector.deactivate()
    await pulse_exchange.stop_pulse()

if __name__ == "__main__":
    # asyncio.run(main_input_sector_example())
    print("InputProcessingSector class defined. Example can be run by uncommenting asyncio.run.")
