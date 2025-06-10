# victor_modules/plugin_loader.py
# THIS FILE IS DEPRECATED. Use victor_core.sectors.modular_plugin_sector.ModularPluginCortex instead.

import os
import importlib.util
import sys
import json

# Original PLUGIN_DIR calculation. Relative to this file's new location (victor_modules),
# os.path.dirname(__file__) is victor_modules.
# So, ../modules points to a 'modules' directory at the project root.
# This is kept for historical context but is part of the deprecated functionality.
PLUGIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../project_modules_legacy")) # Renamed to avoid conflict
VICTOR_PLUGIN_REGISTRY = {}

# --- DEPRECATION_NOTICE ---
DEPRECATION_MESSAGE = (
    "DEPRECATED: VictorPluginLoader and its functions are deprecated.\n"
    "Please use victor_core.sectors.modular_plugin_sector.ModularPluginCortex for plugin management."
)
# --- END_DEPRECATION_NOTICE ---

def load_victor_plugins():
    """
    DEPRECATED. Loads Victor plugins from the PLUGIN_DIR.
    Modern plugin loading is handled by victor_core.sectors.modular_plugin_sector.ModularPluginCortex.
    """
    print(f"\n{'*' * 20}\n{DEPRECATION_MESSAGE}\n{'*' * 20}\n")
    # Log this using a basic print, as this module might not have VictorLoggerStub configured.
    # If VictorLoggerStub were available and configured:
    # logger = VictorLoggerStub(component="LegacyPluginLoader")
    # logger.warn(DEPRECATION_MESSAGE)

    # The original logic is commented out to prevent accidental execution
    # and potential interference with the new plugin system.
    """
    if not os.path.exists(PLUGIN_DIR):
        print(f"[LegacyPluginLoader] INFO: Plugin directory '{PLUGIN_DIR}' does not exist. Creating.")
        try:
            os.makedirs(PLUGIN_DIR)
        except OSError as e:
            print(f"[LegacyPluginLoader] ERROR: Could not create plugin directory '{PLUGIN_DIR}': {e}")
            return

    print(f"[LegacyPluginLoader] INFO: Scanning for plugins in (now potentially incorrect) legacy path: {PLUGIN_DIR}")

    for filename in os.listdir(PLUGIN_DIR):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            filepath = os.path.join(PLUGIN_DIR, filename)
            try:
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                if spec:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module # Add to sys.modules before exec
                    spec.loader.exec_module(module)

                    # Attempt to load manifest if module has a way to point to it
                    manifest = {}
                    if hasattr(module, 'get_manifest_path'):
                        manifest_path = module.get_manifest_path()
                        manifest = load_manifest(manifest_path) # Changed to take full path
                    elif os.path.exists(os.path.join(PLUGIN_DIR, module_name + ".manifest.json")):
                        manifest = load_manifest(os.path.join(PLUGIN_DIR, module_name + ".manifest.json"))

                    plugin_data = {
                        "module": module,
                        "name": manifest.get("name", module_name),
                        "version": manifest.get("version", "0.0.0"),
                        "description": manifest.get("description", "N/A"),
                        "author": manifest.get("author", "N/A"),
                        "entry_point": manifest.get("entry_point", None) # Function name to call
                    }
                    VICTOR_PLUGIN_REGISTRY[module_name] = plugin_data
                    print(f"[LegacyPluginLoader] INFO: Loaded plugin '{plugin_data['name']}' (from {module_name})")

                    if hasattr(module, 'initialize_plugin'):
                        module.initialize_plugin() # Legacy plugins might not take args

                else:
                    print(f"[LegacyPluginLoader] WARN: Could not create spec for {filepath}")
            except Exception as e:
                print(f"[LegacyPluginLoader] ERROR: Failed to load plugin {module_name} from {filepath}: {e}")
    """
    print(f"[LegacyPluginLoader] INFO: (Deprecated) Plugin loading sequence complete. Registry size: {len(VICTOR_PLUGIN_REGISTRY)}")


def load_manifest(manifest_path): # Changed to take full path
    """
    DEPRECATED. Loads a plugin's manifest file (JSON).
    """
    # print(DEPRECATION_MESSAGE) # Not strictly needed for every function if module is deprecated
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        return manifest
    except FileNotFoundError:
        print(f"[LegacyPluginLoader] WARN: Manifest file not found at {manifest_path}")
    except json.JSONDecodeError:
        print(f"[LegacyPluginLoader] ERROR: Could not decode manifest file {manifest_path}")
    except Exception as e:
        print(f"[LegacyPluginLoader] ERROR: Unexpected error loading manifest {manifest_path}: {e}")
    return {}

# === AUTO-EXPAND HOOK ===
def expand():
    # print(DEPRECATION_MESSAGE) # Redundant if load_victor_plugins shows it clearly.
    print(f'[AUTO_EXPAND] Module {__file__} (Legacy VictorPluginLoader) is DEPRECATED. Please use ModularPluginCortex in victor_core.sectors.modular_plugin_sector. Placeholder expansion activated.')

# Example: Call load_victor_plugins to demonstrate the deprecation message
if __name__ == "__main__":
    print("Running legacy VictorPluginLoader directly to show deprecation notice:")
    # Create a dummy legacy plugin directory for the example to run without erroring on os.listdir
    os.makedirs(PLUGIN_DIR, exist_ok=True)
    with open(os.path.join(PLUGIN_DIR, "example_legacy_plugin.py"), "w") as f:
        f.write("# Example legacy plugin\n")
        f.write("def initialize_plugin(): print('[LegacyExamplePlugin] Initialized')\n")
        f.write("def get_manifest_path(): return __file__.replace('.py', '.manifest.json')\n") # Example
    with open(os.path.join(PLUGIN_DIR, "example_legacy_plugin.manifest.json"), "w") as f:
        json.dump({"name": "LegacyExample", "version": "0.5"}, f)

    load_victor_plugins()
    if VICTOR_PLUGIN_REGISTRY: # This will be empty due to commented out logic
        print(f"Legacy registry (should be empty): {VICTOR_PLUGIN_REGISTRY.keys()}")

    # Clean up dummy legacy dir
    # import shutil
    # if os.path.exists(PLUGIN_DIR):
    #     shutil.rmtree(PLUGIN_DIR) # Be careful with rmtree
    print(f"Note: The actual loading logic in load_victor_plugins is commented out for safety.")
