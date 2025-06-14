# run_victor_with_fol.py
# This script launches the Victor AGI with the Flower of Life Network features.

import sys
import os # For potential path manipulations if needed, though direct imports are tried first.
import numpy as np # Often needed by AGI components, good to have.
import pickle # For any direct pickle operations if ever needed at this level.

# --- Attempt to import necessary components ---

# 1. The FoL-enabled AGI subclass
try:
    from fol_integration_module import VictorAGIMonolithWithFOL
    FOL_INTEGRATION_AVAILABLE = True
    print("[Boot INFO - run_victor_with_fol] Successfully imported VictorAGIMonolithWithFOL.")
except ImportError as e_fol_integrate:
    VictorAGIMonolithWithFOL = None # Placeholder
    FOL_INTEGRATION_AVAILABLE = False
    print(f"[Boot CRITICAL - run_victor_with_fol] Could not import VictorAGIMonolithWithFOL from fol_integration_module.py. Error: {e_fol_integrate}")
    print("Ensure fol_integration_module.py and flower_of_life_core.py are in the Python path.")

# 2. Import globals from original script and the new FOL GUI
victor_log_imported = False # Flag to track if victor_log was successfully imported
try:
    from PRIME_OMEGA_STABLE_v5_0_0 import BloodlineRootLaw, victor_log, VICTOR_CONFIG # Keep these
    victor_log_imported = True
    ORIGINAL_PRIME_GLOBALS_AVAILABLE = True
    print("[Boot INFO - run_victor_with_fol] Successfully imported globals from PRIME_OMEGA_STABLE_v5_0_0.py.")
except ImportError as e_prime_globals:
    BloodlineRootLaw = None; VICTOR_CONFIG = {} # Placeholders
    def victor_log_fallback(level, message, component_name="FALLBACK_RUNNER"): print(f"[{level}] [{component_name}] {message}")
    if not victor_log_imported: victor_log = victor_log_fallback # Assign fallback only if import failed
    ORIGINAL_PRIME_GLOBALS_AVAILABLE = False
    print(f"[Boot CRITICAL - run_victor_with_fol] Could not import globals (Bloodline, victor_log, VICTOR_CONFIG) from PRIME_OMEGA_STABLE_v5_0_0.py. Error: {e_prime_globals}")

try:
    from fol_gui_module import VictorCommandCenterWithFOL # New GUI import
    GUI_CLASS_TO_USE = VictorCommandCenterWithFOL
    FOL_GUI_AVAILABLE = True
    print("[Boot INFO - run_victor_with_fol] Successfully imported VictorCommandCenterWithFOL.")
except ImportError as e_fol_gui:
    GUI_CLASS_TO_USE = None # Placeholder
    FOL_GUI_AVAILABLE = False
    # Use victor_log if available, otherwise the fallback print
    log_func = victor_log if victor_log_imported else victor_log_fallback
    log_func("CRITICAL", f"Could not import VictorCommandCenterWithFOL from fol_gui_module.py. GUI will be unavailable. Error: {e_fol_gui}", component_name="Boot")


# --- Main Execution Block ---
if __name__ == "__main__":
    if not FOL_INTEGRATION_AVAILABLE or VictorAGIMonolithWithFOL is None:
        # Use victor_log if available for critical messages too
        log_func = victor_log if victor_log_imported else victor_log_fallback
        log_func("CRITICAL", "[Boot ABORT - run_victor_with_fol] Cannot start: VictorAGIMonolithWithFOL is not available.", component_name="Boot")
        sys.exit(1)

    if not ORIGINAL_PRIME_GLOBALS_AVAILABLE: # Changed from ORIGINAL_CORE_COMPONENTS_AVAILABLE
        log_func = victor_log if victor_log_imported else victor_log_fallback
        log_func("WARNING", "[Boot WARNING - run_victor_with_fol] Original prime globals (like BloodlineRootLaw) might not be available. Proceeding with limited functionality.", component_name="Boot")

    if BloodlineRootLaw: # Check if it was imported
        print(f"\n[VICTOR AGI (with FOL Network) - v{VICTOR_CONFIG.get('version', 'Unknown')}]")
        print(f"BLOODLINE: {BloodlineRootLaw.BLOODLINE}. PRIME DIRECTIVE: {BloodlineRootLaw.PRIME_DIRECTIVE}\n")
    else: # Fallback if BloodlineRootLaw couldn't be imported
        print("\n[VICTOR AGI (with FOL Network) - Version Unknown]")
        print("BLOODLINE LAW UNKNOWN (Import Failed). OPERATION POTENTIALLY UNSTABLE.\n")

    # Define the AGI instance factory to use the FoL-enabled subclass
    def agi_instance_factory_fol():
        # Pass VICTOR_CONFIG if it was successfully imported and used by the AGI constructor
        # The VictorAGIMonolithWithFOL constructor calls super().__init__(config_overrides),
        # which in turn should use the global VICTOR_CONFIG if no overrides are given.
        # So, ensuring VICTOR_CONFIG is available (even if placeholder) is good.
    config_to_use = VICTOR_CONFIG if ORIGINAL_PRIME_GLOBALS_AVAILABLE and VICTOR_CONFIG else None # Adjusted flag
        return VictorAGIMonolithWithFOL(config_overrides=config_to_use)

    # Launch the GUI, if available
    if FOL_GUI_AVAILABLE and GUI_CLASS_TO_USE: # Check if the FoL GUI class is available
        print("[Boot INFO - run_victor_with_fol] Initializing VictorCommandCenterWithFOL with FoL-enabled AGI...")
        app = GUI_CLASS_TO_USE(agi_instance_provider=agi_instance_factory_fol)
        app.mainloop()

        # Ensure AGI shutdown if GUI is closed and AGI might still be running threads
        # Accessing app.agi might be problematic if AGI init failed within VictorCommandCenter
        try:
            if app.agi and app.agi.system_status not in ["shutdown_complete", "shutting_down"]:
                print("[Boot INFO - run_victor_with_fol] GUI closed, ensuring AGI shutdown...")
                app.agi.shutdown(initiated_by="gui_close_cleanup_fol_runner")
        except AttributeError:
            print("[Boot WARNING - run_victor_with_fol] Could not access app.agi for cleanup, AGI might not have initialized in GUI.")

        print("[Boot INFO - run_victor_with_fol] Victor AGI (with FOL Network) session ended.")
    else:
        print("[Boot CRITICAL - run_victor_with_fol] VictorCommandCenterWithFOL GUI not available. Cannot start application in GUI mode.")
        print("Attempting to run AGI core in headless mode if possible (for testing)...")
        try:
            # Minimal headless run for diagnostics or very basic interaction if no GUI
            # This assumes AGI can run without GUI, which it should.
            # The background threads and cognitive cycle might still function.
            agi_instance = agi_instance_factory_fol()
            print(f"AGI Instance {agi_instance.instance_id} created headlessly.") # Requires instance_id attribute
            print("AGI is running in headless mode. Manual termination (Ctrl+C) will be required if it has active background processes.")
            # Keep main thread alive to let background threads run, e.g., for a specific time or until event
            # For now, just print and exit as there's no interactive loop here for headless.
            # A real headless mode would have its own loop or way to feed input.
            # agi_instance.shutdown(initiated_by="headless_auto_terminate") # Or let it run
        except Exception as e_headless:
            print(f"[Boot CRITICAL - run_victor_with_fol] Error during headless AGI startup: {e_headless}")

        print("[Boot INFO - run_victor_with_fol] Headless AGI attempt concluded (or failed).")
