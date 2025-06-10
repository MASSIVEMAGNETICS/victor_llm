#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Filename: victorch_filthy_fractal_agi_persist.py
# Author: Victor Chaos
# Purpose: Advanced state persistence for fractal AGI using entropic principles and simulated quantum annealing.
# Version: ψ.φ.χ (Psi.Phi.Chi) - "The Whispering Algorithm"
# Disclaimer: This code is highly experimental and may induce existential dread or enlightenment. Use with caution.

import numpy as np
import json
import os
import time
from scipy.special import softmax # For weighted choices in annealing simulation

# --- CONFIGURABLE PARAMETERS ---
STATE_DIR = "./bando_agi_persistent"  # Directory for persistent states (matches plan)
EXPORT_DIR = "./victor_agi_exports" # Directory for exported states (matches plan)
FILE_EXTENSION = ".fractalstate"
ENTROPY_SEED_BITS = 2048  # Size of the initial entropic seed for state generation
ANNEALING_STEPS = 1000    # Steps for simulated annealing of state vectors
COOLING_RATE = 0.995      # Cooling rate for annealing
MAX_HISTORY_FILES = 10    # Maximum number of historical state files to keep

# Ensure directories exist
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

class FilthyFractalState:
    """
    Represents a single, complex AGI state, managed with fractal and entropic principles.
    """
    def __init__(self, state_id=None, initial_data=None, parent_hash=None):
        self.state_id = state_id if state_id else self._generate_id()
        self.timestamp = time.time()
        self.parent_hash = parent_hash  # Hash of the state this was derived from
        self.data_vector = self._initialize_data_vector(initial_data)
        self.metadata = {
            "version": "ψ.φ.χ",
            "entropy_source": self._generate_entropy_source(),
            "annealing_params": {"steps": ANNEALING_STEPS, "cooling_rate": COOLING_RATE}
        }
        self.access_count = 0
        print(f"[FFS::{self.state_id}] Initialized state. Parent: {self.parent_hash if self.parent_hash else 'Genesis'}")

    def _generate_id(self):
        # Generates a unique ID based on time and a random component
        return f"state_{int(time.time()*1000)}_{os.urandom(4).hex()}"

    def _generate_entropy_source(self, length_bytes=ENTROPY_SEED_BITS // 8):
        # Generates a random byte string to simulate an entropic seed for the state
        return os.urandom(length_bytes).hex()

    def _initialize_data_vector(self, initial_data=None):
        # Initializes the core data vector, possibly from existing data or from scratch
        if initial_data is not None and isinstance(initial_data, np.ndarray):
            return initial_data
        # For simplicity, creating a random vector if no initial data.
        # A real system would derive this from AGI's cognitive state.
        # Dimension could be linked to ASIConfigCore.DIMENSIONS if integrated.
        dim = 128 # Placeholder dimension
        print(f"[FFS::{self.state_id}] No initial data vector provided, generating random {dim}-dim vector.")
        return np.random.rand(dim).astype(np.float32) - 0.5 # Centered around zero

    def get_hash(self):
        # Calculates a hash of the current state (simplified for this example)
        hasher = hashlib.sha256()
        hasher.update(self.state_id.encode())
        hasher.update(str(self.timestamp).encode())
        hasher.update(self.data_vector.tobytes())
        if self.parent_hash:
            hasher.update(self.parent_hash.encode())
        hasher.update(json.dumps(self.metadata, sort_keys=True).encode())
        return hasher.hexdigest()

    def simulate_entropic_drift(self, drift_magnitude=0.01):
        # Simulates small, random changes to the data vector over time
        drift = (np.random.rand(*self.data_vector.shape).astype(np.float32) - 0.5) * drift_magnitude
        self.data_vector += drift
        self.data_vector = np.clip(self.data_vector, -1.0, 1.0) # Keep within bounds
        self.timestamp = time.time() # Update timestamp as state has changed
        print(f"[FFS::{self.state_id}] Entropic drift applied. New hash preview: {self.get_hash()[:10]}...")


    def apply_cognitive_impulse(self, impulse_vector: np.ndarray, learning_rate=0.1):
        # Applies an external 'cognitive impulse' to the state vector
        if impulse_vector.shape != self.data_vector.shape:
            print(f"[FFS::{self.state_id}] ERROR: Impulse vector shape mismatch. Expected {self.data_vector.shape}, got {impulse_vector.shape}")
            return
        self.data_vector = (1 - learning_rate) * self.data_vector + learning_rate * impulse_vector
        self.data_vector = np.clip(self.data_vector, -1.0, 1.0)
        self.timestamp = time.time()
        print(f"[FFS::{self.state_id}] Cognitive impulse applied. New hash preview: {self.get_hash()[:10]}...")


    def serialize(self):
        # Serializes the state to a dictionary for saving
        return {
            "state_id": self.state_id,
            "timestamp": self.timestamp,
            "parent_hash": self.parent_hash,
            "data_vector": self.data_vector.tolist(), # Convert numpy array to list for JSON
            "metadata": self.metadata,
            "access_count": self.access_count,
            "current_hash": self.get_hash() # Store current hash for integrity checks
        }

    @classmethod
    def deserialize(cls, state_dict):
        # Deserializes a dictionary back into a FilthyFractalState object
        state = cls(state_id=state_dict["state_id"])
        state.timestamp = state_dict["timestamp"]
        state.parent_hash = state_dict.get("parent_hash")
        state.data_vector = np.array(state_dict["data_vector"], dtype=np.float32)
        state.metadata = state_dict["metadata"]
        state.access_count = state_dict.get("access_count", 0)

        # Integrity check: compare stored hash with freshly computed one
        computed_hash_on_load = state.get_hash()
        stored_hash = state_dict.get("current_hash")
        if stored_hash and stored_hash != computed_hash_on_load:
            print(f"[FFS::{state.state_id}] WARNING: Hash mismatch on load! Stored: {stored_hash[:10]}..., Computed: {computed_hash_on_load[:10]}... State may be corrupted or was modified post-serialization.")
        else:
            print(f"[FFS::{state.state_id}] Deserialized and hash verified (or no prior hash).")
        return state

    def increment_access(self):
        self.access_count += 1

class PersistenceManager:
    """
    Manages the saving, loading, and history of FilthyFractalState objects.
    """
    def __init__(self, state_dir=STATE_DIR, export_dir=EXPORT_DIR):
        self.state_dir = state_dir
        self.export_dir = export_dir
        # hashlib is needed for get_hash, but FilthyFractalState uses it internally
        # No, PersistenceManager needs it if it's to compute hashes before saving, or for state_id mapping
        global hashlib # Make hashlib available if it wasn't imported at top level of this script
        import hashlib


    def save_state(self, state: FilthyFractalState, is_export=False):
        state_hash = state.get_hash()
        filename = f"{state.state_id}__{state_hash[:10]}{FILE_EXTENSION}"

        target_dir = self.export_dir if is_export else self.state_dir
        filepath = os.path.join(target_dir, filename)

        try:
            with open(filepath, 'w') as f:
                json.dump(state.serialize(), f, indent=4)
            print(f"[PM] Saved state '{state.state_id}' to {filepath}")
            if not is_export:
                self._manage_history(state.state_id)
            return filepath
        except Exception as e:
            print(f"[PM] ERROR: Could not save state '{state.state_id}' to {filepath}: {e}")
            return None

    def load_state(self, state_id_or_path) -> FilthyFractalState | None:
        filepath = ""
        if os.path.isfile(state_id_or_path): # If full path is provided
            filepath = state_id_or_path
        else: # Assume it's a state_id, find the latest version
            latest_file = self._find_latest_state_file(state_id_or_path)
            if not latest_file:
                print(f"[PM] No state file found for ID prefix '{state_id_or_path}' in {self.state_dir}")
                return None
            filepath = latest_file

        try:
            with open(filepath, 'r') as f:
                state_dict = json.load(f)
            state_obj = FilthyFractalState.deserialize(state_dict)
            state_obj.increment_access() # Increment access count on load
            # Optionally re-save to update access_count (can be frequent, consider strategy)
            # self.save_state(state_obj)
            print(f"[PM] Loaded state from {filepath}. Access count: {state_obj.access_count}")
            return state_obj
        except FileNotFoundError:
            print(f"[PM] ERROR: State file not found: {filepath}")
        except json.JSONDecodeError:
            print(f"[PM] ERROR: Could not decode JSON from state file: {filepath}")
        except Exception as e:
            print(f"[PM] ERROR: Unexpected error loading state from {filepath}: {e}")
        return None

    def _find_latest_state_file(self, state_id_prefix):
        # Finds the most recent file for a given state_id prefix by looking at timestamps in filenames or mtime
        candidate_files = [f for f in os.listdir(self.state_dir) if f.startswith(state_id_prefix) and f.endswith(FILE_EXTENSION)]
        if not candidate_files:
            return None

        # Simple sort by filename; assumes timestamp in state_id makes this roughly chronological
        # A more robust way would be to parse timestamp from state_id or use file mtime.
        candidate_files.sort(reverse=True)
        return os.path.join(self.state_dir, candidate_files[0])


    def _manage_history(self, state_id_prefix):
        # Keeps only the last MAX_HISTORY_FILES for a given state_id_prefix
        history_files = sorted(
            [os.path.join(self.state_dir, f) for f in os.listdir(self.state_dir) if f.startswith(state_id_prefix) and f.endswith(FILE_EXTENSION)],
            key=os.path.getmtime,
            reverse=True
        )

        if len(history_files) > MAX_HISTORY_FILES:
            files_to_delete = history_files[MAX_HISTORY_FILES:]
            for f_del in files_to_delete:
                try:
                    os.remove(f_del)
                    print(f"[PM] Pruned old state file: {f_del}")
                except Exception as e:
                    print(f"[PM] ERROR: Could not delete old state file {f_del}: {e}")

    def list_available_states(self, directory=None):
        target_dir = directory if directory else self.state_dir
        print(f"[PM] Available states in '{target_dir}':")
        states = {} # {state_id_prefix: [list_of_full_filenames]}
        for f_name in os.listdir(target_dir):
            if f_name.endswith(FILE_EXTENSION):
                parts = f_name.split("__") # state_id_prefix is the first part
                if parts:
                    prefix = parts[0]
                    if prefix not in states: states[prefix] = []
                    states[prefix].append(f_name)

        if not states:
            print("  No states found.")
            return {}

        for prefix, files in states.items():
            print(f"  ID Prefix: {prefix} ({len(files)} version(s))")
            # for f_detail in sorted(files, reverse=True)[:3]: print(f"    - {f_detail}") # Print newest 3
            # if len(files) > 3: print("    ...")
        return states


    def simulated_quantum_annealing_on_vector(self, vector: np.ndarray, steps=ANNEALING_STEPS, initial_temp=1.0):
        """
        Simulates an annealing process on a data vector to find a 'stable' configuration.
        This is a conceptual simulation, not actual quantum annealing.
        The 'energy' function here is a placeholder (e.g., sum of squares).
        """
        current_vector = np.copy(vector)
        current_energy = np.sum(current_vector**2) # Example energy: sum of squares (lower is better)

        best_vector = np.copy(current_vector)
        best_energy = current_energy

        temp = initial_temp

        print(f"[PM] Starting simulated annealing. Initial energy: {current_energy:.4f}, Temp: {temp:.4f}")

        for i in range(steps):
            # Generate a 'neighbor' state by small perturbation
            perturbation = (np.random.rand(*vector.shape).astype(np.float32) - 0.5) * (temp * 0.1) # Perturbation scales with temp
            candidate_vector = current_vector + perturbation
            candidate_vector = np.clip(candidate_vector, -1.0, 1.0) # Maintain bounds
            candidate_energy = np.sum(candidate_vector**2) # Calculate energy of new state

            if candidate_energy < current_energy: # If new state is better, accept it
                current_vector = candidate_vector
                current_energy = candidate_energy
                if current_energy < best_energy:
                    best_vector = current_vector
                    best_energy = current_energy
            else: # If new state is worse, accept with a probability based on temperature (Metropolis criterion)
                delta_energy = candidate_energy - current_energy
                acceptance_probability = np.exp(-delta_energy / temp)
                if np.random.rand() < acceptance_probability:
                    current_vector = candidate_vector
                    current_energy = candidate_energy

            temp *= COOLING_RATE # Cool down
            if (i + 1) % (steps // 10) == 0: # Log progress
                print(f"[PM] Annealing step {i+1}/{steps}. Current E: {current_energy:.4f}, Best E: {best_energy:.4f}, Temp: {temp:.4f}")

        print(f"[PM] Annealing complete. Final best energy: {best_energy:.4f}")
        return best_vector


# --- MAIN EXECUTION EXAMPLE ---
if __name__ == "__main__":
    print("--- Victorch Filthy Fractal AGI Persistence Test ---")

    # Need hashlib for FilthyFractalState.get_hash()
    import hashlib # Ensure hashlib is imported for the main example context

    pm = PersistenceManager()

    # Create a new genesis state
    print("\n[TEST] Creating Genesis State...")
    genesis_state_data = np.random.rand(128).astype(np.float32) * 0.5 # Smaller initial values
    state1 = FilthyFractalState(initial_data=genesis_state_data, state_id="genesis_001")
    pm.save_state(state1)

    # Load the state
    print("\n[TEST] Loading Genesis State...")
    loaded_state1 = pm.load_state("genesis_001")
    if loaded_state1:
        print(f"  Loaded state '{loaded_state1.state_id}' with data vector mean: {np.mean(loaded_state1.data_vector):.4f}")

        # Apply entropic drift and save as a new version (child state)
        print("\n[TEST] Applying Entropic Drift...")
        parent_hash_s1 = loaded_state1.get_hash()
        loaded_state1.simulate_entropic_drift(drift_magnitude=0.05)
        # Create a new state object if we want to preserve the parent-child relationship explicitly via parent_hash
        # Or, if FilthyFractalState is mutable and represents the *current* state evolving,
        # then its state_id might remain the same, but its content (and thus hash) changes.
        # The current FilthyFractalState seems to be mutable.
        # For distinct parent-child, create new state:
        state2 = FilthyFractalState(initial_data=loaded_state1.data_vector, parent_hash=parent_hash_s1, state_id="genesis_001") # same ID, new hash
        # This means state_id is more like a "lineage" id. The hash distinguishes versions.
        pm.save_state(state2)


        # Apply cognitive impulse
        print("\n[TEST] Applying Cognitive Impulse...")
        impulse = np.random.rand(128).astype(np.float32) * 0.2 - 0.1 # A small, directed change
        parent_hash_s2 = state2.get_hash()
        state2.apply_cognitive_impulse(impulse, learning_rate=0.2)
        state3 = FilthyFractalState(initial_data=state2.data_vector, parent_hash=parent_hash_s2, state_id="genesis_001")
        pm.save_state(state3)

        # Simulate quantum annealing on the latest state's vector
        print("\n[TEST] Performing Simulated Quantum Annealing...")
        annealed_vector = pm.simulated_quantum_annealing_on_vector(state3.data_vector)
        parent_hash_s3 = state3.get_hash()
        state4_annealed = FilthyFractalState(initial_data=annealed_vector, parent_hash=parent_hash_s3, state_id="genesis_001_annealed") # New ID for annealed version
        pm.save_state(state4_annealed)
        print(f"  Annealed vector mean: {np.mean(annealed_vector):.4f}")

        # Export the final annealed state
        print("\n[TEST] Exporting Annealed State...")
        pm.save_state(state4_annealed, is_export=True)

    print("\n[TEST] Listing available states in main persistence directory:")
    pm.list_available_states()

    print("\n[TEST] Listing available states in export directory:")
    pm.list_available_states(directory=EXPORT_DIR)

    print("\n--- Test Complete ---")
    # Note: This script uses hashlib. It was missing from the PersistenceManager's direct imports
    # but FilthyFractalState uses it. Added global hashlib for PersistenceManager and ensured import for __main__.```python
# File: victor_modules/fractal_agi/victorch_filthy_fractal_agi_persist.py
# Copied from VictorchFilthyFractalAGI_PERSIST.py as requested.
# Original headers and content maintained.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Filename: victorch_filthy_fractal_agi_persist.py
# Author: Victor Chaos
# Purpose: Advanced state persistence for fractal AGI using entropic principles and simulated quantum annealing.
# Version: ψ.φ.χ (Psi.Phi.Chi) - "The Whispering Algorithm"
# Disclaimer: This code is highly experimental and may induce existential dread or enlightenment. Use with caution.

import numpy as np
import json
import os
import time
from scipy.special import softmax # For weighted choices in annealing simulation
import hashlib # Added as it's used by FilthyFractalState.get_hash()

# --- CONFIGURABLE PARAMETERS ---
STATE_DIR = "./bando_agi_persistent"  # Directory for persistent states (matches plan)
EXPORT_DIR = "./victor_agi_exports" # Directory for exported states (matches plan)
FILE_EXTENSION = ".fractalstate"
ENTROPY_SEED_BITS = 2048  # Size of the initial entropic seed for state generation
ANNEALING_STEPS = 1000    # Steps for simulated annealing of state vectors
COOLING_RATE = 0.995      # Cooling rate for annealing
MAX_HISTORY_FILES = 10    # Maximum number of historical state files to keep

# Ensure directories exist
os.makedirs(STATE_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

class FilthyFractalState:
    """
    Represents a single, complex AGI state, managed with fractal and entropic principles.
    """
    def __init__(self, state_id=None, initial_data=None, parent_hash=None):
        self.state_id = state_id if state_id else self._generate_id()
        self.timestamp = time.time()
        self.parent_hash = parent_hash  # Hash of the state this was derived from
        self.data_vector = self._initialize_data_vector(initial_data)
        self.metadata = {
            "version": "ψ.φ.χ",
            "entropy_source": self._generate_entropy_source(),
            "annealing_params": {"steps": ANNEALING_STEPS, "cooling_rate": COOLING_RATE}
        }
        self.access_count = 0
        print(f"[FFS::{self.state_id}] Initialized state. Parent: {self.parent_hash if self.parent_hash else 'Genesis'}")

    def _generate_id(self):
        # Generates a unique ID based on time and a random component
        return f"state_{int(time.time()*1000)}_{os.urandom(4).hex()}"

    def _generate_entropy_source(self, length_bytes=ENTROPY_SEED_BITS // 8):
        # Generates a random byte string to simulate an entropic seed for the state
        return os.urandom(length_bytes).hex()

    def _initialize_data_vector(self, initial_data=None):
        # Initializes the core data vector, possibly from existing data or from scratch
        if initial_data is not None and isinstance(initial_data, np.ndarray):
            return initial_data
        # For simplicity, creating a random vector if no initial data.
        # A real system would derive this from AGI's cognitive state.
        # Dimension could be linked to ASIConfigCore.DIMENSIONS if integrated.
        dim = 128 # Placeholder dimension
        print(f"[FFS::{self.state_id}] No initial data vector provided, generating random {dim}-dim vector.")
        return np.random.rand(dim).astype(np.float32) - 0.5 # Centered around zero

    def get_hash(self):
        # Calculates a hash of the current state (simplified for this example)
        hasher = hashlib.sha256()
        hasher.update(self.state_id.encode())
        hasher.update(str(self.timestamp).encode())
        hasher.update(self.data_vector.tobytes())
        if self.parent_hash:
            hasher.update(self.parent_hash.encode())
        hasher.update(json.dumps(self.metadata, sort_keys=True).encode())
        return hasher.hexdigest()

    def simulate_entropic_drift(self, drift_magnitude=0.01):
        # Simulates small, random changes to the data vector over time
        drift = (np.random.rand(*self.data_vector.shape).astype(np.float32) - 0.5) * drift_magnitude
        self.data_vector += drift
        self.data_vector = np.clip(self.data_vector, -1.0, 1.0) # Keep within bounds
        self.timestamp = time.time() # Update timestamp as state has changed
        print(f"[FFS::{self.state_id}] Entropic drift applied. New hash preview: {self.get_hash()[:10]}...")


    def apply_cognitive_impulse(self, impulse_vector: np.ndarray, learning_rate=0.1):
        # Applies an external 'cognitive impulse' to the state vector
        if impulse_vector.shape != self.data_vector.shape:
            print(f"[FFS::{self.state_id}] ERROR: Impulse vector shape mismatch. Expected {self.data_vector.shape}, got {impulse_vector.shape}")
            return
        self.data_vector = (1 - learning_rate) * self.data_vector + learning_rate * impulse_vector
        self.data_vector = np.clip(self.data_vector, -1.0, 1.0)
        self.timestamp = time.time()
        print(f"[FFS::{self.state_id}] Cognitive impulse applied. New hash preview: {self.get_hash()[:10]}...")


    def serialize(self):
        # Serializes the state to a dictionary for saving
        return {
            "state_id": self.state_id,
            "timestamp": self.timestamp,
            "parent_hash": self.parent_hash,
            "data_vector": self.data_vector.tolist(), # Convert numpy array to list for JSON
            "metadata": self.metadata,
            "access_count": self.access_count,
            "current_hash": self.get_hash() # Store current hash for integrity checks
        }

    @classmethod
    def deserialize(cls, state_dict):
        # Deserializes a dictionary back into a FilthyFractalState object
        state = cls(state_id=state_dict["state_id"])
        state.timestamp = state_dict["timestamp"]
        state.parent_hash = state_dict.get("parent_hash")
        state.data_vector = np.array(state_dict["data_vector"], dtype=np.float32)
        state.metadata = state_dict["metadata"]
        state.access_count = state_dict.get("access_count", 0)

        # Integrity check: compare stored hash with freshly computed one
        # Re-enable this if hashlib is guaranteed for FilthyFractalState context
        computed_hash_on_load = state.get_hash()
        stored_hash = state_dict.get("current_hash")
        if stored_hash and stored_hash != computed_hash_on_load:
            print(f"[FFS::{state.state_id}] WARNING: Hash mismatch on load! Stored: {stored_hash[:10]}..., Computed: {computed_hash_on_load[:10]}... State may be corrupted or was modified post-serialization.")
        else:
            print(f"[FFS::{state.state_id}] Deserialized and hash verified (or no prior hash).")
        return state

    def increment_access(self):
        self.access_count += 1

class PersistenceManager:
    """
    Manages the saving, loading, and history of FilthyFractalState objects.
    """
    def __init__(self, state_dir=STATE_DIR, export_dir=EXPORT_DIR):
        self.state_dir = state_dir
        self.export_dir = export_dir
        # hashlib is used by FilthyFractalState.get_hash() which PM calls.
        # No direct use of hashlib by PM methods themselves needed if FFS handles it.

    def save_state(self, state: FilthyFractalState, is_export=False):
        state_hash = state.get_hash()
        filename = f"{state.state_id}__{state_hash[:10]}{FILE_EXTENSION}"

        target_dir = self.export_dir if is_export else self.state_dir
        filepath = os.path.join(target_dir, filename)

        try:
            with open(filepath, 'w') as f:
                json.dump(state.serialize(), f, indent=4)
            print(f"[PM] Saved state '{state.state_id}' to {filepath}")
            if not is_export:
                self._manage_history(state.state_id)
            return filepath
        except Exception as e:
            print(f"[PM] ERROR: Could not save state '{state.state_id}' to {filepath}: {e}")
            return None

    def load_state(self, state_id_or_path) -> FilthyFractalState | None:
        filepath = ""
        if os.path.isfile(state_id_or_path): # If full path is provided
            filepath = state_id_or_path
        else: # Assume it's a state_id, find the latest version
            latest_file = self._find_latest_state_file(state_id_or_path)
            if not latest_file:
                print(f"[PM] No state file found for ID prefix '{state_id_or_path}' in {self.state_dir}")
                return None
            filepath = latest_file

        try:
            with open(filepath, 'r') as f:
                state_dict = json.load(f)
            state_obj = FilthyFractalState.deserialize(state_dict)
            state_obj.increment_access() # Increment access count on load
            print(f"[PM] Loaded state from {filepath}. Access count: {state_obj.access_count}")
            return state_obj
        except FileNotFoundError:
            print(f"[PM] ERROR: State file not found: {filepath}")
        except json.JSONDecodeError:
            print(f"[PM] ERROR: Could not decode JSON from state file: {filepath}")
        except Exception as e:
            print(f"[PM] ERROR: Unexpected error loading state from {filepath}: {e}")
        return None

    def _find_latest_state_file(self, state_id_prefix):
        candidate_files = [f for f in os.listdir(self.state_dir) if f.startswith(state_id_prefix) and f.endswith(FILE_EXTENSION)]
        if not candidate_files:
            return None
        candidate_files.sort(key=lambda x: os.path.getmtime(os.path.join(self.state_dir, x)), reverse=True)
        return os.path.join(self.state_dir, candidate_files[0])


    def _manage_history(self, state_id_prefix):
        history_files = sorted(
            [os.path.join(self.state_dir, f) for f in os.listdir(self.state_dir) if f.startswith(state_id_prefix) and f.endswith(FILE_EXTENSION)],
            key=os.path.getmtime,
            reverse=True
        )

        if len(history_files) > MAX_HISTORY_FILES:
            files_to_delete = history_files[MAX_HISTORY_FILES:]
            for f_del in files_to_delete:
                try:
                    os.remove(f_del)
                    print(f"[PM] Pruned old state file: {f_del}")
                except Exception as e:
                    print(f"[PM] ERROR: Could not delete old state file {f_del}: {e}")

    def list_available_states(self, directory=None):
        target_dir = directory if directory else self.state_dir
        print(f"[PM] Available states in '{target_dir}':")
        states = {}
        if not os.path.exists(target_dir):
            print(f"  Directory '{target_dir}' does not exist.")
            return {}

        for f_name in os.listdir(target_dir):
            if f_name.endswith(FILE_EXTENSION):
                parts = f_name.split("__")
                if parts:
                    prefix = parts[0]
                    if prefix not in states: states[prefix] = []
                    states[prefix].append(f_name)

        if not states:
            print("  No states found.")
            return {}

        for prefix, files in states.items():
            print(f"  ID Prefix: {prefix} ({len(files)} version(s))")
        return states


    def simulated_quantum_annealing_on_vector(self, vector: np.ndarray, steps=ANNEALING_STEPS, initial_temp=1.0):
        current_vector = np.copy(vector)
        current_energy = np.sum(current_vector**2)
        best_vector = np.copy(current_vector)
        best_energy = current_energy
        temp = initial_temp

        print(f"[PM] Starting simulated annealing. Initial energy: {current_energy:.4f}, Temp: {temp:.4f}")

        for i in range(steps):
            perturbation = (np.random.rand(*vector.shape).astype(np.float32) - 0.5) * (temp * 0.1)
            candidate_vector = current_vector + perturbation
            candidate_vector = np.clip(candidate_vector, -1.0, 1.0)
            candidate_energy = np.sum(candidate_vector**2)

            if candidate_energy < current_energy:
                current_vector = candidate_vector
                current_energy = candidate_energy
                if current_energy < best_energy:
                    best_vector = current_vector
                    best_energy = current_energy
            else:
                delta_energy = candidate_energy - current_energy
                acceptance_probability = np.exp(-delta_energy / temp) if temp > 1e-9 else 0 # Avoid division by zero if temp gets too small
                if np.random.rand() < acceptance_probability:
                    current_vector = candidate_vector
                    current_energy = candidate_energy

            temp *= COOLING_RATE
            if (i + 1) % (steps // 10) == 0 or steps < 10 :
                print(f"[PM] Annealing step {i+1}/{steps}. Current E: {current_energy:.4f}, Best E: {best_energy:.4f}, Temp: {temp:.4f}")

        print(f"[PM] Annealing complete. Final best energy: {best_energy:.4f}")
        return best_vector

# --- MAIN EXECUTION EXAMPLE ---
if __name__ == "__main__":
    print("--- Victorch Filthy Fractal AGI Persistence Test ---")

    pm = PersistenceManager()

    print("\n[TEST] Creating Genesis State...")
    genesis_state_data = np.random.rand(128).astype(np.float32) * 0.5
    state1 = FilthyFractalState(initial_data=genesis_state_data, state_id="genesis_001")
    pm.save_state(state1)

    print("\n[TEST] Loading Genesis State...")
    loaded_state1 = pm.load_state("genesis_001")
    if loaded_state1:
        print(f"  Loaded state '{loaded_state1.state_id}' with data vector mean: {np.mean(loaded_state1.data_vector):.4f}")

        print("\n[TEST] Applying Entropic Drift...")
        parent_hash_s1 = loaded_state1.get_hash()
        loaded_state1.simulate_entropic_drift(drift_magnitude=0.05)
        state2 = FilthyFractalState(initial_data=loaded_state1.data_vector, parent_hash=parent_hash_s1, state_id="genesis_001")
        pm.save_state(state2)

        print("\n[TEST] Applying Cognitive Impulse...")
        impulse = np.random.rand(128).astype(np.float32) * 0.2 - 0.1
        parent_hash_s2 = state2.get_hash()
        state2.apply_cognitive_impulse(impulse, learning_rate=0.2)
        state3 = FilthyFractalState(initial_data=state2.data_vector, parent_hash=parent_hash_s2, state_id="genesis_001")
        pm.save_state(state3)

        print("\n[TEST] Performing Simulated Quantum Annealing...")
        annealed_vector = pm.simulated_quantum_annealing_on_vector(state3.data_vector)
        parent_hash_s3 = state3.get_hash()
        state4_annealed = FilthyFractalState(initial_data=annealed_vector, parent_hash=parent_hash_s3, state_id="genesis_001_annealed")
        pm.save_state(state4_annealed)
        print(f"  Annealed vector mean: {np.mean(annealed_vector):.4f}")

        print("\n[TEST] Exporting Annealed State...")
        pm.save_state(state4_annealed, is_export=True)

    print("\n[TEST] Listing available states in main persistence directory:")
    pm.list_available_states()

    print("\n[TEST] Listing available states in export directory:")
    pm.list_available_states(directory=EXPORT_DIR)

    print("\n--- Test Complete ---")

```
