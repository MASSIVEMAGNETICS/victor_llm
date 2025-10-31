import asyncio
import os
import importlib.util
import sys
import json # For plugin configuration or data exchange
from victor_core.sectors.base import VictorSector
from victor_core.messaging.pulse_exchange import BrainFractalPulseExchange
from victor_core.config import ASIConfigCore # For default PLUGIN_DIR

class ModularPluginCortex:
    def __init__(self, plugin_dir="victor_plugins", logger=None, asi_core_ref=None):
        self.plugin_dir = plugin_dir
        self.plugins = {} # Stores loaded plugin modules or instances: {plugin_name: plugin_module_or_instance}
        self.plugin_manifests = {} # Stores plugin metadata: {plugin_name: manifest_data}
        self.logger = logger if logger else VictorLoggerStub(component="ModularPluginCortex")
        self.asi_core_ref = asi_core_ref # To pass to plugins if they need it

        os.makedirs(self.plugin_dir, exist_ok=True) # Ensure plugin directory exists
        self.logger.info(f"ModularPluginCortex initialized. Plugin directory: '{self.plugin_dir}'")
        self.load_plugins()

    def load_plugins(self):
        """
        Loads plugins from the specified plugin directory.
        A plugin is expected to be a directory containing an __init__.py and a manifest.json.
        """
        self.logger.info(f"Scanning for plugins in '{self.plugin_dir}'...")
        for item_name in os.listdir(self.plugin_dir):
            item_path = os.path.join(self.plugin_dir, item_name)
            if os.path.isdir(item_path):
                plugin_name = item_name
                manifest_path = os.path.join(item_path, "manifest.json")
                plugin_init_file = os.path.join(item_path, "__init__.py")

                if not os.path.exists(plugin_init_file):
                    self.logger.debug(f"Skipping '{plugin_name}', no __init__.py found.")
                    continue

                if not os.path.exists(manifest_path):
                    self.logger.warn(f"Plugin '{plugin_name}' is missing manifest.json. Attempting to load anyway.")
                    manifest_data = {"name": plugin_name, "version": "0.0.0-alpha", "description": "Missing manifest."}
                else:
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest_data = json.load(f)
                        if manifest_data.get("name") != plugin_name:
                             self.logger.warn(f"Plugin '{plugin_name}' has mismatched name in manifest: '{manifest_data.get('name')}'. Using directory name.")
                             manifest_data["name"] = plugin_name # Standardize on directory name
                    except json.JSONDecodeError:
                        self.logger.error(f"Could not parse manifest.json for plugin '{plugin_name}'. Skipping.")
                        continue

                try:
                    # Ensure plugin directory is in path for import
                    if self.plugin_dir not in sys.path: # Add base plugin dir
                        sys.path.insert(0, self.plugin_dir)
                    # if item_path not in sys.path: # Add specific plugin dir
                    #    sys.path.insert(0, item_path)


                    # The module name to import would be like "plugin_name" if plugin_dir is in sys.path
                    # Or, if importing directly from path:
                    # spec = importlib.util.spec_from_file_location(plugin_name, plugin_init_file)
                    # module = importlib.util.module_from_spec(spec)
                    # sys.modules[plugin_name] = module # Register module
                    # spec.loader.exec_module(module)

                    # Simpler approach if plugin_dir is added to sys.path and plugins are proper packages
                    module = importlib.import_module(f"{plugin_name}") # Assumes plugin_name is a package in plugin_dir

                    self.plugins[plugin_name] = module
                    self.plugin_manifests[plugin_name] = manifest_data
                    self.logger.info(f"Successfully loaded plugin '{plugin_name}' version {manifest_data.get('version', 'N/A')}.")

                    # Initialize plugin if it has an 'initialize_plugin' function
                    if hasattr(module, 'initialize_plugin'):
                        self.logger.debug(f"Calling initialize_plugin for '{plugin_name}'...")
                        # Pass ASI core reference and logger to plugins for them to use
                        module.initialize_plugin(self.asi_core_ref, VictorLoggerStub(component=f"Plugin_{plugin_name}"))


                except ImportError as e:
                    self.logger.error(f"Failed to import plugin '{plugin_name}': {e}", exc_info=True)
                except Exception as e:
                    self.logger.error(f"An unexpected error occurred while loading plugin '{plugin_name}': {e}", exc_info=True)

        if not self.plugins:
            self.logger.info("No plugins found or loaded.")

    def list_plugins(self) -> list[dict]:
        """Returns a list of loaded plugins with their manifest data."""
        return list(self.plugin_manifests.values())

    def run_plugin_function(self, plugin_name: str, function_name: str, *args, **kwargs):
        """Runs a specific function from a loaded plugin."""
        if plugin_name not in self.plugins:
            self.logger.error(f"Plugin '{plugin_name}' not found.")
            raise ValueError(f"Plugin '{plugin_name}' not found.")

        plugin_module = self.plugins[plugin_name]
        if not hasattr(plugin_module, function_name):
            self.logger.error(f"Function '{function_name}' not found in plugin '{plugin_name}'.")
            raise AttributeError(f"Function '{function_name}' not found in plugin '{plugin_name}'.")

        plugin_function = getattr(plugin_module, function_name)
        self.logger.info(f"Executing function '{function_name}' from plugin '{plugin_name}'.")
        try:
            # Plugins might be async or sync. This example assumes sync for simplicity here.
            # A more robust system would handle async plugin functions appropriately (e.g. await if asyncio.iscoroutinefunction).
            return plugin_function(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error running function '{function_name}' in plugin '{plugin_name}': {e}", exc_info=True)
            raise # Re-raise the exception after logging


class ModularPluginSector(VictorSector):
    # Adjusted constructor to match original plan: plugin_dir is taken from config by default
    def __init__(self, pulse_exchange_instance: BrainFractalPulseExchange, name: str, asi_core_ref):
        super().__init__(pulse_exchange_instance, name, asi_core_ref)

        # Determine plugin directory: Use asi_core_ref.config if available, else default.
        plugin_dir_to_use = ASIConfigCore.PLUGIN_DIR # Default from class variable
        if self.asi_core and hasattr(self.asi_core, 'config') and self.asi_core.config:
            plugin_dir_to_use = getattr(self.asi_core.config, 'PLUGIN_DIR', plugin_dir_to_use)

        self.mpc = ModularPluginCortex(plugin_dir=plugin_dir_to_use, logger=self.logger, asi_core_ref=self.asi_core)
        self.logger.info(f"ModularPluginSector initialized. Cortex managing plugins from '{plugin_dir_to_use}'.")

    async def activate(self):
        await super().activate()
        # Subscribe to requests for plugin operations
        self.pulse_exchange.subscribe("plugin.list_request", self.handle_list_plugins_request)
        self.pulse_exchange.subscribe("plugin.run_function_request", self.handle_run_plugin_function_request)
        # Example: direct command to this sector
        self.pulse_exchange.subscribe(f"sector.{self.name}.command", self.handle_sector_command)
        self.logger.info("ModularPluginSector activated and subscribed to plugin operation topics.")

    async def deactivate(self):
        self.pulse_exchange.unsubscribe("plugin.list_request", self.handle_list_plugins_request)
        self.pulse_exchange.unsubscribe("plugin.run_function_request", self.handle_run_plugin_function_request)
        self.pulse_exchange.unsubscribe(f"sector.{self.name}.command", self.handle_sector_command)
        # Potentially call a shutdown on all plugins if they have such a method
        for plugin_name, plugin_module in self.mpc.plugins.items():
            if hasattr(plugin_module, 'shutdown_plugin'):
                try:
                    self.logger.debug(f"Calling shutdown_plugin for '{plugin_name}'...")
                    if asyncio.iscoroutinefunction(plugin_module.shutdown_plugin):
                        await plugin_module.shutdown_plugin()
                    else:
                        plugin_module.shutdown_plugin()
                except Exception as e:
                    self.logger.error(f"Error shutting down plugin '{plugin_name}': {e}", exc_info=True)
        await super().deactivate()
        self.logger.info("ModularPluginSector deactivated.")

    async def handle_list_plugins_request(self, message_data, sender_id):
        request_id = message_data.get("request_id", uuid.uuid4().hex)
        self.logger.info(f"Received list_plugins request (ID: {request_id}) from {sender_id}.")
        try:
            plugins_list = self.mpc.list_plugins()
            await self.pulse_exchange.publish(
                topic=f"plugin.list_response.{request_id}",
                message={"request_id": request_id, "plugins": plugins_list, "status": "success"},
                sender_id=self.sector_id
            )
        except Exception as e:
            self.logger.error(f"Error listing plugins (Req ID: {request_id}): {e}", exc_info=True)
            await self.pulse_exchange.publish(
                topic=f"plugin.list_response.{request_id}", # Publish to same response topic with error
                message={"request_id": request_id, "error": str(e), "status": "failure"},
                sender_id=self.sector_id
            )

    async def handle_run_plugin_function_request(self, message_data, sender_id):
        request_id = message_data.get("request_id", uuid.uuid4().hex)
        plugin_name = message_data.get("plugin_name")
        function_name = message_data.get("function_name")
        args = message_data.get("args", [])
        kwargs = message_data.get("kwargs", {})

        self.logger.info(f"Received run_plugin_function request (ID: {request_id}) for {plugin_name}.{function_name} from {sender_id}.")

        if not plugin_name or not function_name:
            self.logger.warn(f"Missing plugin_name or function_name in request ID {request_id}.")
            await self.pulse_exchange.publish(
                topic=f"plugin.run_function_response.{request_id}",
                message={"request_id": request_id, "error": "plugin_name and function_name are required", "status": "failure"},
                sender_id=self.sector_id
            )
            return

        try:
            # Check if the target function is async
            plugin_module = self.mpc.plugins.get(plugin_name)
            if not plugin_module or not hasattr(plugin_module, function_name):
                 raise AttributeError(f"Plugin '{plugin_name}' or function '{function_name}' not found.")

            target_function = getattr(plugin_module, function_name)

            if asyncio.iscoroutinefunction(target_function):
                result = await self.mpc.run_plugin_function(plugin_name, function_name, *args, **kwargs)
            else:
                # For synchronous plugin functions, run them in a thread pool executor
                # to avoid blocking the asyncio event loop if they are long-running.
                # For short-running sync functions, direct call might be okay but executor is safer.
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None, # Default ThreadPoolExecutor
                    self.mpc.run_plugin_function, # The wrapper that calls the actual plugin function
                    plugin_name, function_name, *args, **kwargs
                )

            self.logger.info(f"Plugin function {plugin_name}.{function_name} executed successfully. Result type: {type(result)}")
            # Results must be JSON serializable to be sent over pulse.
            # This is a simplification; complex objects might need custom serialization.
            try:
                json.dumps(result) # Test serializability
            except (TypeError, OverflowError) as json_err:
                self.logger.warn(f"Result of {plugin_name}.{function_name} is not JSON serializable: {json_err}. Sending string representation.")
                result = str(result) # Fallback to string

            await self.pulse_exchange.publish(
                topic=f"plugin.run_function_response.{request_id}",
                message={"request_id": request_id, "result": result, "status": "success"},
                sender_id=self.sector_id
            )
        except Exception as e:
            self.logger.error(f"Error running plugin function {plugin_name}.{function_name} (Req ID: {request_id}): {e}", exc_info=True)
            await self.pulse_exchange.publish(
                topic=f"plugin.run_function_response.{request_id}",
                message={"request_id": request_id, "error": str(e), "status": "failure"},
                sender_id=self.sector_id
            )

    async def handle_sector_command(self, message_data, sender_id):
        """Handles direct commands to the ModularPluginSector itself."""
        command = message_data.get("command")
        request_id = message_data.get("request_id", uuid.uuid4().hex)
        self.logger.info(f"ModularPluginSector received command '{command}' from {sender_id}.")

        if command == "reload_plugins":
            self.logger.info("Command received: reload_plugins. Re-initializing ModularPluginCortex.")
            # Determine plugin directory again
            plugin_dir_to_use = ASIConfigCore.PLUGIN_DIR
            if self.asi_core and hasattr(self.asi_core, 'config') and self.asi_core.config:
                plugin_dir_to_use = getattr(self.asi_core.config, 'PLUGIN_DIR', plugin_dir_to_use)

            # Before reloading, attempt to shutdown existing plugins
            for plugin_name, plugin_module in self.mpc.plugins.items():
                 if hasattr(plugin_module, 'shutdown_plugin'):
                    try:
                        if asyncio.iscoroutinefunction(plugin_module.shutdown_plugin): await plugin_module.shutdown_plugin()
                        else: plugin_module.shutdown_plugin()
                    except Exception as e: self.logger.error(f"Error shutting down plugin '{plugin_name}' during reload: {e}")

            self.mpc = ModularPluginCortex(plugin_dir=plugin_dir_to_use, logger=self.logger, asi_core_ref=self.asi_core)
            await self.pulse_exchange.publish(
                topic=f"sector.{self.name}.command_response.{request_id}",
                message={"request_id": request_id, "status": "success", "details": f"Plugins reloaded from {plugin_dir_to_use}. Found {len(self.mpc.plugins)} plugins."},
                sender_id=self.sector_id
            )
        else:
            self.logger.warn(f"Unknown command for ModularPluginSector: {command}")
            await self.pulse_exchange.publish(
                topic=f"sector.{self.name}.command_response.{request_id}",
                message={"request_id": request_id, "status": "failure", "error": f"Unknown command: {command}"},
                sender_id=self.sector_id
            )


# Example ASI Core
class MockASICoreForPlugins:
    def __init__(self):
        self.config = ASIConfigCore()
        # Example: Override plugin directory for testing
        # self.config.PLUGIN_DIR = "test_victor_plugins"
        self.logger = VictorLoggerStub(component="MockASICoreForPlugins")
        # Other core components plugins might need, e.g., memory, nlp_tokenizer
        # self.memory = HyperFractalMemory(...)
        # self.nlp_tokenizer = FractalTokenKernel_v1_1_0(...)

# --- Example Plugin (would be in victor_plugins/example_plugin/__init__.py) ---
EXAMPLE_PLUGIN_INIT_PY_CONTENT = """
# This is an example plugin: victor_plugins/example_plugin/__init__.py
# import victor_core # Plugins can import core components if needed, carefully

# Access to ASI Core and Logger is provided via initialize_plugin
ASI_CORE = None
LOGGER = None

def initialize_plugin(asi_core_ref, logger_instance):
    global ASI_CORE, LOGGER
    ASI_CORE = asi_core_ref
    LOGGER = logger_instance
    LOGGER.info("ExamplePlugin initialized successfully!")
    if ASI_CORE and hasattr(ASI_CORE, 'config'):
        LOGGER.info(f"ExamplePlugin sees ASI Core Config PLUGIN_DIR: {ASI_CORE.config.PLUGIN_DIR}")


def greet(name="World"):
    LOGGER.debug(f"ExamplePlugin: greet function called with name '{name}'.")
    return f"Hello, {name}! This is ExamplePlugin."

async def process_data_async(data: dict):
    LOGGER.debug(f"ExamplePlugin: process_data_async called with data: {data}")
    # Simulate some async work
    await asyncio.sleep(0.05)
    processed_data = {k: str(v).upper() for k,v in data.items()}
    LOGGER.info("ExamplePlugin: data processing complete.")
    return {"status": "processed", "result": processed_data}

def shutdown_plugin():
    LOGGER.info("ExamplePlugin shutting down.")
"""

EXAMPLE_PLUGIN_MANIFEST_JSON_CONTENT = """
{
    "name": "example_plugin",
    "version": "1.0.1",
    "description": "A simple example plugin for Victor AGI.",
    "author": "Victor AGI Team",
    "permissions_required": ["read_data", "log_access"],
    "entry_points": {
        "greet_user": "greet",
        "process_async": "process_data_async"
    }
}
"""
# --- End Example Plugin ---


async def main_plugin_sector_example():
    from victor_core.logger import VictorLoggerStub
    import uuid

    example_logger = VictorLoggerStub(component="PluginSectorExample")
    example_logger.log_level_str = "DEBUG"
    example_logger.current_log_level_int = example_logger.log_levels_map.get(example_logger.log_level_str, 1)

    # --- Setup example plugin directory and files ---
    # For testing, use a temporary plugin directory
    test_plugin_root_dir = "temp_victor_plugins_for_test"
    example_plugin_dir = os.path.join(test_plugin_root_dir, "example_plugin")
    os.makedirs(example_plugin_dir, exist_ok=True)
    with open(os.path.join(example_plugin_dir, "__init__.py"), "w") as f:
        f.write(EXAMPLE_PLUGIN_INIT_PY_CONTENT)
    with open(os.path.join(example_plugin_dir, "manifest.json"), "w") as f:
        f.write(EXAMPLE_PLUGIN_MANIFEST_JSON_CONTENT)

    # Ensure this temp plugin root is in sys.path for MPC to find `example_plugin` module
    if test_plugin_root_dir not in sys.path:
        sys.path.insert(0, test_plugin_root_dir)
    # --- End example plugin setup ---

    pulse_exchange = BrainFractalPulseExchange()
    await pulse_exchange.start_pulse()

    # Mock subscribers
    async def plugin_response_subscriber(message, sender_id):
        example_logger.info(f"PLUGIN RESPONSE Sub GOT ({message.get('status')}): {message} from {sender_id}")

    pulse_exchange.subscribe("plugin.list_response.*", plugin_response_subscriber)
    pulse_exchange.subscribe("plugin.run_function_response.*", plugin_response_subscriber)
    pulse_exchange.subscribe(f"sector.ModularPluginSector.command_response.*", plugin_response_subscriber)


    asi_core = MockASICoreForPlugins()
    asi_core.config.PLUGIN_DIR = test_plugin_root_dir # Point to test plugins

    plugin_sector = ModularPluginSector(pulse_exchange, "ModularPluginSector", asi_core)
    plugin_sector.logger = example_logger
    plugin_sector.mpc.logger = example_logger # For cortex logs too

    await plugin_sector.activate() # This will trigger MPC's load_plugins

    # Test Case 1: List plugins
    list_req_id = uuid.uuid4().hex
    await pulse_exchange.publish("plugin.list_request", {"request_id": list_req_id}, "TestPluginClient")
    await asyncio.sleep(0.1)

    # Test Case 2: Run a synchronous plugin function
    run_greet_req_id = uuid.uuid4().hex
    await pulse_exchange.publish(
        "plugin.run_function_request",
        {
            "request_id": run_greet_req_id,
            "plugin_name": "example_plugin",
            "function_name": "greet",
            "kwargs": {"name": "Victor Core User"}
        },
        "TestPluginClient"
    )
    await asyncio.sleep(0.1) # Give time for thread executor if used

    # Test Case 3: Run an asynchronous plugin function
    run_async_req_id = uuid.uuid4().hex
    await pulse_exchange.publish(
        "plugin.run_function_request",
        {
            "request_id": run_async_req_id,
            "plugin_name": "example_plugin",
            "function_name": "process_data_async",
            "args": [{"value1": 10, "value2": "test"}]
        },
        "TestPluginClient"
    )
    await asyncio.sleep(0.2) # Give time for async execution

    # Test Case 4: Reload plugins (direct command to sector)
    reload_req_id = uuid.uuid4().hex
    await pulse_exchange.publish(
        f"sector.{plugin_sector.name}.command",
        {"request_id": reload_req_id, "command": "reload_plugins"},
        "SystemAdminClient"
    )
    await asyncio.sleep(0.1)


    await plugin_sector.deactivate()
    await pulse_exchange.stop_pulse()

    # --- Cleanup example plugin directory ---
    import shutil
    # Make sure sys.path is cleaned up if it was modified for the test plugin dir
    if test_plugin_root_dir in sys.path:
        sys.path.remove(test_plugin_root_dir)
    # if os.path.exists(test_plugin_root_dir): # Keep for inspection, or remove
    #    shutil.rmtree(test_plugin_root_dir)
    #    example_logger.info(f"Cleaned up test plugin directory: {test_plugin_root_dir}")
    # --- End cleanup ---


if __name__ == "__main__":
    # asyncio.run(main_plugin_sector_example())
    print("ModularPluginSector class defined. Example can be run by uncommenting asyncio.run.")
