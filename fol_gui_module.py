import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, scrolledtext
import numpy as np # For handling FoL input/output data
import random # For eval context if user uses random.randn etc.

# Attempt to import the original VictorCommandCenter.
# This is crucial and might fail if PRIME_OMEGA_STABLE_v5_0_0.py is not importable.
try:
    from PRIME_OMEGA_STABLE_v5_0_0 import VictorCommandCenter
    ORIGINAL_GUI_AVAILABLE = True
except ImportError as e:
    print(f"CRITICAL ERROR in fol_gui_module: Could not import VictorCommandCenter from PRIME_OMEGA_STABLE_v5_0_0.py. Error: {e}")
    # Define a placeholder if import fails, so the rest of the file can be parsed.
    # The application will likely not run correctly if this happens.
    class VictorCommandCenter: # type: ignore
        def __init__(self, agi_instance_provider):
            print("Placeholder VictorCommandCenter initialized because original could not be imported.")
            # Minimal Tk setup to prevent immediate crash if super() is called by subclass.
            self.root_tk = tk.Tk()
            self.root_tk.title("Placeholder GUI - Import Failed")
            self.notebook = ttk.Notebook(self.root_tk) # So self.notebook.add exists
            self.tabs = {}
            self.agi = None # Placeholder
            self.after = self.root_tk.after # For bridge calls
            # Mock log_message if bridge calls it
            self.log_message = lambda l,m: print(f"[GUI FALLBACK LOG {l}]: {m}")
            self.root_tk.withdraw() # Keep it hidden

    ORIGINAL_GUI_AVAILABLE = False

class VictorCommandCenterWithFOL(VictorCommandCenter):
    def __init__(self, agi_instance_provider):
        super().__init__(agi_instance_provider)
        # self.agi is set by super().__init__ calling _initialize_agi_and_layout
        # We need to ensure _create_fol_widgets is called after AGI is available.
        # The original _layout_widgets is called in _initialize_agi_and_layout by the parent.
        # We can augment _create_widgets or add a new method called after AGI init.

        # One way is to override _layout_widgets or _initialize_agi_and_layout
        # For simplicity, let's try to add widgets after the main GUI is built.
        # The AGI instance (self.agi) should be available after super().__init__()
        # has run its course (specifically its self.after(100, self._initialize_agi_and_layout))
        # This is a bit tricky due to the deferred AGI initialization in the parent.
        # A safer way: call a method to add our tab once self.agi is confirmed.
        self.after(200, self._try_create_fol_tab) # Try after parent's AGI init

    def _try_create_fol_tab(self):
        if not hasattr(self, 'agi') or self.agi is None:
            # AGI not yet initialized by parent, or failed. Reschedule or error.
            if hasattr(self, 'log_message'): # Check if log_message exists (it should via parent or placeholder)
                 self.log_message("WARNING", "AGI not ready for FOL tab creation, retrying...")
            self.after(500, self._try_create_fol_tab) # Retry
            return

        if not hasattr(self.agi, 'fol_network') or self.agi.fol_network is None:
            if hasattr(self, 'log_message'):
                self.log_message("ERROR", "FOL Network not found in AGI instance. FOL GUI tab cannot be created.")
            return

        self._create_fol_widgets()
        if hasattr(self, 'log_message'):
            self.log_message("INFO", "Flower of Life Network GUI tab created.")


    def _create_fol_widgets(self):
        if not hasattr(self, 'notebook'): # Should have been created by parent
            if hasattr(self, 'log_message'): self.log_message("ERROR", "Notebook not found in GUI. Cannot add FOL tab.")
            return

        self.fol_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.fol_tab, text="Flower of Life Network")
        self.tabs["Flower of Life Network"] = self.fol_tab # Store reference like other tabs

        # Main PanedWindow for FOL tab layout
        fol_main_pane = ttk.PanedWindow(self.fol_tab, orient=tk.HORIZONTAL)
        fol_main_pane.pack(fill=tk.BOTH, expand=True)

        # Left Pane: Network Controls & Node Selection
        fol_left_pane = ttk.Frame(fol_main_pane, padding=5)
        fol_main_pane.add(fol_left_pane, weight=1)

        # Network-level controls
        network_ctrl_frame = ttk.LabelFrame(fol_left_pane, text="Full Network State", padding=5)
        network_ctrl_frame.pack(pady=5, padx=5, fill=tk.X)
        ttk.Button(network_ctrl_frame, text="Load Full FoL Network", command=self._fol_load_network).pack(fill=tk.X, pady=2)
        ttk.Button(network_ctrl_frame, text="Save Full FoL Network", command=self._fol_save_network).pack(fill=tk.X, pady=2)

        # Node-specific controls
        node_ctrl_frame = ttk.LabelFrame(fol_left_pane, text="Node Operations", padding=5)
        node_ctrl_frame.pack(pady=5, padx=5, fill=tk.X, expand=True)

        ttk.Label(node_ctrl_frame, text="Select Node (0-36):").grid(row=0, column=0, padx=2, pady=2, sticky=tk.W)
        self.fol_node_idx_var = tk.StringVar(value="0")
        # Assuming self.agi.fol_network.num_nodes is available; default to 37 if not.
        num_nodes = self.agi.fol_network.num_nodes if self.agi and self.agi.fol_network else 37
        self.fol_node_selector = ttk.Combobox(node_ctrl_frame, textvariable=self.fol_node_idx_var,
                                              values=[str(i) for i in range(num_nodes)], width=5, state="readonly")
        self.fol_node_selector.grid(row=0, column=1, padx=2, pady=2, sticky=tk.EW)

        ttk.Label(node_ctrl_frame, text="Select Block Type:").grid(row=1, column=0, padx=2, pady=2, sticky=tk.W)
        self.fol_block_type_var = tk.StringVar()
        available_blocks = ["None"] # Default
        if self.agi and self.agi.fol_network and hasattr(self.agi.fol_network, 'available_block_classes'):
            available_blocks.extend(list(self.agi.fol_network.available_block_classes.keys()))
        self.fol_block_selector = ttk.Combobox(node_ctrl_frame, textvariable=self.fol_block_type_var,
                                               values=available_blocks, width=25, state="readonly")
        self.fol_block_selector.grid(row=1, column=1, padx=2, pady=2, sticky=tk.EW)
        if available_blocks: self.fol_block_selector.set(available_blocks[0])


        # TODO: Add entry for block_params (e.g., JSON string) for assign_block_to_node
        # For now, assign_block will use default params or only dim.
        ttk.Button(node_ctrl_frame, text="Assign Block to Node", command=self._fol_assign_block).grid(row=2, column=0, columnspan=2, pady=5, sticky=tk.EW)

        ttk.Button(node_ctrl_frame, text="Load Block Weights", command=self._fol_load_weights).grid(row=3, column=0, pady=2, sticky=tk.EW)
        ttk.Button(node_ctrl_frame, text="Save Block Weights", command=self._fol_save_weights).grid(row=3, column=1, pady=2, sticky=tk.EW)

        # Right Pane: Input/Output for FoL
        fol_right_pane = ttk.Frame(fol_main_pane, padding=5)
        fol_main_pane.add(fol_right_pane, weight=2)

        io_frame = ttk.LabelFrame(fol_right_pane, text="Process Input & See Output", padding=5)
        io_frame.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)

        ttk.Label(io_frame, text="Input Data (numpy parsable string, e.g., '1.0,2.0,3.0' or 'np.random.randn(64)'):").pack(anchor=tk.W)
        self.fol_input_text = scrolledtext.ScrolledText(io_frame, height=3, relief=tk.SOLID, borderwidth=1)
        self.fol_input_text.pack(fill=tk.X, pady=2)
        self.fol_input_text.insert(tk.END, "np.random.randn(64)") # Default example input

        ttk.Button(io_frame, text="Process Input via FoL Network", command=self._fol_process_input).pack(pady=5)

        ttk.Label(io_frame, text="FoL Network Output:").pack(anchor=tk.W)
        self.fol_output_text = scrolledtext.ScrolledText(io_frame, height=10, state=tk.DISABLED, relief=tk.SOLID, borderwidth=1)
        self.fol_output_text.pack(fill=tk.BOTH, expand=True, pady=2)

        fol_left_pane.columnconfigure(1, weight=1) # Make comboboxes expand
        node_ctrl_frame.columnconfigure(1, weight=1)


    # --- Callback methods for FOL GUI elements ---
    def _fol_log_output(self, message):
        self.fol_output_text.configure(state=tk.NORMAL)
        self.fol_output_text.insert(tk.END, str(message) + "\n")
        self.fol_output_text.configure(state=tk.DISABLED)
        self.fol_output_text.see(tk.END)

    def _fol_load_network(self):
        if not self.agi or not hasattr(self.agi, 'fol_load_full_network'): return
        filepath = filedialog.askopenfilename(
            title="Load Full Flower of Life Network State",
            defaultextension=".folnet", filetypes=[("FOL Network State", "*.folnet"), ("Pickle files", "*.pkl"), ("All Files", "*.*")]
        )
        if filepath:
            if self.agi.fol_load_full_network(filepath):
                self.log_message("INFO", f"FoL Network state loaded from {filepath}")
                messagebox.showinfo("Load Success", "Flower of Life Network state loaded successfully.")
                # TODO: Refresh relevant parts of FoL tab if needed (e.g. node block assignments)
            else:
                self.log_message("ERROR", f"Failed to load FoL Network state from {filepath}")
                messagebox.showerror("Load Failed", "Failed to load Flower of Life Network state.")

    def _fol_save_network(self):
        if not self.agi or not hasattr(self.agi, 'fol_save_full_network'): return
        filepath = filedialog.asksaveasfilename(
            title="Save Full Flower of Life Network State",
            defaultextension=".folnet", filetypes=[("FOL Network State", "*.folnet"), ("Pickle files", "*.pkl"), ("All Files", "*.*")]
        )
        if filepath:
            if self.agi.fol_save_full_network(filepath):
                self.log_message("INFO", f"FoL Network state saved to {filepath}")
                messagebox.showinfo("Save Success", "Flower of Life Network state saved successfully.")
            else:
                self.log_message("ERROR", f"Failed to save FoL Network state to {filepath}")
                messagebox.showerror("Save Failed", "Failed to save Flower of Life Network state.")

    def _fol_get_selected_node_idx(self):
        try:
            return int(self.fol_node_idx_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid node index selected.")
            return None

    def _fol_assign_block(self):
        if not self.agi or not hasattr(self.agi, 'fol_assign_block'): return
        node_idx = self._fol_get_selected_node_idx()
        if node_idx is None: return

        block_class_name = self.fol_block_type_var.get()
        if not block_class_name or block_class_name == "None":
            # To unassign a block, one might need a specific method or assign a placeholder "NoneBlock"
            # For now, just show error if "None" is selected for assignment.
            messagebox.showwarning("Assign Block", "Please select a valid block type to assign.")
            return

        # Placeholder for block_params - for now, it's empty
        # A more advanced GUI could have dynamic fields for params based on selected block.
        block_params = {}
        # Example: if block_class_name == "VICtorchBlock": block_params['heads'] = 8

        if self.agi.fol_assign_block(node_idx, block_class_name, block_params):
            self.log_message("INFO", f"Block '{block_class_name}' assigned to FoL node {node_idx}.")
            messagebox.showinfo("Assign Success", f"Block '{block_class_name}' assigned to node {node_idx}.")
        else:
            self.log_message("ERROR", f"Failed to assign block '{block_class_name}' to FoL node {node_idx}.")
            messagebox.showerror("Assign Failed", f"Failed to assign block to node {node_idx}.")

    def _fol_load_weights(self):
        if not self.agi or not hasattr(self.agi, 'fol_load_block_weights'): return
        node_idx = self._fol_get_selected_node_idx()
        if node_idx is None: return

        filepath = filedialog.askopenfilename(
            title=f"Load Weights for Block at Node {node_idx}",
            defaultextension=".pkl", filetypes=[("Pickle State Dict", "*.pkl"), ("All Files", "*.*")]
        )
        if filepath:
            if self.agi.fol_load_block_weights(node_idx, filepath):
                self.log_message("INFO", f"Weights loaded for block at FoL node {node_idx} from {filepath}")
                messagebox.showinfo("Load Success", f"Weights loaded for node {node_idx}.")
            else:
                self.log_message("ERROR", f"Failed to load weights for block at FoL node {node_idx}")
                messagebox.showerror("Load Failed", f"Failed to load weights for node {node_idx}.")

    def _fol_save_weights(self):
        if not self.agi or not hasattr(self.agi, 'fol_save_block_weights'): return
        node_idx = self._fol_get_selected_node_idx()
        if node_idx is None: return

        filepath = filedialog.asksaveasfilename(
            title=f"Save Weights for Block at Node {node_idx}",
            defaultextension=".pkl", filetypes=[("Pickle State Dict", "*.pkl"), ("All Files", "*.*")]
        )
        if filepath:
            if self.agi.fol_save_block_weights(node_idx, filepath): # True if saved to file
                self.log_message("INFO", f"Weights saved for block at FoL node {node_idx} to {filepath}")
                messagebox.showinfo("Save Success", f"Weights saved for node {node_idx}.")
            else:
                self.log_message("ERROR", f"Failed to save weights for block at FoL node {node_idx}")
                messagebox.showerror("Save Failed", f"Failed to save weights for node {node_idx}.")

    def _fol_process_input(self):
        if not self.agi or not hasattr(self.agi, 'fol_process_input'): return

        input_str = self.fol_input_text.get("1.0", tk.END).strip()
        if not input_str:
            messagebox.showwarning("Input Error", "Please provide input data for the FoL network.")
            return

        try:
            # Try to evaluate the input string. This allows numpy expressions.
            # This is potentially unsafe if arbitrary code is entered.
            # For a controlled environment, it's flexible.
            # A safer alternative would be to parse comma-separated floats.
            input_data = eval(input_str, {"np": np, "numpy": np, "random": random}) # Provide numpy and random
            if not isinstance(input_data, (np.ndarray, list)): # Allow list of inputs too
                # Attempt to convert to numpy array if it's a scalar or simple list of numbers
                input_data = np.array(input_data)

        except Exception as e_eval:
            self._fol_log_output(f"Input Evaluation Error: {e_eval}")
            messagebox.showerror("Input Error", f"Could not parse input data: {e_eval}")
            return

        self._fol_log_output(f"Processing FoL input: {input_str} (parsed as type: {type(input_data)})")

        try:
            response = self.agi.fol_process_input(input_data) # This should be a numpy array or similar
            self._fol_log_output(f"FoL Network Response:\n{response}")
            if response is not None:
                 self._fol_log_output(f"Response shape: {response.shape}, dtype: {response.dtype}")

        except Exception as e_proc:
            self._fol_log_output(f"FoL Processing Error: {e_proc}")
            import traceback
            self._fol_log_output(traceback.format_exc())


# This allows testing this GUI module standalone if needed, though it's meant to be imported.
if __name__ == '__main__':
    print("Testing FoL GUI Module Standalone...")

    # Mock AGI for standalone GUI testing
    class MockFOLNetworkOrchestrator:
        def __init__(self, num_nodes=37, model_dim=64, **kwargs):
            self.num_nodes = num_nodes
            self.model_dim = model_dim
            self.available_block_classes = { # Mocked from flower_of_life_core.py
                "VICtorchBlock": "VICtorchBlock_Class", "OmegaTensorBlock": "OmegaTensorBlock_Class",
                "FractalAttentionBlock": "FractalAttentionBlock_Class"
            }
            print(f"MockFOLNetworkOrchestrator initialized with {num_nodes} nodes, model_dim {model_dim}")

        def assign_block_to_node(self,idx,name,**params): print(f"Mock Assign: {name} to {idx} with {params}"); return True
        def load_block_weights_to_node(self,idx,sd): print(f"Mock Load W: for {idx}"); return True
        def save_block_weights_from_node(self,idx): print(f"Mock Save W: for {idx}"); return {"mock_weights":np.random.rand(3)}
        def process_input(self,data): print(f"Mock Process: {type(data)}"); return np.array(["mock_response", np.random.rand(self.model_dim if isinstance(self.model_dim, int) else 3)])
        def save_network_state(self,fp): print(f"Mock Save Net: to {fp}"); return True
        def load_network_state(self,fp): print(f"Mock Load Net: from {fp}"); return True

    class MockAgiWithFol:
        def __init__(self, config_overrides=None):
            self.fol_network = MockFOLNetworkOrchestrator()
            # Mock other things GUI might expect from AGI
            self.config = {"version": "MockFOLAGI_v0.1"}
            self.gui_bridge = None # Usually set by AGI, but GUI sets it back
            self.system_status = "mock_idle"
            # Ensure log_message exists on the mock AGI itself if GUI tries to call self.agi.log_message
            self.log_message = lambda l,m: print(f"[MOCK AGI LOG {l}]: {m}")


        # Mock the passthrough methods
        def fol_assign_block(self,idx,name,params): return self.fol_network.assign_block_to_node(idx,name,**params)
        def fol_load_block_weights(self,idx,sd_or_path): return self.fol_network.load_block_weights_to_node(idx,sd_or_path)
        def fol_save_block_weights(self,idx,save_path=None): return self.fol_network.save_block_weights_from_node(idx) # Simplified for mock
        def fol_process_input(self,data): return self.fol_network.process_input(data)
        def fol_save_full_network(self,fp): return self.fol_network.save_network_state(fp)
        def fol_load_full_network(self,fp): return self.fol_network.load_network_state(fp)

        # Mock methods called by VictorCommandCenter parent during its init
        def process_text_input(self, text, source="", metadata=None): self.log_message("CMD", f"Mock AGI received: {text}")
        def get_status_report(self, for_gui=False): return {"version":"Mock", "status":"testing"} if for_gui else "Mock Status"
        def shutdown(self, initiated_by="test"): self.log_message("INFO", f"Mock AGI shutdown by {initiated_by}")


    if ORIGINAL_GUI_AVAILABLE:
        mock_agi_provider = lambda: MockAgiWithFol()
        app = VictorCommandCenterWithFOL(agi_instance_provider=mock_agi_provider)

        # The AGI instance in app is created after a delay.
        # To link bridge for logging from AGI to GUI:
        def link_bridge_to_mock_gui():
            if app.agi and hasattr(app.agi, 'gui_bridge'):
                 # In real scenario, AGI creates bridge, GUI sets itself on bridge.
                 # Here, mock AGI doesn't have a full bridge, so we ensure GUI's log_message is used.
                 # This is mainly for testing the GUI's own logging calls.
                 # The parent VictorCommandCenter's _initialize_agi_and_layout already does:
                 # self.agi.gui_bridge.set_gui_app(self)
                 # So, if app.agi.gui_bridge exists, it should be usable.
                 pass

        app.after(300, link_bridge_to_mock_gui) # Delay to allow AGI and its bridge to be set up
        app.mainloop()
    else:
        print("Original VictorCommandCenter not available, cannot run standalone GUI test for VictorCommandCenterWithFOL.")

```
