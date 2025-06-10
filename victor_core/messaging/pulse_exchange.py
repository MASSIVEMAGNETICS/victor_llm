import asyncio
import collections
from victor_core.logger import VictorLoggerStub

logger = VictorLoggerStub(component="BrainFractalPulseExchange")

class BrainFractalPulseExchange:
    def __init__(self):
        self.listeners = collections.defaultdict(list)
        self.event_queue = asyncio.Queue()
        self.pulse_active = True # Flag to control the pulse loop
        logger.info("BrainFractalPulseExchange initialized.")

    async def publish(self, topic: str, message, sender_id="System"):
        if not self.pulse_active:
            logger.warn(f"Pulse is not active. Message to {topic} from {sender_id} dropped.")
            return

        logger.debug(f"Publishing to {topic}: {message} from {sender_id}")
        if topic in self.listeners:
            for callback in self.listeners[topic]:
                try:
                    # If the callback is a coroutine, schedule it. Otherwise, call directly.
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(message, sender_id))
                    else:
                        callback(message, sender_id)
                except Exception as e:
                    logger.error(f"Error in callback for topic {topic}: {e}", exc_info=True)
        await self.event_queue.put({"topic": topic, "message": message, "sender_id": sender_id})


    def subscribe(self, topic: str, callback):
        logger.debug(f"New subscription to {topic}")
        self.listeners[topic].append(callback)

    def unsubscribe(self, topic: str, callback):
        logger.debug(f"Unsubscribing from {topic}")
        if topic in self.listeners:
            try:
                self.listeners[topic].remove(callback)
            except ValueError:
                logger.warn(f"Callback not found for topic {topic} during unsubscribe.")

    async def _pulse_processor(self):
        """Internal coroutine to process events from the queue."""
        logger.info("Pulse processor started.")
        while self.pulse_active:
            try:
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0) # Timeout to allow checking pulse_active
                if event is None: # Sentinel value to stop the processor
                    logger.info("Pulse processor received stop signal.")
                    break
                # Basic processing for now, could be expanded
                # logger.debug(f"Pulse processed event: {event['topic']} from {event['sender_id']}")
                self.event_queue.task_done()
            except asyncio.TimeoutError:
                continue # Allows checking self.pulse_active flag
            except Exception as e:
                logger.error(f"Exception in pulse processor: {e}", exc_info=True)
        logger.info("Pulse processor stopped.")

    async def start_pulse(self):
        """Starts the pulse processor task."""
        if not hasattr(self, '_processor_task') or self._processor_task.done():
            self.pulse_active = True
            self._processor_task = asyncio.create_task(self._pulse_processor())
            logger.info("BrainFractalPulseExchange pulse started.")
        else:
            logger.info("Pulse already running or start requested again without stopping.")


    async def stop_pulse(self):
        """Stops the pulse processor task."""
        logger.info("Attempting to stop BrainFractalPulseExchange pulse...")
        self.pulse_active = False # Signal the loop to stop
        if hasattr(self, '_processor_task') and not self._processor_task.done():
            try:
                # Put a sentinel value to ensure the queue.get() unblocks if empty
                await self.event_queue.put(None)
                await asyncio.wait_for(self._processor_task, timeout=5.0) # Wait for the task to finish
                logger.info("Pulse processor task successfully stopped.")
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for pulse processor to stop. It might be stuck.")
                self._processor_task.cancel() # Force cancel if it doesn't stop gracefully
                try:
                    await self._processor_task
                except asyncio.CancelledError:
                    logger.info("Pulse processor task was cancelled.")
            except Exception as e:
                logger.error(f"Exception during pulse stop: {e}", exc_info=True)
        else:
            logger.info("Pulse processor task was not running or already stopped.")
        # Clear listeners and queue if needed, or manage state for restart
        # self.listeners.clear()
        # while not self.event_queue.empty():
        # self.event_queue.get_nowait()
        logger.info("BrainFractalPulseExchange pulse stopped.")

# Example Usage (for testing purposes, typically run within an asyncio event loop)
async def example_subscriber(message, sender_id):
    logger.info(f"Example subscriber received: {message} from {sender_id}")

async def main():
    pulse_exchange = BrainFractalPulseExchange()
    await pulse_exchange.start_pulse()

    pulse_exchange.subscribe("test_topic", example_subscriber)
    await pulse_exchange.publish("test_topic", {"data": "Hello World"}, "TestSender")

    await asyncio.sleep(1) # Give time for message to be processed

    await pulse_exchange.stop_pulse()

if __name__ == "__main__":
    # Basic logger for the example, replace with proper setup in application
    # import sys
    # logger.log_level_str = "DEBUG"
    # logger.current_log_level_int = logger.log_levels_map.get(logger.log_level_str, 2)
    # handler = logging.StreamHandler(sys.stdout)
    # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # handler.setFormatter(formatter)
    # temp_logger = logging.getLogger("BrainFractalPulseExchangeExample")
    # temp_logger.addHandler(handler)
    # temp_logger.setLevel(logging.DEBUG)
    # logger.info = temp_logger.info # monkey patch for example
    # logger.debug = temp_logger.debug
    # logger.error = temp_logger.error

    asyncio.run(main())
