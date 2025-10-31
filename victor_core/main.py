import asyncio
import hashlib # For any potential hashing if needed by main logic (e.g. instance ID generation)
import time
import os
import signal # For graceful shutdown handling
import json
import sys

from victor_core.brain import VictorBrain
from victor_core.logger import VictorLoggerStub
from victor_core.config import ASIConfigCore # To access CONFIG.PLUGIN_DIR for dummy plugin setup

# Global logger for the main application bootstrap phase
logger = VictorLoggerStub(component="VictorPrimeApp")

# Global variable to hold the VictorBrain instance for signal handling
victor_brain_instance: VictorBrain = None

def _create_dummy_plugin_if_not_exists():
    """
    Creates a dummy plugin structure if no plugins are found.
    This helps the ModularPluginSector initialize without errors if the plugin dir is empty.
    """
    plugin_root_dir = ASIConfigCore.PLUGIN_DIR # Get from class directly

    # Check if the plugin directory exists and if it's empty or has no valid plugins.
    # A more robust check would be to see if ModularPluginCortex would load any plugins.
    # For now, simple check if the directory is empty.
    os.makedirs(plugin_root_dir, exist_ok=True) # Ensure root plugin dir exists

    # Check if any subdirectories (potential plugins) exist
    has_subdirectories = False
    for item in os.listdir(plugin_root_dir):
        if os.path.isdir(os.path.join(plugin_root_dir, item)):
            has_subdirectories = True
            break

    if not has_subdirectories:
        logger.info(f"No plugins found in '{plugin_root_dir}'. Creating a dummy plugin.")
        dummy_plugin_name = "dummy_plugin"
        dummy_plugin_path = os.path.join(plugin_root_dir, dummy_plugin_name)
        os.makedirs(dummy_plugin_path, exist_ok=True)

        # Create __init__.py
        with open(os.path.join(dummy_plugin_path, "__init__.py"), "w") as f:
            f.write(f"# Dummy plugin: {dummy_plugin_name}\n")
            f.write("LOGGER = None\n")
            f.write("ASI_CORE = None\n")
            f.write("def initialize_plugin(asi_core_ref, logger_instance):\n")
            f.write("    global LOGGER, ASI_CORE\n")
            f.write("    LOGGER = logger_instance\n")
            f.write("    ASI_CORE = asi_core_ref\n")
            f.write(f"    LOGGER.info('{dummy_plugin_name} initialized by ModularPluginCortex.')\n\n")
            f.write("def sample_function():\n")
            f.write(f"    LOGGER.info('{dummy_plugin_name}.sample_function called.')\n")
            f.write("    return 'Dummy plugin says hello!'\n")

        # Create manifest.json
        manifest_content = {
            "name": dummy_plugin_name,
            "version": "0.1.0",
            "description": "A dummy plugin automatically created because the plugin directory was empty.",
            "author": "Victor AGI System",
            "entry_points": {
                "sample": "sample_function"
            }
        }
        with open(os.path.join(dummy_plugin_path, "manifest.json"), "w") as f:
            json.dump(manifest_content, f, indent=4)
        logger.info(f"Dummy plugin '{dummy_plugin_name}' created in '{dummy_plugin_path}'.")
    else:
        logger.info(f"Plugins directory '{plugin_root_dir}' is not empty. Skipping dummy plugin creation.")


async def run_victor_prime_core():
    global victor_brain_instance # Allow signal handler to access the instance

    logger.info("Victor Prime Core starting up...")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python version: {sys.version.split()[0]}")
    logger.info(f"Asyncio loop type: {type(asyncio.get_event_loop()).__name__}")


    # Ensure persistent directories for memory etc. exist, using path from config
    # Example: bando_agi_persistent derived from PLUGIN_DIR structure in VictorBrain/ASICoreDataContainer
    persistent_dir_example = ASIConfigCore.PLUGIN_DIR.replace('plugins', 'bando_persistent')
    os.makedirs(persistent_dir_example, exist_ok=True)
    logger.info(f"Ensured persistent directory exists: {persistent_dir_example}")


    # Create a dummy plugin if the plugin directory is empty, to ensure ModularPluginSector works.
    try:
        _create_dummy_plugin_if_not_exists()
    except Exception as e:
        logger.error(f"Failed to create dummy plugin (non-critical): {e}", exc_info=True)


    # Initialize VictorBrain
    # These signatures/entities could come from a secure config store in a real scenario
    creator_signature = hashlib.sha256(f"VictorPrimeGenesis_{time.time()}".encode()).hexdigest()[:32]
    approved_entities = ["VictorInternalDevTeam", "SystemAdministration"]

    try:
        victor_brain_instance = VictorBrain(
            creator_signature_for_plk=creator_signature,
            approved_entities_for_plk=approved_entities
        )
    except Exception as e:
        logger.critical(f"Fatal error during VictorBrain initialization: {e}", exc_info=True)
        return # Cannot proceed

    # Start the brain's processing
    await victor_brain_instance.start()

    # Example: Inject a startup message
    await victor_brain_instance.inject_raw_input(
        text_input="System startup sequence initiated. Victor Prime Core is online.",
        input_type="text",
        metadata={"source": "system_bootstrap", "priority": "high"}
    )

    # Keep the main function alive until shutdown is triggered
    # The actual work happens in VictorBrain's main loop and its async components.
    try:
        while victor_brain_instance._is_running: # Check the brain's running flag
            await asyncio.sleep(1)
            # Could add a periodic status log here if desired
            # logger.debug(f"Victor Prime Core main thread alive. Brain status: {victor_brain_instance.get_status()['is_running']}")
    except asyncio.CancelledError:
        logger.info("run_victor_prime_core task was cancelled.")
    except KeyboardInterrupt: # Should be caught by signal handler primarily
        logger.info("KeyboardInterrupt in run_victor_prime_core. Initiating shutdown sequence...")
    finally:
        logger.info("run_victor_prime_core shutting down...")
        if victor_brain_instance:
            await victor_brain_instance.stop()
        logger.info("Victor Prime Core has shut down.")


async def shutdown_handler(sig, loop):
    logger.warn(f"Received signal {sig.name}. Initiating graceful shutdown...")
    if victor_brain_instance:
        # It's important that victor_brain_instance.stop() is idempotent and handles being called multiple times.
        # Also, it should correctly signal all its internal tasks and sectors to stop.
        await victor_brain_instance.stop()
    else:
        logger.warn("No VictorBrain instance to stop.")

    # Additional cleanup if necessary

    # Stop the asyncio loop itself if all tasks are done
    # This can be tricky; ensure all background tasks spawned by asyncio.create_task are handled.
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    if tasks:
        logger.info(f"Cancelling {len(tasks)} outstanding tasks...")
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Outstanding tasks cancelled.")

    # loop.stop() # This might be called implicitly by asyncio.run finishing

def main():
    # Setup logging level from environment variable if needed
    log_level_env = os.environ.get("VICTOR_LOG_LEVEL", "INFO").upper()
    logger.log_level_str = log_level_env
    logger.current_log_level_int = logger.log_levels_map.get(log_level_env, 2)
    logger.info(f"Victor Prime Core application starting with log level: {log_level_env}")

    loop = asyncio.get_event_loop()

    # Add signal handlers for graceful shutdown
    if os.name == 'nt': # Windows does not support SIGINT/SIGTERM well for asyncio
        # logger.warn("Windows environment detected. SIGINT/SIGTERM handling might be limited. Use Ctrl+C carefully.")
        # For Windows, Ctrl+C raises KeyboardInterrupt directly in the main thread,
        # which should be caught by the try/except in run_victor_prime_core.
        # signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(shutdown_handler(s, loop))) # May not work well
        pass
    else: # POSIX
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown_handler(s, loop)))
            # Using functools.partial or a wrapper if lambda captures s incorrectly:
            # handler = functools.partial(lambda s: asyncio.create_task(shutdown_handler(s, loop)), sig)
            # loop.add_signal_handler(sig, handler)


    try:
        asyncio.run(run_victor_prime_core())
    except KeyboardInterrupt: # Fallback for systems where signal handler might not be perfect
        logger.info("Main function caught KeyboardInterrupt. Ensuring shutdown...")
        if victor_brain_instance and victor_brain_instance._is_running : # If brain is still marked as running
             loop.run_until_complete(victor_brain_instance.stop())
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {e}", exc_info=True)
    finally:
        logger.info("Application exiting.")
        # loop.close() # asyncio.run() handles loop closing.

if __name__ == "__main__":
    main()
