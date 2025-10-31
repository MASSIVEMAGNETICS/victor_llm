"""
VICTOR_AGI_LLM.py
Version: v1.0.0-GODCORE-MONOLITH-FINAL (Conceptual)
This file implements the InfiniteDevUI for Victor AGI.
"""

import sys
import argparse
import os
import json
import time
import traceback

# Check for numpy first
try:
    import numpy as np
except ImportError:
    print("ERROR: numpy is required. Please run: pip install -r requirements.txt")
    sys.exit(1)

# Check for openai
try:
    import openai
except ImportError:
    print("WARNING: openai package not found. LLM features will be limited.")
    print("To enable full functionality: pip install openai")
    openai = None

# Check for tkinter
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, simpledialog, filedialog, scrolledtext
except ImportError:
    print("FATAL ERROR: Tkinter is required for the VICTOR_AGI Command Center GUI.")
    print("\nInstallation instructions:")
    print("  Ubuntu/Debian: sudo apt-get install python3-tk")
    print("  Mac: Included with Python from python.org")
    print("  Windows: Included with standard Python installation")
    sys.exit(1)

try:
    import pyttsx3
except ImportError:  # voice output is optional
    pyttsx3 = None

# Optional import for vision functions. Not required to run basic chat.
try:
    import cv2  # type: ignore
except Exception:  # opencv might not be installed
    cv2 = None

# Placeholder for classes that might be defined elsewhere or simplified
class FractalState: # Simplified placeholder
    def __init__(self):
        self.state = {"modules": {}, "vars": {}}
        self.history = []
        self.timelines = {"main": []}
        self.current_timeline_idx = "main"
    def save_state(self, desc): self.history.append({"desc": desc, "ts": time.time(), "timeline_idx": self.current_timeline_idx})
    def undo(self): return False # Placeholder
    def redo(self): return False # Placeholder
    def get_timeline_log(self, last_n=15): return [{"ts":time.time(), "desc":"Timeline log entry placeholder"}]
    def switch_timeline(self, idx): return False
    def fork_timeline(self, name): return "new_timeline_placeholder"
    def fractal_export(self, path): pass
    def fractal_import(self, path): pass

class NLPInterface: # Simplified placeholder
    def parse(self, text, cot=False): return {"sentiment":0, "intent":"unknown", "keywords":[], "entities":[], "summary":text, "cot_trace":[]}
    def suggest_patch(self, code, error): return "# No suggestion available."
    def autocomplete_code(self, text, context): return text

class ReasoningEngine: # Simplified placeholder
    def reason(self, facts, query, verbose=False): return {"decision":"Unknown", "meta":{}, "summaries":[]}

class TriadManager: # Simplified placeholder
    def __init__(self): self.default_teacher = None; self.default_student = None; self.default_verifier = None
    def run(self, problem, teacher, student, verifier): return "Triad verdict placeholder."

class EvolutionLoop: # Simplified placeholder
    def run(self, force_mutate_code=False): pass

class AwarenessLoop: # Simplified placeholder
    def run(self): return "Introspection placeholder.", {}

class BloodlineLaw: # Simplified placeholder
    def enforce(self, state): pass

class DiagnosticSystem: # Simplified placeholder
    def generate_report(self): return "Diagnostics placeholder."

class VictorASIOmniBrainGodcore: # Adapted from VictorAGI, more complex
    def __init__(self, voice: bool = False, gui_callback=None):
        self.voice = bool(voice and pyttsx3)
        self.history = [] # For chat history, separate from fractal state history
        self.gui_callback = gui_callback
        if self.voice:
            self.engine = pyttsx3.init()
        else:
            self.engine = None

        self.fractal_state = FractalState() # Placeholder
        self.nlp = NLPInterface() # Placeholder
        self.reasoner = ReasoningEngine() # Placeholder
        self.triad = TriadManager() # Placeholder
        self.evolution_loop = EvolutionLoop() # Placeholder
        self.awareness_loop = AwarenessLoop() # Placeholder
        self.bloodline_law = BloodlineLaw() # Placeholder
        self.diagnostics = DiagnosticSystem() # Placeholder

        # Initialize some example modules and variables for UI testing
        self.fractal_state.state["modules"]["example_module"] = type('Mod', (object,), {'name': 'example_module', 'code': 'print("Hello")', 'doc': 'Prints hello', 'last_eval_time': None, 'last_eval_error': None, 'last_eval_output': None})()
        self.fractal_state.state["vars"]["sample_var"] = 123
        self.fractal_state.save_state("AGI Genesis state with examples")


    def set_gui_callback(self, callback):
        self.gui_callback = callback

    def _speak(self, text: str) -> None:
        if self.engine:
            self.engine.say(text)
            self.engine.runAndWait()

    def respond_to_text_input(self, message: str) -> str: # Renamed for clarity
        self.history.append({"role": "user", "content": message})
        # Simplified: In a real scenario, might use self.nlp, self.reasoner, etc.
        # For now, let's assume it's a direct call to a chat model if available
        if "OPENAI_API_KEY" in os.environ and openai.api_key:
            try:
                resp = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo", # Or a config-driven model
                    messages=self.history,
                )
                reply = resp["choices"][0]["message"]["content"]
            except Exception as e:
                reply = f"Error communicating with OpenAI: {e}"
        else:
            reply = "AI Core: OpenAI API key not set. Responding with placeholder."

        self.history.append({"role": "assistant", "content": reply})
        if self.gui_callback:
            self.gui_callback() # Update UI after response
        return reply

    def save_snapshot(self, name): # Placeholder for GUI interaction
        self.fractal_state.save_state(name)

    def rollback_snapshot(self, name): # Placeholder
        # This needs more logic to find the actual snapshot by name
        if self.fractal_state.history: # Simplistic rollback to last
            # In a real system, you'd search history for 'name'
            self.fractal_state.history.pop()
            return True
        return False

    def add_module(self, name, code, doc, autorun=False): # Placeholder
        self.fractal_state.state["modules"][name] = type('Mod', (object,), {'name': name, 'code': code, 'doc': doc, 'last_eval_time': None, 'last_eval_error': None, 'last_eval_output': None})()
        self.fractal_state.save_state(f"Added module {name}")
        if autorun: self.run_module(name)

    def run_module(self, name): # Placeholder
        mod = self.fractal_state.state["modules"].get(name)
        if mod:
            try:
                # Simplified execution
                exec_globals = {"agi": self, "variables": self.fractal_state.state["vars"], "print": lambda *args: setattr(mod, 'last_eval_output', " ".join(map(str,args)))}
                exec(mod.code, exec_globals)
                mod.last_eval_error = None
            except Exception as e:
                mod.last_eval_error = str(e)
                mod.last_eval_output = None
            mod.last_eval_time = time.time()
            self.fractal_state.save_state(f"Ran module {name}")

    def get_state_report(self): # Placeholder
        return {"status": "Nominal", "timeline": self.fractal_state.current_timeline_idx, "history_len": len(self.fractal_state.history)}

    def get_loaded_packages_info(self):
        print("[AGI] get_loaded_packages_info called")
        tk_version = "unknown"
        if 'tk' in sys.modules:
            try: tk_version = tk.Tcl().eval('info patchlevel')
            except Exception: tk_version = "unknown via Tcl"

        numpy_version = "unknown"
        if 'numpy' in sys.modules and hasattr(sys.modules['numpy'], '__version__'): # Check if numpy was imported
            numpy_version = sys.modules['numpy'].__version__
        else:
            numpy_version = "Not imported or no version info"


        return {
            "sys_version": sys.version.split()[0],
            "os_name": os.name,
            "tkinter_patchlevel": tk_version,
            "numpy_version": numpy_version, # Corrected access
            "custom_victor_core": "loaded_successfully_v1.0.0-GODCORE-MONOLITH-FINAL"
        }

    def save_state_full(self): # Placeholder, for safe_quit
        self.fractal_state.save_state("System shutdown state save")
        print("AGI state saved (simulated).")

    def handle_critical_error(self, error_message):
        print(f"CRITICAL ERROR: {error_message}")
        # Potentially trigger safe mode, save state, etc.

class InfiniteDevUI(tk.Tk):
    def __init__(self, agi_core):
        super().__init__()
        self.agi = agi_core
        self.agi.set_gui_callback(self.update_dashboard)
        self.title("Victor OmniDev Godcore – v1.0.0-GODCORE-MONOLITH-FINAL")
        self.geometry("1900x1000")
        self.protocol("WM_DELETE_WINDOW", self.safe_quit)
        self.configure(bg="#181818")
        self.style = ttk.Style(self)
        self.style.theme_use('clam')

        self.base_bg = "#181818"; self.sidebar_bg = "#111111"; self.entry_bg = "#2A2A2A"
        self.text_fg = "#E0E0E0"; self.neon_green = "#39FF14"; self.neon_cyan = "#00FFFF"
        self.neon_magenta = "#FF00FF"; self.highlight_bg = "#004477"

        self.style.configure("TFrame", background=self.base_bg)
        self.style.configure("TLabel", background=self.base_bg, foreground=self.text_fg, font=("Consolas", 10))
        self.style.configure("TButton", background="#333333", foreground=self.neon_cyan, font=("Consolas", 10, "bold"), borderwidth=1, relief=tk.FLAT)
        self.style.map("TButton", background=[('active', '#444444'), ('pressed', '#222222')], foreground=[('active', self.neon_magenta)])
        self.style.configure("TEntry", fieldbackground=self.entry_bg, foreground=self.neon_green, insertbackground=self.neon_green, borderwidth=1, relief=tk.FLAT)
        self.style.configure("TText", background=self.entry_bg, foreground=self.neon_green, insertbackground=self.neon_green, borderwidth=1, relief=tk.FLAT, font=("Consolas", 10))
        self.style.configure("TListbox", background=self.entry_bg, foreground=self.neon_green, selectbackground=self.highlight_bg, selectforeground=self.text_fg, borderwidth=1, relief=tk.FLAT)
        self.style.configure("TLabelFrame", background=self.base_bg, borderwidth=1, relief=tk.SOLID)
        self.style.configure("TLabelFrame.Label", foreground=self.neon_cyan, background=self.base_bg, font=("Consolas", 11, "bold"))
        self.style.configure("Header.TLabel", foreground=self.neon_green, font=("Consolas", 12, "bold"))

        self.style.configure("Sidebar.TFrame", background=self.sidebar_bg)
        self.style.configure("CategoryHeader.TButton", font=("Consolas", 11, "bold"), background="#202020", foreground=self.neon_green, borderwidth=0, relief=tk.FLAT, anchor=tk.W, padding=(10,8))
        self.style.map("CategoryHeader.TButton", background=[('active', '#2c2c2c')], foreground=[('active', self.neon_cyan)])
        self.style.configure("SidebarItem.TButton", font=("Consolas", 10), background=self.sidebar_bg, foreground=self.text_fg, borderwidth=0, relief=tk.FLAT, anchor=tk.W, padding=(20,5))
        self.style.map("SidebarItem.TButton", background=[('active', '#2c2c2c')], foreground=[('active', self.neon_cyan)])
        self.style.configure("SidebarItems.TFrame", background=self.sidebar_bg)

        self._graph_loop_running = False; self._graph_loop_id = None; self.section_states = {}

        # StringVars for Model Parameters
        self.model_temp_var = tk.DoubleVar(value=0.7) # For Scale
        self.model_max_tokens_var = tk.StringVar(value="4096")
        self.model_top_p_var = tk.DoubleVar(value=0.9) # For Scale
        self.model_name_var = tk.StringVar(value="gpt-4-turbo-preview")

        # StringVars for Core System Params
        self.core_log_level_var = tk.StringVar(value="INFO")
        self.core_max_recursion_var = tk.StringVar(value="20")

        # StringVars for Memory Params
        self.mem_stm_cap_var = tk.StringVar(value="5000")
        self.mem_ltm_autosave_var = tk.DoubleVar(value=240) # For Scale

        # StringVars for UI Skin/Theme
        self.ui_accent_color_var = tk.StringVar(value=self.neon_magenta)


        self.create_layout()
        self.update_dashboard(); self.start_auto_refresh()

    def _create_collapsible_section(self, parent_frame, category_title, items_config):
        category_frame = ttk.Frame(parent_frame, style="Sidebar.TFrame")
        category_frame.pack(fill=tk.X, expand=True, pady=1)
        header_button = ttk.Button(category_frame,text=f"▶ {category_title}",command=lambda: toggle_items(),style="CategoryHeader.TButton")
        header_button.pack(fill=tk.X)
        items_frame = ttk.Frame(category_frame, style="SidebarItems.TFrame")
        for item_text, item_command in items_config:
            item_button = ttk.Button(items_frame,text=item_text,command=item_command,style="SidebarItem.TButton")
            item_button.pack(fill=tk.X, padx=(10,0))
        self.section_states[category_title] = {'button': header_button, 'frame': items_frame, 'expanded': False}
        def toggle_items(): # Nested function, captures variables from parent scope
            state = self.section_states[category_title]; state['expanded'] = not state['expanded']
            if state['expanded']:
                state['button'].config(text=f"▼ {category_title}")
                state['frame'].pack(fill=tk.X, expand=True, pady=(0, 5))
            else:
                state['button'].config(text=f"▶ {category_title}")
                state['frame'].pack_forget()

    def create_layout(self):
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL); main_pane.pack(fill='both', expand=True, padx=5, pady=5)
        left_frame = ttk.Frame(main_pane, style="Sidebar.TFrame", width=300); left_frame.pack_propagate(False); main_pane.add(left_frame, weight=0)
        self.sidebar_container = ttk.Frame(left_frame, style="Sidebar.TFrame"); self.sidebar_container.pack(side=tk.TOP, fill=tk.X, pady=(0,10))

        sidebar_categories = {
            "VICTOR CORE": [("New Chat", self._handle_new_chat), ("Search Chats", self._handle_search_chats)],
            "LIBRARY": [("Project Library", self._handle_project_library), ("Custom Experts", self._handle_custom_experts)],
            "OPERATIONS": [("Swarm Mode", self._handle_swarm_mode)],
            "DEVELOPER": [("Developer Options", self._handle_developer_options), ("Loaded Packages Inspector", self._handle_inspect_packages)],
            "STATE & TIMELINES": [("Snapshot State", self.save_snap), ("Rollback to Snapshot", self.rollback_snap), ("UNDO", self.undo), ("REDO", self.redo),
                ("Export Fractal State", self.export_state), ("Import Fractal State", self.import_state), ("Fork Current Timeline", self.fork_timeline)],
            "TOOLS & PARAMETERS": [("Core System", self._handle_core_system_tools), ("Model Parameters", self._handle_model_parameters_tools),
                ("Memory Parameters", self._handle_memory_parameters_tools), ("UI Skin/Theme", self._handle_ui_skin_tools)],
            "SETTINGS": [("Preferences", self._handle_preferences_settings), ("System Settings", self._handle_system_settings)]}
        for category, items in sidebar_categories.items(): self._create_collapsible_section(self.sidebar_container, category, items)

        history_timeline_frame = ttk.Frame(left_frame, style="Sidebar.TFrame"); history_timeline_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        ttk.Label(history_timeline_frame, text="FRACTAL HISTORY", style="Header.TLabel").pack(pady=(10,2), anchor=tk.W, padx=5)
        self.history_box = tk.Listbox(history_timeline_frame, bg=self.entry_bg, fg=self.neon_green, selectbackground=self.highlight_bg, selectforeground=self.text_fg, height=10, relief=tk.FLAT, borderwidth=0)
        self.history_box.pack(fill="both", expand=True, padx=5, pady=2)
        ttk.Label(history_timeline_frame, text="TIMELINE CONTROL", style="Header.TLabel").pack(pady=(10,2), anchor=tk.W, padx=5)
        self.timeline_selector = ttk.Combobox(history_timeline_frame, state="readonly", values=list(self.agi.fractal_state.timelines.keys()), font=("Consolas", 9))
        self.timeline_selector.pack(fill="x", padx=5, pady=2); self.timeline_selector.bind("<<ComboboxSelected>>", self.switch_timeline_event)
        self.timeline_log_box = scrolledtext.ScrolledText(history_timeline_frame, height=8, bg=self.entry_bg, fg=self.neon_green, wrap="word", relief=tk.FLAT, borderwidth=0, font=("Consolas",9))
        self.timeline_log_box.pack(fill="both", expand=True, padx=5, pady=(2,5))

        center_frame = ttk.Frame(main_pane, style="TFrame"); main_pane.add(center_frame, weight=3)
        top_center_pane = ttk.PanedWindow(center_frame, orient=tk.VERTICAL); top_center_pane.pack(fill='both', expand=True)
        module_var_frame = ttk.Frame(top_center_pane, style="TFrame"); top_center_pane.add(module_var_frame, weight=1)
        mod_frame = ttk.LabelFrame(module_var_frame, text="MODULES / LOGIC"); mod_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.mod_list = tk.Listbox(mod_frame, bg=self.entry_bg, fg=self.neon_green, selectbackground=self.highlight_bg, selectforeground=self.text_fg, relief=tk.FLAT, borderwidth=0)
        self.mod_list.pack(fill="both", expand=True); self.mod_list.bind("<<ListboxSelect>>", self.on_module_select); self.mod_list.bind('<Double-Button-1>', lambda event: self.run_module())
        mod_buttons_frame = ttk.Frame(mod_frame, style="TFrame"); mod_buttons_frame.pack(fill=tk.X, pady=3)
        ttk.Button(mod_buttons_frame, text="Add", command=self.add_module).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(mod_buttons_frame, text="Edit", command=self.edit_module).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(mod_buttons_frame, text="Run", command=self.run_module).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(mod_buttons_frame, text="Del", command=self.del_module).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        var_frame = ttk.LabelFrame(module_var_frame, text="GLOBAL VARIABLES"); var_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.var_list = tk.Listbox(var_frame, bg=self.entry_bg, fg=self.neon_green, selectbackground=self.highlight_bg, selectforeground=self.text_fg, relief=tk.FLAT, borderwidth=0)
        self.var_list.pack(fill="both", expand=True)
        var_buttons_frame = ttk.Frame(var_frame, style="TFrame"); var_buttons_frame.pack(fill=tk.X, pady=3)
        ttk.Button(var_buttons_frame, text="Add", command=self.add_variable).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        ttk.Button(var_buttons_frame, text="Edit", command=self.edit_variable).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
        wire_frame = ttk.LabelFrame(top_center_pane, text="LOGIC/WIRE GRAPH"); top_center_pane.add(wire_frame, weight=2)
        self.wire_canvas = WireGraphCanvas(wire_frame, self.agi.fractal_state, width=600, height=400, bg="#101010") # Placeholder
        self.wire_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        canvas_toolbar = ttk.Frame(wire_frame, style="TFrame"); canvas_toolbar.pack(fill="x", pady=(2, 5))
        ttk.Button(canvas_toolbar, text="▶ Run", command=self._start_graph_loop).pack(side=tk.LEFT, padx=(5,2))
        ttk.Button(canvas_toolbar, text="⏸ Pause", command=self._pause_graph_loop).pack(side=tk.LEFT, padx=2)
        ttk.Button(canvas_toolbar, text="⏹ Stop", command=self._stop_graph_loop).pack(side=tk.LEFT, padx=2)

        right_frame = ttk.Frame(main_pane, style="TFrame"); main_pane.add(right_frame, weight=2)
        omnimind_frame = ttk.LabelFrame(right_frame, text="OMNIMIND / AI COPILOT"); omnimind_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.ai_input = ttk.Entry(omnimind_frame, width=70, font=("Consolas", 10)); self.ai_input.pack(fill="x", padx=4, pady=(4,2)); self.ai_input.bind('<Return>', lambda e: self.ask_ai())
        ttk.Button(omnimind_frame, text="Ask Victor (NLP / Code / Reason)", command=self.ask_ai).pack(fill=tk.X, pady=2, padx=4)
        self.ai_output = scrolledtext.ScrolledText(omnimind_frame, height=15, wrap="word", bg=self.entry_bg, fg=self.neon_green, relief=tk.FLAT, borderwidth=0, font=("Consolas", 10))
        self.ai_output.pack(fill="both", expand=True, padx=4, pady=2)
        control_buttons_frame = ttk.LabelFrame(right_frame, text="CORE CONTROLS"); control_buttons_frame.pack(fill="x", padx=5, pady=5)
        core_buttons = [("ZeroShot Triad", self.zero_shot_ui), ("Self-Evolution", self.trigger_evolution), ("Self-Introspection", self.perform_introspection), ("Enforce Law", self.enforce_bloodline), ("Diagnostics", self.diagnostics)]
        for i, (text, cmd) in enumerate(core_buttons): ttk.Button(control_buttons_frame, text=text, command=cmd).grid(row=i//2, column=i%2, sticky=tk.EW, padx=2, pady=2)
        control_buttons_frame.columnconfigure((0,1), weight=1)
        status_frame = ttk.LabelFrame(right_frame, text="AGI CORE STATUS"); status_frame.pack(fill="x", padx=5, pady=5)
        self.core_status_text = tk.Text(status_frame, height=6, wrap="word", bg=self.entry_bg, fg=self.text_fg, relief=tk.FLAT, borderwidth=0, font=("Consolas",9))
        self.core_status_text.pack(fill="both", expand=True, padx=2, pady=2); self.core_status_text.config(state='disabled')

        self.notebook = ttk.Notebook(right_frame) # Notebook for tools tabs

        # Core System Params Tab
        self.tools_core_system_tab = ttk.Frame(self.notebook, style="TFrame", padding=10)
        ttk.Label(self.tools_core_system_tab, text="Log Level:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.core_log_level_entry = ttk.Entry(self.tools_core_system_tab, textvariable=self.core_log_level_var)
        self.core_log_level_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(self.tools_core_system_tab, text="Apply Log Level", command=self._apply_log_level).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(self.tools_core_system_tab, text="Max Recursion Depth:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.core_max_recursion_entry = ttk.Entry(self.tools_core_system_tab, textvariable=self.core_max_recursion_var)
        self.core_max_recursion_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(self.tools_core_system_tab, text="Apply Max Recursion", command=self._apply_max_recursion).grid(row=1, column=2, padx=5, pady=5)
        self.tools_core_system_tab.columnconfigure(1, weight=1)
        self.notebook.add(self.tools_core_system_tab, text="Core System")

        # Model Parameters Tab
        self.tools_model_params_tab = ttk.Frame(self.notebook, style="TFrame", padding=10)
        ttk.Label(self.tools_model_params_tab, text="Temperature:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.model_temp_scale = ttk.Scale(self.tools_model_params_tab, from_=0.0, to=1.0, orient=tk.HORIZONTAL, variable=self.model_temp_var, command=self._update_temp_label)
        self.model_temp_scale.set(0.7)
        self.model_temp_scale.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.model_temp_value_label = ttk.Label(self.tools_model_params_tab, text=f"{self.model_temp_var.get():.2f}")
        self.model_temp_value_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Label(self.tools_model_params_tab, text="Max Tokens:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.model_max_tokens_entry = ttk.Entry(self.tools_model_params_tab, textvariable=self.model_max_tokens_var)
        self.model_max_tokens_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(self.tools_model_params_tab, text="Apply Max Tokens", command=self._apply_max_tokens).grid(row=1, column=2, padx=5, pady=5)
        ttk.Label(self.tools_model_params_tab, text="Top-P:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.model_top_p_scale = ttk.Scale(self.tools_model_params_tab, from_=0.0, to=1.0, orient=tk.HORIZONTAL, variable=self.model_top_p_var, command=self._update_top_p_label)
        self.model_top_p_scale.set(0.9)
        self.model_top_p_scale.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)
        self.model_top_p_value_label = ttk.Label(self.tools_model_params_tab, text=f"{self.model_top_p_var.get():.2f}")
        self.model_top_p_value_label.grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Label(self.tools_model_params_tab, text="Model Name:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.model_name_entry = ttk.Entry(self.tools_model_params_tab, textvariable=self.model_name_var, width=40)
        self.model_name_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(self.tools_model_params_tab, text="Apply Model Name", command=self._apply_model_name).grid(row=3, column=2, padx=5, pady=5)
        self.tools_model_params_tab.columnconfigure(1, weight=1)
        self.notebook.add(self.tools_model_params_tab, text="Model Params")

        # Memory Parameters Tab
        self.tools_memory_params_tab = ttk.Frame(self.notebook, style="TFrame", padding=10)
        ttk.Label(self.tools_memory_params_tab, text="STM Capacity:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.mem_stm_cap_entry = ttk.Entry(self.tools_memory_params_tab, textvariable=self.mem_stm_cap_var)
        self.mem_stm_cap_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(self.tools_memory_params_tab, text="Apply STM Capacity", command=self._apply_stm_capacity).grid(row=0, column=2, padx=5, pady=5)
        ttk.Label(self.tools_memory_params_tab, text="LTM Auto-Save (sec):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.mem_ltm_autosave_scale = ttk.Scale(self.tools_memory_params_tab, from_=30, to=600, orient=tk.HORIZONTAL, variable=self.mem_ltm_autosave_var, command=self._update_ltm_autosave_label)
        self.mem_ltm_autosave_scale.set(240)
        self.mem_ltm_autosave_scale.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        self.mem_ltm_autosave_value_label = ttk.Label(self.tools_memory_params_tab, text=f"{int(self.mem_ltm_autosave_var.get())}s")
        self.mem_ltm_autosave_value_label.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.tools_memory_params_tab.columnconfigure(1, weight=1)
        self.notebook.add(self.tools_memory_params_tab, text="Memory Params")

        # UI Skin/Theme Tab
        self.tools_ui_skin_tab = ttk.Frame(self.notebook, style="TFrame", padding=10)
        ttk.Label(self.tools_ui_skin_tab, text="Select Theme:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        theme_button_frame = ttk.Frame(self.tools_ui_skin_tab, style="TFrame")
        ttk.Button(theme_button_frame, text="Theme: Glitch", command=lambda: self._apply_theme("glitch")).pack(side=tk.LEFT, padx=2)
        ttk.Button(theme_button_frame, text="Theme: Neon", command=lambda: self._apply_theme("neon")).pack(side=tk.LEFT, padx=2)
        ttk.Button(theme_button_frame, text="Theme: Synthwave", command=lambda: self._apply_theme("synthwave")).pack(side=tk.LEFT, padx=2)
        theme_button_frame.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        ttk.Label(self.tools_ui_skin_tab, text="Accent Color (Hex):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.ui_accent_color_entry = ttk.Entry(self.tools_ui_skin_tab, textvariable=self.ui_accent_color_var)
        self.ui_accent_color_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        ttk.Button(self.tools_ui_skin_tab, text="Apply Accent Color", command=self._apply_accent_color).grid(row=1, column=2, padx=5, pady=5)
        self.tools_ui_skin_tab.columnconfigure(1, weight=1)
        self.notebook.add(self.tools_ui_skin_tab, text="UI Skin/Theme")

        self.notebook.pack_forget() # Initially hide the notebook until a tool item is clicked

    def _handle_new_chat(self): self.status_bar("Action: New Chat (placeholder)")
    def _handle_search_chats(self): self.status_bar("Action: Search Chats (placeholder)")
    def _handle_project_library(self): self.status_bar("Action: Project Library (placeholder)")
    def _handle_custom_experts(self): self.status_bar("Action: Custom Experts (placeholder)")
    def _handle_swarm_mode(self): self.status_bar("Action: Swarm Mode (placeholder)")
    def _handle_developer_options(self): self.status_bar("Action: Developer Options (placeholder)")
    def _handle_inspect_packages(self):
        self.status_bar("Action: Inspect Packages...")
        if self.agi and hasattr(self.agi, 'get_loaded_packages_info'):
            info = self.agi.get_loaded_packages_info()
            output_str = "\n--- Loaded Packages Inspector ---\n" + json.dumps(info, indent=2) + "\n"
            self.ai_output.config(state='normal'); self.ai_output.insert(tk.END, output_str); self.ai_output.config(state='disabled'); self.ai_output.see(tk.END)
        else: self.status_bar("Error: AGI or package info function not available.")

    def _show_tool_tab(self, tab_to_select):
        self.notebook.pack(fill='both', expand=True, padx=5, pady=(0,5)) # Ensure notebook is visible
        self.notebook.select(tab_to_select)
        # Ensure other main content area widgets (omnimind_frame, control_buttons_frame, status_frame) are hidden
        # This might need adjustment based on how these frames are packed in relation to the notebook
        # For now, assume they are siblings in right_frame and self.notebook.pack() will place it correctly.

    def _handle_core_system_tools(self): self.status_bar("Tool Panel: Core System"); self._show_tool_tab(self.tools_core_system_tab)
    def _handle_model_parameters_tools(self): self.status_bar("Tool Panel: Model Params"); self._show_tool_tab(self.tools_model_params_tab)
    def _handle_memory_parameters_tools(self): self.status_bar("Tool Panel: Memory Params"); self._show_tool_tab(self.tools_memory_params_tab)
    def _handle_ui_skin_tools(self): self.status_bar("Tool Panel: UI Skin/Theme"); self._show_tool_tab(self.tools_ui_skin_tab)

    def _handle_preferences_settings(self): self.status_bar("Action: Preferences (placeholder)")
    def _handle_system_settings(self): self.status_bar("Action: System Settings (placeholder)")

    def _update_temp_label(self, value): self.model_temp_value_label.config(text=f"{float(value):.2f}")
    def _apply_max_tokens(self): self.status_bar(f"Model Param: Max Tokens set to {self.model_max_tokens_var.get()} (UI only)")
    def _update_top_p_label(self, value): self.model_top_p_value_label.config(text=f"{float(value):.2f}")
    def _apply_model_name(self): self.status_bar(f"Model Param: Model Name set to {self.model_name_var.get()} (UI only)")
    def _apply_log_level(self): self.status_bar(f"Core Param: Log Level set to {self.core_log_level_var.get()} (UI only)")
    def _apply_max_recursion(self): self.status_bar(f"Core Param: Max Recursion set to {self.core_max_recursion_var.get()} (UI only)")
    def _apply_stm_capacity(self): self.status_bar(f"Memory Param: STM Capacity set to {self.mem_stm_cap_var.get()} (UI only)")
    def _update_ltm_autosave_label(self, value): self.mem_ltm_autosave_value_label.config(text=f"{int(float(value))}s")
    def _apply_theme(self, theme_name): self.status_bar(f"UI Action: Apply theme '{theme_name}' (placeholder)")
    def _apply_accent_color(self): self.status_bar(f"UI Action: Accent color set to {self.ui_accent_color_var.get()} (placeholder)")

    def update_dashboard(self):
        if hasattr(self.agi, 'fractal_state') and hasattr(self.agi.fractal_state, 'history'):
            self.history_box.delete(0, tk.END)
            for snap in self.agi.fractal_state.history:
                description = snap.get('desc', '')
                if not description.startswith("Init") and not description.startswith("AGI Genesis"):
                    ts_str = time.ctime(snap['ts']) if 'ts' in snap and isinstance(snap['ts'], (int, float)) else "Invalid TS"
                    tl_idx = snap.get('timeline_idx', 'N/A')
                    self.history_box.insert(tk.END, f"[{ts_str}] [{tl_idx}] {description}")
        if hasattr(self.agi, 'fractal_state') and "modules" in self.agi.fractal_state.state:
            self.mod_list.delete(0, tk.END)
            for name in self.agi.fractal_state.state["modules"]: self.mod_list.insert(tk.END, name)
        if hasattr(self.agi, 'fractal_state') and "vars" in self.agi.fractal_state.state:
            self.var_list.delete(0, tk.END)
            for v_name, v_val in self.agi.fractal_state.state["vars"].items():
                max_len = 70; display_val_str = ""
                try: display_val_str = json.dumps(v_val) if isinstance(v_val, (dict, list, tuple)) else str(v_val)
                except TypeError: display_val_str = str(v_val)
                if len(display_val_str) > max_len: display_val_str = display_val_str[:max_len-3] + "..."
                self.var_list.insert(tk.END, f"{v_name}: {display_val_str}")
        if hasattr(self.agi, 'fractal_state'):
            self.timeline_selector['values'] = list(self.agi.fractal_state.timelines.keys())
            self.timeline_selector.set(self.agi.fractal_state.current_timeline_idx)
            self.timeline_log_box.config(state='normal'); self.timeline_log_box.delete('1.0', tk.END)
            for entry in self.agi.fractal_state.get_timeline_log(last_n=15): self.timeline_log_box.insert(tk.END, f"[{time.ctime(entry['ts'])}] {entry['desc']}\n")
            self.timeline_log_box.config(state='disabled')
        if hasattr(self, 'wire_canvas'): self.wire_canvas.redraw()
        if hasattr(self.agi, 'get_state_report'):
            self.core_status_text.config(state='normal'); self.core_status_text.delete('1.0', tk.END)
            report = self.agi.get_state_report()
            for k, v_val in report.items(): self.core_status_text.insert(tk.END, f"{k}: {v_val}\n")
            self.core_status_text.config(state='disabled')
    def start_auto_refresh(self): self.update_dashboard(); self.after(1000, self.start_auto_refresh)
    def undo(self):
        if self.agi.fractal_state.undo(): self.update_dashboard(); messagebox.showinfo("Undo", "State reverted.")
    def redo(self):
        if self.agi.fractal_state.redo(): self.update_dashboard(); messagebox.showinfo("Redo", "State re-applied.")
    def save_snap(self):
        name = simpledialog.askstring("Snapshot Name", "Enter name for snapshot:")
        if name: self.agi.save_snapshot(name); messagebox.showinfo("Snapshot", f"Snapshot '{name}' saved."); self.update_dashboard()
    def rollback_snap(self):
        name = simpledialog.askstring("Rollback To", "Enter snapshot name:")
        if name:
            if self.agi.rollback_snapshot(name): messagebox.showinfo("Rollback", f"Rolled back to '{name}'."); self.update_dashboard()
            else: messagebox.showerror("Rollback", f"Snapshot '{name}' not found.")
    def export_state(self):
        path = filedialog.asksaveasfilename(defaultextension=".pkl", title="Export Fractal State")
        if path: self.agi.fractal_state.fractal_export(path); messagebox.showinfo("Export", "State exported.")
    def import_state(self):
        path = filedialog.askopenfilename(title="Import Fractal State")
        if path: self.agi.fractal_state.fractal_import(path); messagebox.showinfo("Import", "State imported."); self.update_dashboard()
    def switch_timeline_event(self, event):
        idx = self.timeline_selector.get() # No int conversion needed if keys are strings
        if self.agi.fractal_state.switch_timeline(idx): messagebox.showinfo("Timeline Switch", f"Switched to timeline {idx}."); self.update_dashboard()
        else: messagebox.showerror("Timeline Switch", f"Failed to switch to {idx}.")
    def fork_timeline(self):
        name = simpledialog.askstring("Fork Timeline", "Name for new branch?")
        if name: new_idx = self.agi.fractal_state.fork_timeline(name); messagebox.showinfo("Timeline Fork", f"New timeline: {new_idx}."); self.update_dashboard()
    def add_module(self):
        name = simpledialog.askstring("Add Module", "Module Name:");
        if not name: return
        code = simpledialog.askstring("Add Module", "Python Code:", initialvalue="# Code here\npass")
        if code is None: return
        doc = simpledialog.askstring("Add Module", "Docs:", initialvalue=""); doc = doc if doc is not None else ""
        autorun = messagebox.askyesno("Autorun", "Run module after adding?")
        try: self.agi.add_module(name, code, doc, autorun=autorun); messagebox.showinfo("Module Added", f"Module '{name}' added.")
        except ValueError as ve: messagebox.showerror("Add Module Error", str(ve))
        except Exception as e_val: messagebox.showerror("Add Module Error", f"Error: {e_val}\n{traceback.format_exc()}")
        self.update_dashboard()
    def on_module_select(self, event):
        idx = self.mod_list.curselection()
        if idx:
            name = self.mod_list.get(idx[0]); self.wire_canvas.select_module(name)
            mod = self.agi.fractal_state.state["modules"].get(name)
            if mod:
                self.ai_output.config(state='normal'); self.ai_output.delete('1.0', tk.END)
                self.ai_output.insert(tk.END, f"--- Module: {mod.name} ---\nDoc: {mod.doc or 'N/A'}\n")
                last_run = time.ctime(mod.last_eval_time) if mod.last_eval_time else "NEVER"
                self.ai_output.insert(tk.END, f"Last Run: {last_run}\nError: {mod.last_eval_error or 'None'}\nOutput: {mod.last_eval_output or 'None'}\n--- Code ---\n{mod.code}")
                self.ai_output.config(state='disabled'); self.ai_output.see(tk.END)
    def edit_module(self):
        idx = self.mod_list.curselection();
        if not idx: messagebox.showwarning("Edit Module", "Select module."); return
        name = self.mod_list.get(idx[0]); mod = self.agi.fractal_state.state["modules"][name]
        new_code = simpledialog.askstring("Edit Code", f"Code for '{name}':", initialvalue=mod.code)
        if new_code is not None:
            mod.code = new_code
            new_doc = simpledialog.askstring("Edit Docs", f"Docs for '{name}':", initialvalue=mod.doc)
            if new_doc is not None: mod.doc = new_doc
            self.agi.fractal_state.save_state(f"Edited module {name}"); messagebox.showinfo("Module Edited", f"'{name}' updated."); self.update_dashboard()
    def run_module(self):
        idx = self.mod_list.curselection()
        if not idx: messagebox.showwarning("Run Module", "Select module."); return
        name = self.mod_list.get(idx[0]); self.agi.run_module(name); mod = self.agi.fractal_state.state["modules"][name]
        if mod.last_eval_error:
            patch_sugg = self.agi.nlp.suggest_patch(mod.code, mod.last_eval_error)
            messagebox.showerror("Module Error", f"'{name}' failed:\n{mod.last_eval_error}\nSuggestion:\n{patch_sugg}")
        else: messagebox.showinfo("Module Ran", f"'{name}' executed.\nOutput:\n{mod.last_eval_output[:500]}...")
        self.update_dashboard()
    def del_module(self):
        idx = self.mod_list.curselection()
        if not idx: messagebox.showwarning("Delete Module", "Select module."); return
        name = self.mod_list.get(idx[0])
        if messagebox.askyesno("Confirm Delete", f"Delete '{name}'?"):
            del self.agi.fractal_state.state["modules"][name]; self.agi.fractal_state.save_state(f"Deleted {name}")
            messagebox.showinfo("Module Deleted", f"'{name}' deleted."); self.update_dashboard()
    def add_variable(self):
        vname = simpledialog.askstring("Add Variable", "Name:")
        if not vname: return
        val_str = simpledialog.askstring("Add Variable", f"Value for '{vname}' (eval'd):")
        if val_str is None: return
        try: val = eval(val_str); self.agi.fractal_state.state["vars"][vname] = val; self.agi.fractal_state.save_state(f"Added Var-{vname}")
        except Exception as e_val: messagebox.showerror("Add Var Error", f"Invalid value: {e_val}"); return
        messagebox.showinfo("Variable Added", f"Var '{vname}' = '{val}'."); self.update_dashboard()
    def edit_variable(self):
        idx = self.var_list.curselection()
        if not idx: messagebox.showwarning("Edit Variable", "Select var."); return
        vname = self.var_list.get(idx[0]).split(":")[0].strip(); current_val = self.agi.fractal_state.state["vars"][vname]
        new_val_str = simpledialog.askstring("Edit Var", f"New value for '{vname}' (curr: {current_val}, eval'd):", initialvalue=str(current_val))
        if new_val_str is not None:
            try: new_val = eval(new_val_str); self.agi.fractal_state.state["vars"][vname] = new_val; self.agi.fractal_state.save_state(f"Edited Var-{vname}")
            except Exception as e_val: messagebox.showerror("Edit Var Error", f"Invalid value: {e_val}"); return
            messagebox.showinfo("Variable Edited", f"Var '{vname}' = '{new_val}'."); self.update_dashboard()
    def ask_ai(self):
        prompt = self.ai_input.get().strip();
        if not prompt: return
        self.ai_output.config(state='normal'); self.ai_output.insert(tk.END, f"\n--- User: {prompt} ---\n", 'user_prompt'); self.ai_input.delete(0, tk.END)
        if prompt.lower().startswith("/code"):
            sugg = self.agi.nlp.autocomplete_code(prompt[5:].strip(), context=str(self.agi.fractal_state.state['vars']))
            self.ai_output.insert(tk.END, f"\n[AI CODE SUGGESTION]:\n{sugg}\n", 'ai_response')
        else:
            try:
                if "reason" in prompt.lower() or "solve" in prompt.lower():
                    facts = [f"{k}:{v}" for k,v in self.agi.fractal_state.state['vars'].items()]
                    res = self.agi.reasoner.reason(facts=facts,query=prompt,verbose=False)
                    out_text = f"Reasoner Decision: {res['decision']}\nMeta: {json.dumps(res['meta'],indent=2)}\nSummaries: {[s[0] for s in res['summaries']]}\n"
                    self.ai_output.insert(tk.END, f"\n[AI REASONING]:\n{out_text}\n", 'ai_response')
                else:
                    nlp_out = self.agi.nlp.parse(prompt,cot=True)
                    out_text = f"Sentiment: {nlp_out['sentiment']}\nIntent: {nlp_out['intent']}\nKeywords: {', '.join(nlp_out['keywords'])}\nEntities: {', '.join(nlp_out['entities'])}\nSummary: {nlp_out['summary']}\n"
                    if 'cot_trace' in nlp_out: out_text += f"\n[COT]:\n" + "\n".join(nlp_out['cot_trace']) + "\n"
                    self.ai_output.insert(tk.END, f"\n[AI NLP PARSE]:\n{out_text}\n", 'ai_response')
            except Exception as e_val: self.ai_output.insert(tk.END, f"\n[AI ERROR]: {e_val}\n{traceback.format_exc()}\n", 'ai_error')
        self.ai_output.config(state='disabled'); self.ai_output.see(tk.END)
    def zero_shot_ui(self):
        problem = simpledialog.askstring("ZeroShot", "Problem/directive:")
        if problem:
            verdict = self.agi.triad.run(problem,self.agi.triad.default_teacher,self.agi.triad.default_student,self.agi.triad.default_verifier)
            self.ai_output.config(state='normal'); self.ai_output.insert(tk.END, f"\n--- ZeroShot ---\nProblem: {problem}\nVerdict: {verdict}\n", 'ai_response')
            self.ai_output.config(state='disabled'); self.ai_output.see(tk.END); self.update_dashboard()
    def trigger_evolution(self):
        if messagebox.askyesno("Evolve", "Trigger self-evolution?"):
            self.agi.evolution_loop.run(force_mutate_code=True)
            messagebox.showinfo("Evolution", "Evolution cycle initiated."); self.update_dashboard()
    def perform_introspection(self):
        reflection, status = self.agi.awareness_loop.run()
        self.ai_output.config(state='normal'); self.ai_output.insert(tk.END, f"\n--- Introspection ---\n{reflection}\nStatus: {json.dumps(status,indent=2)}\n", 'ai_response')
        self.ai_output.config(state='disabled'); self.ai_output.see(tk.END); self.update_dashboard()
    def enforce_bloodline(self):
        try: self.agi.bloodline_law.enforce(self.agi.fractal_state.state); messagebox.showinfo("Bloodline Law", "PASS.")
        except Exception as e_val: messagebox.showerror("Bloodline Law Violation", f"{e_val}\nEmergency procedures initiated."); self.agi.handle_critical_error(f"Bloodline violation: {e_val}")
        self.update_dashboard()
    def diagnostics(self):
        diag = self.agi.diagnostics.generate_report()
        self.ai_output.config(state='normal'); self.ai_output.insert(tk.END, f"\n--- Diagnostics ---\n{diag}", 'ai_response')
        self.ai_output.config(state='disabled'); self.ai_output.see(tk.END)
    def safe_quit(self):
        if messagebox.askokcancel("Quit", "Save backups & terminate?"): self.agi.save_state_full(); self.destroy()
    def status_bar(self, msg):
        print(f"[UI STATUS] {msg}")
        if hasattr(self, 'core_status_text') and self.core_status_text:
            try:
                self.core_status_text.config(state='normal'); self.core_status_text.delete('1.0', '2.0'); self.core_status_text.insert('1.0', f"{msg}\n"); self.core_status_text.config(state='disabled')
            except tk.TclError: pass
    def _graph_tick(self):
        if not self._graph_loop_running: return
        try:
            if hasattr(self.agi, 'run_main_loop_step'): self.agi.run_main_loop_step("GUI Graph Tick")
            else: self._graph_loop_running = False; self.status_bar("ERROR: AGI loop missing. Graph stopped."); return
        except Exception as e_val: self.status_bar(f"ERROR in graph tick: {e_val}. Graph stopped."); self._graph_loop_running = False; return
        finally:
            if self._graph_loop_running: self._graph_loop_id = self.after(500, self._graph_tick)
    def _start_graph_loop(self):
        if self._graph_loop_running: self.status_bar("Graph RUNNING."); return
        self._graph_loop_running = True; self._graph_tick(); self.status_bar("Graph RUNNING...")
    def _pause_graph_loop(self):
        if not self._graph_loop_running: return
        self._graph_loop_running = False
        if self._graph_loop_id: self.after_cancel(self._graph_loop_id); self._graph_loop_id = None
        self.status_bar("Graph PAUSED.")
    def _stop_graph_loop(self): self._pause_graph_loop(); self.status_bar("Graph STOPPED.")

# Placeholder for WireGraphCanvas if not defined elsewhere
class WireGraphCanvas(tk.Canvas):
    def __init__(self, master, fractal_state_ref, **kwargs):
        super().__init__(master, **kwargs)
        self.fractal_state = fractal_state_ref
        self.selected_module = None
        # Basic drawing to indicate it's working
        self.create_text(10, 10, anchor=tk.NW, text="WireGraphCanvas Placeholder", fill="white")
    def redraw(self): pass # Placeholder
    def select_module(self, module_name): self.selected_module = module_name; self.redraw()


def global_exception_hook(exc_type, exc_value, exc_traceback):
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"GLOBAL EXCEPTION CAUGHT:\n{error_msg}")
    if agi_instance_global_ref:
        try:
            victor_log("CRITICAL", f"Global unhandled exception: {error_msg}", component_name="EXCEPTION_HANDLER")
            # agi_instance_global_ref.fractal_state.save_state("CRITICAL_ERROR_STATE_DUMP") # Save state before potential crash
            # agi_instance_global_ref.awareness_loop.log_event("CRITICAL_ERROR", {"type": str(exc_type), "message": str(exc_value), "trace": error_msg})
        except Exception as e_log:
            print(f"Further error during global exception handling: {e_log}")
    sys.__excepthook__(exc_type, exc_value, exc_traceback) # Call default hook

sys.excepthook = global_exception_hook
agi_instance_global_ref = None # Will hold the AGI instance

def main_gui():
    """Main GUI entry point with comprehensive error handling."""
    global agi_instance_global_ref
    
    try:
        # Check for OpenAI API key
        if openai and "OPENAI_API_KEY" not in os.environ:
            root = tk.Tk()
            root.withdraw()
            result = messagebox.askyesno(
                "OpenAI Key Not Found",
                "OpenAI API key is not set. Some features will be limited.\n\n"
                "Do you want to continue anyway?\n\n"
                "To set it later, use:\nexport OPENAI_API_KEY='your-key'"
            )
            root.destroy()
            if not result:
                print("Exiting: OpenAI API key required for full functionality.")
                return 1
        elif openai and "OPENAI_API_KEY" in os.environ:
            openai.api_key = os.environ["OPENAI_API_KEY"]

        print("Initializing VictorASIOmniBrainGodcore...")
        agi_core = VictorASIOmniBrainGodcore(voice=False)
        agi_instance_global_ref = agi_core

        print("Initializing InfiniteDevUI...")
        app = InfiniteDevUI(agi_core)
        app.mainloop()
        print("InfiniteDevUI closed successfully.")
        return 0
        
    except Exception as e:
        error_msg = f"Fatal error in main_gui: {e}\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Fatal Error",
                f"An error occurred:\n\n{str(e)}\n\nCheck console for details."
            )
            root.destroy()
        except:
            pass
        return 1

if __name__ == "__main__":
    sys.exit(main_gui())
