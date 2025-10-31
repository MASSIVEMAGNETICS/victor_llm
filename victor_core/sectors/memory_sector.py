import asyncio
import numpy as np # For handling vector embeddings
from victor_core.sectors.base import VictorSector
from victor_core.messaging.pulse_exchange import BrainFractalPulseExchange
# Assuming HyperFractalMemory is in hyper_fractal_memory.py
# from victor_core.memory.hyper_fractal_memory import HyperFractalMemory

class MemorySector(VictorSector):
    def __init__(self, pulse_exchange_instance: BrainFractalPulseExchange, name: str, asi_core_ref):
        super().__init__(pulse_exchange_instance, name, asi_core_ref)

        # Memory component is expected to be an attribute of asi_core_ref
        # e.g., self.asi_core.memory, an instance of HyperFractalMemory
        self.memory_system = getattr(self.asi_core, 'memory', None)

        if not self.memory_system:
            self.logger.error("Memory system (HyperFractalMemory instance) not found in asi_core_ref. MemorySector will be non-functional.")
            # Potentially raise an error or set a non-functional state
        else:
            self.logger.info(f"MemorySector initialized. Using memory system: {type(self.memory_system).__name__}")

    async def activate(self):
        if not self.memory_system:
            self.logger.error("Cannot activate MemorySector: memory system is missing.")
            self.status = "error_missing_memory_system"
            return

        await super().activate()
        # Subscribe to commands or requests for memory operations
        self.pulse_exchange.subscribe(f"sector.{self.name}.command", self.handle_memory_command)
        # Example: direct subscription to storage requests from other systems
        self.pulse_exchange.subscribe("memory.store_request", self.handle_store_request_event)
        self.pulse_exchange.subscribe("memory.search_request", self.handle_search_request_event)
        self.logger.info("MemorySector activated and subscribed to memory operation topics.")

    async def deactivate(self):
        if not self.memory_system: # Already logged during init/activate
            await super().deactivate() # Basic deactivation
            return

        self.pulse_exchange.unsubscribe(f"sector.{self.name}.command", self.handle_memory_command)
        self.pulse_exchange.unsubscribe("memory.store_request", self.handle_store_request_event)
        self.pulse_exchange.unsubscribe("memory.search_request", self.handle_search_request_event)
        await super().deactivate()
        self.logger.info("MemorySector deactivated.")

    async def handle_memory_command(self, message_data, sender_id):
        """Handles direct commands sent to this sector."""
        command = message_data.get("command")
        data = message_data.get("data")
        request_id = message_data.get("request_id", uuid.uuid4().hex) # For tracking responses

        self.logger.info(f"Received command '{command}' from {sender_id} (Req ID: {request_id}).")

        if command == "store_from_directive": # Example from CognitiveExecutiveSector
            if not data or not isinstance(data, dict):
                self.logger.warn(f"Invalid data for 'store_from_directive': {data}")
                await self._publish_error_response(request_id, "INVALID_DATA", "Data for storage is missing or malformed.")
                return

            # Adapt data from directive to fit store_memory_entry arguments
            # This is a placeholder transformation
            text_summary = data.get('summary', 'Information from directive')
            content_data = data.get('input_details', {'raw': str(data)})
            # keyword_hashes might be part of the directive details, or derived
            keyword_hashes = data.get('keyword_hashes', [word.lower() for word in text_summary.split()[:3]])
            emotional_tags = {"source": "directive", "priority": data.get("priority", 0.5)}

            try:
                content_hash = self.memory_system.store_memory_entry(
                    content_data=content_data,
                    text_summary=text_summary,
                    keyword_hashes=keyword_hashes,
                    emotional_tags=emotional_tags
                )
                self.logger.info(f"Stored memory from directive. Hash: {content_hash}. Req ID: {request_id}")
                await self.pulse_exchange.publish(
                    topic=f"memory.operation_success.{request_id}",
                    message={"operation": command, "content_hash": content_hash, "status": "success"},
                    sender_id=self.sector_id
                )
            except Exception as e:
                self.logger.error(f"Error storing memory from directive (Req ID: {request_id}): {e}", exc_info=True)
                await self._publish_error_response(request_id, "STORAGE_FAILED", str(e))

        elif command == "search_memory":
            query_vector_list = data.get("query_vector")
            query_vector = np.array(query_vector_list) if query_vector_list is not None else None
            keyword_hashes = data.get("keyword_hashes")
            top_n = data.get("top_n", 5)

            try:
                results = self.memory_system.search_memories(
                    query_vector=query_vector,
                    keyword_hashes=keyword_hashes,
                    top_n=top_n
                )
                self.logger.info(f"Search command yielded {len(results)} results. Req ID: {request_id}")
                # Serialize results for publishing (numpy arrays, datetime objects)
                serializable_results = self._serialize_search_results(results)
                await self.pulse_exchange.publish(
                    topic=f"memory.search_results.{request_id}",
                    message={"operation": command, "results": serializable_results, "status": "success"},
                    sender_id=self.sector_id
                )
            except Exception as e:
                self.logger.error(f"Error during memory search command (Req ID: {request_id}): {e}", exc_info=True)
                await self._publish_error_response(request_id, "SEARCH_FAILED", str(e))

        elif command == "get_memory_by_hash":
            content_hash = data.get("content_hash")
            if not content_hash:
                await self._publish_error_response(request_id, "INVALID_DATA", "content_hash missing for get_memory_by_hash.")
                return
            try:
                entry = self.memory_system.retrieve_memory_by_hash(content_hash)
                serializable_entry = self._serialize_search_results([entry] if entry else [])[0] if entry else None
                await self.pulse_exchange.publish(
                    topic=f"memory.retrieved_entry.{request_id}",
                    message={"operation": command, "entry": serializable_entry, "status": "success" if entry else "not_found"},
                    sender_id=self.sector_id
                )
            except Exception as e:
                 self.logger.error(f"Error retrieving memory by hash (Req ID: {request_id}): {e}", exc_info=True)
                 await self._publish_error_response(request_id, "RETRIEVAL_FAILED", str(e))
        else:
            self.logger.warn(f"Unknown memory command: {command}. Req ID: {request_id}")
            await self._publish_error_response(request_id, "UNKNOWN_COMMAND", f"Command '{command}' not recognized.")

    async def handle_store_request_event(self, message_data, sender_id):
        """Handles generic memory storage requests from the bus."""
        request_id = message_data.get("request_id", uuid.uuid4().hex)
        self.logger.info(f"Handling store_request_event from {sender_id}. Req ID: {request_id}")
        try:
            # Assuming message_data directly contains arguments for store_memory_entry
            # Or requires some transformation
            content_data = message_data.get("content_data")
            text_summary = message_data.get("text_summary")
            vector_embedding_list = message_data.get("vector_embedding")
            vector_embedding = np.array(vector_embedding_list) if vector_embedding_list is not None else None

            if not content_data or not text_summary:
                 await self._publish_error_response(request_id, "INVALID_DATA_STORE_EVENT", "content_data or text_summary missing.")
                 return

            content_hash = self.memory_system.store_memory_entry(
                content_data=content_data,
                text_summary=text_summary,
                vector_embedding=vector_embedding,
                keyword_hashes=message_data.get("keyword_hashes"),
                emotional_tags=message_data.get("emotional_tags"),
                related_memory_hashes=message_data.get("related_memory_hashes")
            )
            await self.pulse_exchange.publish(
                topic=f"memory.operation_success.{request_id}", # Generic success topic for requests
                message={"operation": "store_event", "content_hash": content_hash, "status": "success"},
                sender_id=self.sector_id
            )
        except Exception as e:
            self.logger.error(f"Error handling store_request_event (Req ID: {request_id}): {e}", exc_info=True)
            await self._publish_error_response(request_id, "STORE_EVENT_FAILED", str(e))

    async def handle_search_request_event(self, message_data, sender_id):
        """Handles generic memory search requests from the bus."""
        request_id = message_data.get("request_id", uuid.uuid4().hex)
        self.logger.info(f"Handling search_request_event from {sender_id}. Req ID: {request_id}")
        try:
            query_vector_list = message_data.get("query_vector")
            query_vector = np.array(query_vector_list) if query_vector_list is not None else None

            results = self.memory_system.search_memories(
                query_vector=query_vector,
                keyword_hashes=message_data.get("keyword_hashes"),
                date_range=message_data.get("date_range"), # Assuming dates are ISO strings, HyperFractalMemory needs to parse
                min_relevance=message_data.get("min_relevance", 0.1),
                top_n=message_data.get("top_n", 5)
            )
            serializable_results = self._serialize_search_results(results)
            await self.pulse_exchange.publish(
                topic=f"memory.search_results.{request_id}", # Generic results topic for requests
                message={"operation": "search_event", "results": serializable_results, "status": "success"},
                sender_id=self.sector_id
            )
        except Exception as e:
            self.logger.error(f"Error handling search_request_event (Req ID: {request_id}): {e}", exc_info=True)
            await self._publish_error_response(request_id, "SEARCH_EVENT_FAILED", str(e))

    def _serialize_search_results(self, results: list[dict]) -> list[dict]:
        """Helper to make search results JSON serializable (datetime, numpy arrays)."""
        serialized = []
        if not results: return []
        for entry in results:
            if not entry: continue
            s_entry = entry.copy()
            if 'vector_embedding' in s_entry and isinstance(s_entry['vector_embedding'], np.ndarray):
                s_entry['vector_embedding'] = s_entry['vector_embedding'].tolist()
            if 'creation_ts' in s_entry and hasattr(s_entry['creation_ts'], 'isoformat'):
                s_entry['creation_ts'] = s_entry['creation_ts'].isoformat()
            if 'last_accessed_ts' in s_entry and hasattr(s_entry['last_accessed_ts'], 'isoformat'):
                s_entry['last_accessed_ts'] = s_entry['last_accessed_ts'].isoformat()
            serialized.append(s_entry)
        return serialized

    async def _publish_error_response(self, request_id: str, error_code: str, error_message: str):
        await self.pulse_exchange.publish(
            topic=f"memory.operation_error.{request_id}",
            message={"error_code": error_code, "message": error_message, "status": "error"},
            sender_id=self.sector_id
        )


# Example of how asi_core_ref might be structured for MemorySector
class MockASICoreForMemory:
    def __init__(self):
        from victor_core.memory.hyper_fractal_memory import HyperFractalMemory
        # Ensure the persistent directory exists for the example
        import os
        os.makedirs("bando_agi_persistent", exist_ok=True)
        self.memory = HyperFractalMemory(storage_path="bando_agi_persistent/memory_sector_test.json")
        self.logger = VictorLoggerStub(component="MockASICoreForMemory")

async def main_memory_sector_example():
    from victor_core.logger import VictorLoggerStub
    example_logger = VictorLoggerStub(component="MemorySectorExample")
    example_logger.log_level_str = "DEBUG"
    example_logger.current_log_level_int = example_logger.log_levels_map.get(example_logger.log_level_str, 1)

    pulse_exchange = BrainFractalPulseExchange()
    await pulse_exchange.start_pulse()

    # Mock subscriber to see memory operation results
    async def memory_op_subscriber(message, sender_id):
        topic_parts = message.get("topic_actual", "unknown.topic").split('.') # topic_actual is added by pulse for wildcard subs
        if "error" in topic_parts:
             example_logger.error(f"Memory Op Error Sub GOT: {message} from {sender_id}")
        else:
             example_logger.info(f"Memory Op Success Sub GOT: {message} from {sender_id}")


    pulse_exchange.subscribe("memory.operation_success.*", memory_op_subscriber)
    pulse_exchange.subscribe("memory.operation_error.*", memory_op_subscriber)
    pulse_exchange.subscribe("memory.search_results.*", memory_op_subscriber)


    asi_core = MockASICoreForMemory()
     # Clean up test memory file
    import os
    if os.path.exists("bando_agi_persistent/memory_sector_test.json"):
        os.remove("bando_agi_persistent/memory_sector_test.json")
    asi_core.memory = HyperFractalMemory(storage_path="bando_agi_persistent/memory_sector_test.json") # re-init
    asi_core.memory.logger = example_logger


    memory_sector = MemorySector(pulse_exchange, "MemoryCore", asi_core)
    memory_sector.logger = example_logger # use more verbose logger

    await memory_sector.activate()

    # Test case 1: Store request via event
    req_id_store = uuid.uuid4().hex
    store_payload = {
        "request_id": req_id_store,
        "content_data": {"info": "This is a test event storage"},
        "text_summary": "Test event storage summary",
        "keyword_hashes": ["test", "event_storage"],
        "emotional_tags": {"sentiment": "neutral"}
    }
    await pulse_exchange.publish("memory.store_request", store_payload, "TestEventPublisher")

    await asyncio.sleep(0.2) # time for processing

    # Test case 2: Search request via command (e.g., from Cognitive Sector)
    req_id_search = uuid.uuid4().hex
    search_command_payload = {
        "command": "search_memory",
        "request_id": req_id_search,
        "data": {
            "keyword_hashes": ["test"],
            "top_n": 1
        }
    }
    # Note: Publishing to `sector.{memory_sector.name}.command`
    await pulse_exchange.publish(f"sector.{memory_sector.name}.command", search_command_payload, "TestCommandPublisher")

    await asyncio.sleep(0.2) # time for processing

    await memory_sector.deactivate()
    await pulse_exchange.stop_pulse()

if __name__ == "__main__":
    # asyncio.run(main_memory_sector_example())
    print("MemorySector class defined. Example can be run by uncommenting asyncio.run.")
