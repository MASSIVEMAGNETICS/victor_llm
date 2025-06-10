import asyncio
from victor_core.sectors.base import VictorSector
from victor_core.messaging.pulse_exchange import BrainFractalPulseExchange
# Potential future import for a sophisticated NLG model or template engine
# from some_nlg_library import NLGModel

class NLGOutputSector(VictorSector):
    def __init__(self, pulse_exchange_instance: BrainFractalPulseExchange, name: str, asi_core_ref):
        super().__init__(pulse_exchange_instance, name, asi_core_ref)

        # In a real system, this might load an NLG model or connect to an NLG service.
        # self.nlg_model = NLGModel()
        # For now, we'll use simple template-based responses.
        self.response_templates = {
            "greeting": "Hello! How can I assist you today?",
            "confirmation": "Understood. I will proceed with that.",
            "error_generic": "I encountered an issue. Please try again or check the logs.",
            "query_answer_simple": "Regarding your query about '{query_summary}': {answer_content}",
            "unknown_query": "I don't have enough information to respond to your query about '{query_summary}'.",
        }
        self.logger.info("NLGOutputSector initialized with template-based responses.")

    async def activate(self):
        await super().activate()
        # Subscribe to requests for text generation
        await self.pulse_exchange.subscribe("nlg.generate_text_request", self.handle_generate_text_request)
        self.logger.info("NLGOutputSector activated and subscribed to NLG requests.")

    async def deactivate(self):
        await self.pulse_exchange.unsubscribe("nlg.generate_text_request", self.handle_generate_text_request)
        await super().deactivate()
        self.logger.info("NLGOutputSector deactivated.")

    async def handle_generate_text_request(self, message_data, sender_id):
        """
        Handles requests to generate text based on a context or template.
        """
        request_id = message_data.get("request_id", uuid.uuid4().hex)
        template_key = message_data.get("template_key")
        context_data = message_data.get("context_data", {})
        output_channel = message_data.get("output_channel", "default_output") # e.g. user_interface, log, specific_plugin

        self.logger.info(f"Received text generation request (ID: {request_id}) for template '{template_key}' from {sender_id}.")

        generated_text = ""
        success = False

        if template_key and template_key in self.response_templates:
            try:
                generated_text = self.response_templates[template_key].format(**context_data)
                success = True
            except KeyError as e: # Missing key in context_data for format string
                self.logger.warn(f"Missing key '{e}' in context_data for template '{template_key}'. Context: {context_data}")
                generated_text = f"Error: Template '{template_key}' requires key {e} which was not provided."
                # Fallback to a generic error or try to use a simpler template
                # generated_text = self.response_templates["error_generic"]
            except Exception as e:
                self.logger.error(f"Error formatting template '{template_key}': {e}", exc_info=True)
                generated_text = self.response_templates.get("error_generic", "An unexpected error occurred during text generation.")

        elif "raw_content" in context_data: # If direct content is provided instead of template
            generated_text = str(context_data["raw_content"])
            success = True
            self.logger.debug(f"Generating text directly from raw_content for request ID {request_id}.")

        else:
            self.logger.warn(f"No valid template_key or raw_content provided for request ID {request_id}. Template: '{template_key}'.")
            generated_text = "I'm not sure how to respond to that."
            # Fallback to a generic unknown response template if available
            # generated_text = self.response_templates.get("unknown_query", "Response cannot be generated.")


        if success:
            self.logger.info(f"Generated text for request ID {request_id}: '{generated_text[:100]}...'")
            await self.pulse_exchange.publish(
                topic=f"nlg.generated_text_response.{request_id}", # Topic for direct response if awaited
                message={
                    "request_id": request_id,
                    "generated_text": generated_text,
                    "output_channel": output_channel, # For routing the output
                    "status": "success"
                },
                sender_id=self.sector_id
            )
            # Also publish to a more general topic for consumption by output channels
            await self.pulse_exchange.publish(
                topic=f"output.{output_channel}",
                message={
                    "text": generated_text,
                    "source_request_id": request_id,
                    "nlg_sender_id": str(self.sector_id)
                },
                sender_id=self.sector_id
            )
        else:
            self.logger.warn(f"Failed to generate text for request ID {request_id}. Template: {template_key}")
            await self.pulse_exchange.publish(
                topic=f"nlg.generation_failed.{request_id}",
                message={
                    "request_id": request_id,
                    "error_message": generated_text, # Contains the error description here
                    "status": "failure"
                },
                sender_id=self.sector_id
            )

# Example of how asi_core_ref might be structured (not strictly needed by this simple NLG)
class MockASICoreForNLG:
    def __init__(self):
        # self.some_nlg_model_config = {} # If NLG needed config from ASI core
        self.logger = VictorLoggerStub(component="MockASICoreForNLG")


async def main_nlg_sector_example():
    from victor_core.logger import VictorLoggerStub
    import uuid # For request_id

    example_logger = VictorLoggerStub(component="NLGSectorExample")
    example_logger.log_level_str = "DEBUG"
    example_logger.current_log_level_int = example_logger.log_levels_map.get(example_logger.log_level_str, 1)

    pulse_exchange = BrainFractalPulseExchange()
    await pulse_exchange.start_pulse()

    # Mock subscriber to see generated output
    async def output_subscriber(message, sender_id):
        example_logger.info(f"Output Subscriber GOT ({message.get('output_channel', 'default')}): '{message.get('text')}' from {sender_id}")

    async def nlg_response_subscriber(message, sender_id):
        example_logger.debug(f"NLG Response Sub GOT: {message} from {sender_id}")

    await pulse_exchange.subscribe("output.*", output_subscriber) # General output consumer
    await pulse_exchange.subscribe("nlg.generated_text_response.*", nlg_response_subscriber) # Specific NLG success
    await pulse_exchange.subscribe("nlg.generation_failed.*", nlg_response_subscriber) # Specific NLG failure


    asi_core = MockASICoreForNLG() # Not really used by this simple NLG
    nlg_sector = NLGOutputSector(pulse_exchange, "NLGOutput", asi_core)
    nlg_sector.logger = example_logger # use more verbose logger

    await nlg_sector.activate()

    # Test case 1: Generate greeting
    req_id_greet = uuid.uuid4().hex
    await pulse_exchange.publish(
        "nlg.generate_text_request",
        {"request_id": req_id_greet, "template_key": "greeting", "output_channel": "user_chat"},
        "TestNLGSender"
    )

    await asyncio.sleep(0.1)

    # Test case 2: Generate a query answer
    req_id_answer = uuid.uuid4().hex
    await pulse_exchange.publish(
        "nlg.generate_text_request",
        {
            "request_id": req_id_answer,
            "template_key": "query_answer_simple",
            "context_data": {"query_summary": "the weather", "answer_content": "It is sunny today."},
            "output_channel": "user_chat"
        },
        "TestNLGSender"
    )
    await asyncio.sleep(0.1)

    # Test case 3: Template key missing in context
    req_id_keyerror = uuid.uuid4().hex
    await pulse_exchange.publish(
        "nlg.generate_text_request",
        {
            "request_id": req_id_keyerror,
            "template_key": "query_answer_simple",
            "context_data": {"query_summary": "the time"}, # Missing 'answer_content'
            "output_channel": "user_chat"
        },
        "TestNLGSender"
    )
    await asyncio.sleep(0.1)

    # Test case 4: Invalid template key
    req_id_badtemplate = uuid.uuid4().hex
    await pulse_exchange.publish(
        "nlg.generate_text_request",
        {"request_id": req_id_badtemplate, "template_key": "non_existent_template", "output_channel": "user_chat"},
        "TestNLGSender"
    )
    await asyncio.sleep(0.1)


    await nlg_sector.deactivate()
    await pulse_exchange.stop_pulse()

if __name__ == "__main__":
    # asyncio.run(main_nlg_sector_example())
    print("NLGOutputSector class defined. Example can be run by uncommenting asyncio.run.")
