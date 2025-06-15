# =============================================================
# 7. TKINTER GUI - VICTOR COMMAND CENTER (Simplified for brevity in this context)
# =============================================================
class VictorCommandCenter(tk.Tk): # Definition as provided in prompt
    def __init__(self, agi_instance_provider): # Takes a function that returns AGI instance
        super().__init__()
        self.agi_instance_provider = agi_instance_provider
        self.agi = None # Will be set by _initialize_agi

        self.title(f"Victor AGI Command Center (Initializing...)")
        self.geometry("1200x800")
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self._setup_styles()
        self._create_widgets() # Create widgets first

        # Defer AGI initialization until GUI is minimally ready
        self.after(100, self._initialize_agi_and_layout)


    def _initialize_agi_and_layout(self):
        try:
            self.agi = self.agi_instance_provider() # Now create/get the AGI instance
            self.agi.gui_bridge.set_gui_app(self) # Link AGI's bridge to this GUI
            self.agi.has_gui = True # Mark this AGI instance as having a GUI
            self.title(f"Victor AGI Command Center v{self.agi.config['version']}") # Update title
        except Exception as e:
            messagebox.showerror("AGI Initialization Error", f"Failed to initialize Victor AGI: {e}\n{traceback.format_exc()}")
            self.log_message("CRITICAL", f"AGI INIT FAILED: {e}")
            self.destroy() # Close GUI if AGI fails
            return

        self._layout_widgets() # Now layout widgets that might depend on AGI config or bridge
        self.log_message("INFO", "Victor Command Center GUI Initialized & AGI Linked.")
        self.agi.gui_bridge.update_status_indicator("Idle", "green")


    def _setup_styles(self): # Same as provided
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure("TNotebook.Tab", padding=[10, 5], font=('Segoe UI', 10, 'bold'))
        self.style.configure("TLabel", font=('Segoe UI', 10))
        self.style.configure("Header.TLabel", font=('Segoe UI', 12, 'bold'))
        self.style.configure("Status.TLabel", font=('Segoe UI', 10, 'italic'))
        self.style.configure("TButton", font=('Segoe UI', 10), padding=5)
        self.style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))
        self.style.configure("Accent.TButton", foreground="white", background="#0078D4", font=('Segoe UI', 10, 'bold'))
        self.style.configure("CategoryHeader.TButton", font=('Segoe UI', 10, 'bold'))


    def _create_widgets(self):
        self.main_paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.left_pane = ttk.Frame(self.main_paned_window, padding=10)
        self.main_paned_window.add(self.left_pane, weight=1) # Adjust weight as needed
        self.right_pane = ttk.Frame(self.main_paned_window)
        self.main_paned_window.add(self.right_pane, weight=3) # Adjust weight

        # Left Pane Widgets (Old structure commented out)
        # self.input_frame = ttk.LabelFrame(self.left_pane, text="Command Input", padding=10)
        # self.input_label = ttk.Label(self.input_frame, text="Enter command or query for Victor:")
        # self.input_text = scrolledtext.ScrolledText(self.input_frame, height=5, width=35, font=('Segoe UI', 10), relief=tk.SOLID, borderwidth=1) # Adjusted width
        # self.send_button = ttk.Button(self.input_frame, text="Send to Victor", command=self._send_input_to_agi, style="Accent.TButton")

        # self.control_frame = ttk.LabelFrame(self.left_pane, text="AGI Control", padding=10)
        # self.status_button = ttk.Button(self.control_frame, text="AGI Status", command=self._get_agi_status)
        # self.override_button = ttk.Button(self.control_frame, text="Ethics Override", command=self._ethics_override_dialog)
        # self.save_state_button = ttk.Button(self.control_frame, text="Save Fractal State", command=self._save_fractal_state)
        # self.load_state_button = ttk.Button(self.control_frame, text="Load Fractal State", command=self._load_fractal_state)
        # self.shutdown_button = ttk.Button(self.control_frame, text="Shutdown AGI", command=self._confirm_shutdown)

        # self.status_frame = ttk.LabelFrame(self.left_pane, text="AGI Status", padding=10)
        # self.status_light_label = ttk.Label(self.status_frame, text="Current Status:", style="Header.TLabel")
        # self.status_light_canvas = tk.Canvas(self.status_frame, width=20, height=20, bg="grey", relief=tk.SUNKEN, borderwidth=1)
        # self.status_light_text = ttk.Label(self.status_frame, text="Initializing...", style="Status.TLabel")
        # self.current_task_label = ttk.Label(self.status_frame, text="Task: None", wraplength=280)
        # self.dominant_emotion_label = ttk.Label(self.status_frame, text="Emotion: Neutral")
        # self.current_timeline_label = ttk.Label(self.status_frame, text="Timeline: genesis (0)")

        # New Sidebar Structure
        self.sidebar_main_frame = ttk.Frame(self.left_pane, padding=5)

        # Populate Sidebar with Categories and Items
        categories = {
            "VICTOR CORE": ["New Chat", "Search Chats"],
            "LIBRARY": ["Project Library", "Custom Experts"],
            "OPERATIONS": ["Swarm Mode"],
            "DEVELOPER": ["Developer Options", "Loaded Packages Inspector"],
            "TOOLS & PARAMETERS": ["Core System", "Model Parameters", "Memory Parameters", "UI Skin/Theme"],
            "STATE & MODELS": ["Save Model", "Load Model", "Snapshot State", "Rollback to Snapshot"],
            "SETTINGS": ["Preferences", "System Settings"]
        }

        for category_title, items in categories.items():
            items_config = []
            for item_name in items:
                # Placeholder command using a default argument to capture item_name correctly in lambda
                command = lambda name=item_name: self.log_message("INFO", f"'{name}' clicked")
                items_config.append((item_name, command))
            self._create_collapsible_section(self.sidebar_main_frame, category_title, items_config)

        # Right Pane Notebook (Tabs)
        self.notebook = ttk.Notebook(self.right_pane)
        tab_names = ["System Log", "Victor's Output", "Task Manager", "Cognitive Cycle / Plans", "Emotional Core", "Knowledge Graph", "Memory System", "Fractal Timelines"]
        self.tabs = {}
        for tab_name in tab_names:
            tab_frame = ttk.Frame(self.notebook, padding=5)
            self.notebook.add(tab_frame, text=tab_name)
            self.tabs[tab_name] = tab_frame
            if tab_name in ["System Log", "Victor's Output", "Cognitive Cycle / Plans", "Knowledge Graph", "Memory System"]:
                text_area = scrolledtext.ScrolledText(tab_frame, width=80, height=20, state=tk.DISABLED, relief=tk.SOLID, borderwidth=1, font=("Courier New", 9) if "Plan" in tab_name else ('Segoe UI', 10))
                text_area.pack(expand=True, fill=tk.BOTH)
                setattr(self, f"{tab_name.lower().replace(' / ', '_').replace(' ', '_')}_text", text_area)

        # Specific setup for Task Manager Tab
        tm_tab = self.tabs["Task Manager"]
        self.task_pending_frame = ttk.LabelFrame(tm_tab, text="Pending/Active Tasks", padding=5)
        self.task_pending_tree = ttk.Treeview(self.task_pending_frame, columns=("id", "desc", "prio", "status", "progress"), show="headings", height=8)
        self._setup_task_treeview(self.task_pending_tree, completed=False)
        self.task_pending_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        self.task_completed_frame = ttk.LabelFrame(tm_tab, text="Recently Completed Tasks", padding=5)
        self.task_completed_tree = ttk.Treeview(self.task_completed_frame, columns=("id", "desc", "status"), show="headings", height=5)
        self._setup_task_treeview(self.task_completed_tree, completed=True)
        self.task_completed_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        # Specific setup for Emotions Tab
        self.emotions_canvas = tk.Canvas(self.tabs["Emotional Core"], width=700, height=400, bg="white", relief=tk.GROOVE, borderwidth=1)
        self.emotions_canvas.pack(expand=True, fill=tk.BOTH)

        # Specific setup for Fractal Timelines Tab
        ft_tab = self.tabs["Fractal Timelines"]
        self.timeline_tree = ttk.Treeview(ft_tab, columns=("name", "length", "maxlen", "last_desc"), show="headings", height=10)
        self.timeline_tree.heading("name", text="Name"); self.timeline_tree.column("name", width=150)
        self.timeline_tree.heading("length", text="History"); self.timeline_tree.column("length", width=70, anchor=tk.CENTER)
        self.timeline_tree.heading("maxlen", text="Max Len"); self.timeline_tree.column("maxlen", width=70, anchor=tk.CENTER)
        self.timeline_tree.heading("last_desc", text="Last State Desc"); self.timeline_tree.column("last_desc", width=300)
        self.timeline_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ft_button_frame = ttk.Frame(ft_tab, padding=5)
        ttk.Button(ft_button_frame, text="Switch To Selected", command=self._switch_timeline).pack(fill=tk.X, pady=2)
        ttk.Button(ft_button_frame, text="Fork Current", command=self._fork_timeline).pack(fill=tk.X, pady=2)
        ttk.Button(ft_button_frame, text="Replay Selected", command=self._replay_timeline_dialog).pack(fill=tk.X, pady=2)
        ttk.Button(ft_button_frame, text="Refresh List", command=self.update_fractal_timelines_display).pack(fill=tk.X, pady=2)
        ft_button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)

    def _create_collapsible_section(self, parent_frame, category_title, items_config):
        # Frame for the category header (button)
        header_frame = ttk.Frame(parent_frame)
        header_frame.pack(fill=tk.X, pady=(5, 0))

        # Frame for the items, initially hidden
        items_frame = ttk.Frame(parent_frame, padding=(10, 5, 0, 5)) # Add some padding for items

        # Toggle function for section visibility
        def toggle_section(items_frame_widget=items_frame): # Default arg to capture items_frame
            if items_frame_widget.winfo_ismapped():
                items_frame_widget.pack_forget()
            else:
                items_frame_widget.pack(fill=tk.X, expand=True)

        # Category header button
        header_button = ttk.Button(header_frame, text=category_title,
                                   command=toggle_section, style="CategoryHeader.TButton")
        header_button.pack(fill=tk.X)

        # Create item buttons within the items_frame
        for item_name, item_command in items_config:
            item_button = ttk.Button(items_frame, text=item_name, command=item_command)
            item_button.pack(fill=tk.X, pady=1)

        # By default, sections start collapsed (items_frame is not packed)

    def _layout_widgets(self): # Simplified, assumes widgets created
        self.main_paned_window.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # Left Pane (Old layout commented out)
        # self.input_frame.pack(pady=5, padx=5, fill=tk.X)
        # self.input_label.pack(anchor=tk.W)
        # self.input_text.pack(pady=(0,5), fill=tk.X, expand=True)
        # self.send_button.pack(pady=(0,5))

        # self.control_frame.pack(pady=5, padx=5, fill=tk.X)
        # self.status_button.grid(row=0, column=0, padx=2, pady=2, sticky=tk.EW)
        # self.override_button.grid(row=0, column=1, padx=2, pady=2, sticky=tk.EW)
        # self.save_state_button.grid(row=1, column=0, padx=2, pady=2, sticky=tk.EW)
        # self.load_state_button.grid(row=1, column=1, padx=2, pady=2, sticky=tk.EW)
        # self.shutdown_button.grid(row=2, column=0, columnspan=2, padx=2, pady=2, sticky=tk.EW)
        # self.control_frame.columnconfigure((0,1), weight=1)

        # self.status_frame.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
        # self.status_light_label.grid(row=0, column=0, sticky=tk.W, pady=2)
        # self.status_light_canvas.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        # self.status_light_text.grid(row=0, column=2, sticky=tk.W, padx=5, pady=2, columnspan=2)
        # self.current_task_label.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=2)
        # self.dominant_emotion_label.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=2)
        # self.current_timeline_label.grid(row=3, column=0, columnspan=4, sticky=tk.W, pady=2)
        # self.status_frame.columnconfigure(2, weight=1)

        # New Sidebar Layout
        self.sidebar_main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Right Pane
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

    def _setup_task_treeview(self, tree, completed=False): # Same as provided
        tree.heading("id", text="ID"); tree.column("id", width=150, anchor=tk.W, stretch=False)
        tree.heading("desc", text="Description"); tree.column("desc", width=250, anchor=tk.W) # Stretch True by default
        tree.heading("status", text="Status"); tree.column("status", width=100, anchor=tk.W, stretch=False)
        if not completed:
            tree.heading("prio", text="Prio"); tree.column("prio", width=40, anchor=tk.CENTER, stretch=False)
            tree.heading("progress", text="Progress"); tree.column("progress", width=100, anchor=tk.W, stretch=False)

        scrollbar = ttk.Scrollbar(tree.master, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) # Tree first
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y) # Then scrollbar

    # --- GUI Update Methods (called by AGI via Bridge) ---
    def log_message(self, level, message):
        log_area = self.system_log_text
        log_area.configure(state=tk.NORMAL)
        log_area.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] [{level}] {message}\n")
        log_area.configure(state=tk.DISABLED)
        log_area.see(tk.END)

    def show_agi_output(self, text_output):
        out_area = self.victor_s_output_text
        out_area.configure(state=tk.NORMAL)
        out_area.insert(tk.END, f"{text_output}\n\n")
        out_area.configure(state=tk.DISABLED)
        out_area.see(tk.END)
        self.notebook.select(self.tabs["Victor's Output"])

    def update_status_light(self, status_text, color):
        # Ensure self.status_light_canvas is available
        if hasattr(self, 'status_light_canvas'): # This check is important as old widgets are commented
            self.status_light_canvas.configure(bg=color)
        # Ensure self.status_light_text is available
        if hasattr(self, 'status_light_text'): # This check is important
            self.status_light_text.configure(text=status_text)


    def update_current_task(self, task_id, description, status):
        display_text = f"Task: {task_id} - {description[:30]}... ({status})" if task_id else "Task: None"
        # Ensure self.current_task_label is available if not commented out
        if hasattr(self, 'current_task_label'): # This check is important
            self.current_task_label.configure(text=display_text)
        # Ensure self.current_timeline_label is available
        if hasattr(self, 'current_timeline_label') and self.agi and self.agi.fractal_state_engine: # This check is important
            fse = self.agi.fractal_state_engine
            self.current_timeline_label.configure(text=f"Timeline: {fse.current_timeline} ({len(fse.history)})")


    def refresh_task_lists(self, pending_tasks, completed_tasks):
        for i in self.task_pending_tree.get_children(): self.task_pending_tree.delete(i)
        for task in pending_tasks:
            progress_bar = self._create_progress_bar_text(task.get("progress", 0))
            self.task_pending_tree.insert("", tk.END, iid=task["id"], values=(task["id"], task["desc"], task["prio"], task["status"], progress_bar))

        for i in self.task_completed_tree.get_children(): self.task_completed_tree.delete(i)
        for task in completed_tasks:
            self.task_completed_tree.insert("", tk.END, iid=task["id"], values=(task["id"], task["desc"], task["status"]))

    def update_task_in_list(self, task_id, description, status, progress_percent):
        if self.task_pending_tree.exists(task_id):
            progress_bar = self._create_progress_bar_text(progress_percent)
            item = self.task_pending_tree.item(task_id) # Get current item
            prio = item['values'][2] if item and len(item['values']) > 2 else 'N/A' # Preserve priority
            self.task_pending_tree.item(task_id, values=(task_id, description, prio, status, progress_bar))

    def _create_progress_bar_text(self, percentage, length=10):
        filled_length = int(length * percentage)
        bar = '█' * filled_length + '░' * (length - filled_length) # Use different char for empty part
        return f"[{bar}] {percentage*100:.0f}%"

    def display_plan_details(self, plan_data, adhoc=False):
        plan_area = self.cognitive_cycle_plans_text
        plan_area.configure(state=tk.NORMAL)
        type_str = "Ad-Hoc Plan" if adhoc else f"Plan for Task {plan_data.get('task_id', 'N/A')}"
        header = f"--- {type_str}: {plan_data.get('name', 'Unnamed Plan')} (ID: {plan_data.get('id')}) ---\n"
        details = f"Goal: {plan_data.get('goal', 'N/A')}\nComplexity: {plan_data.get('estimated_complexity',0):.2f}, Confidence: {plan_data.get('confidence',0):.2f}\nStatus: {plan_data.get('status', 'N/A')}\n"
        steps_info = "Steps:\n"
        for i, step in enumerate(plan_data.get("steps", [])):
            steps_info += f"  {i+1}. (ID: {step.get('id')}) {step.get('action_type', 'Unknown Action')}\n"
            # ... (rest of step details formatting)
            steps_info += f"     Status: PENDING\n"
        plan_area.insert(tk.END, header + details + steps_info + "---\n\n")
        plan_area.configure(state=tk.DISABLED); plan_area.see(tk.END)
        self.notebook.select(self.tabs["Cognitive Cycle / Plans"])
        if not hasattr(self, 'gui_plan_store'): self.gui_plan_store = {}
        self.gui_plan_store[plan_data['id']] = plan_data

    def update_plan_gui_status(self, plan_id, status, final_result=None):
        plan_area = self.cognitive_cycle_plans_text
        plan_area.configure(state=tk.NORMAL)
        plan_area.insert(tk.END, f"\nUPDATE for Plan ID {plan_id}: Status -> {status}\n")
        if final_result: plan_area.insert(tk.END, f"  Final Result: {str(final_result)[:200]}\n") # Limit result length
        plan_area.configure(state=tk.DISABLED); plan_area.see(tk.END)

    def update_step_gui_status(self, plan_id, step_id, status, result=None):
        plan_area = self.cognitive_cycle_plans_text
        plan_area.configure(state=tk.NORMAL)
        update_msg = f"  UPDATE for Plan {plan_id}, Step {step_id}: Status -> {status}"
        if result: update_msg += f", Result: {str(result)[:100]}"
        plan_area.insert(tk.END, update_msg + "\n")
        plan_area.configure(state=tk.DISABLED); plan_area.see(tk.END)

    def update_emotions_display(self, emotions_dict, dominant_emotion): # Same as provided
        # Ensure self.dominant_emotion_label is available
        if hasattr(self, 'dominant_emotion_label'): # This check is important
            self.dominant_emotion_label.configure(text=f"Emotion: {dominant_emotion.capitalize()}")
        canvas = self.emotions_canvas; canvas.delete("all")
        if not emotions_dict: return
        bar_width=30; spacing=8; max_h=canvas.winfo_height()-50; x_off=30; y_off=canvas.winfo_height()-30
        sorted_emotions = sorted([item for item in emotions_dict.items() if item[1] > 0.01], key=lambda x: x[1], reverse=True) # Filter out negligible
        for i, (emo, val) in enumerate(sorted_emotions[:15]): # Show top 15
            h=val*max_h; x1=x_off+i*(bar_width+spacing); y1=y_off-h; x2=x1+bar_width; y2=y_off
            color="blue"; # Basic colors
            if emo in ["joy","serenity","trust","loyalty_bloodline"]: color="green"
            elif emo in ["anger","fear","frustration","disgust"]: color="red"
            elif emo in ["sadness"]: color="grey"
            elif emo in ["surprise","anticipation","awe","interest","vigilance"]: color="purple"
            canvas.create_rectangle(x1,y1,x2,y2,fill=color,outline="black",tags=emo)
            canvas.create_text(x1+bar_width/2,y_off+5,text=emo[:8],anchor=tk.N,font=("Segoe UI",7))
            canvas.create_text(x1+bar_width/2,y1-7,text=f"{val:.2f}",anchor=tk.S,font=("Segoe UI",7))
        canvas.create_text(canvas.winfo_width()/2,15,text=f"Emotional State (Dominant: {dominant_emotion.capitalize()})",font=("Segoe UI",11,"bold"))

    def update_kg_view(self, kg_summary):
        kg_area = self.knowledge_graph_text
        kg_area.configure(state=tk.NORMAL); kg_area.delete('1.0', tk.END)
        kg_area.insert(tk.END, "--- Knowledge Graph Summary ---\n")
        for k,v in kg_summary.items():
            if isinstance(v, list): # For top_relations
                kg_area.insert(tk.END, f"{k.replace('_',' ').title()}:\n")
                for item in v: kg_area.insert(tk.END, f"  - {item[0]}: Count={item[1]['count']}, Avg.Weight={item[1]['avg_weight']:.2f}\n")
            else: kg_area.insert(tk.END, f"{k.replace('_',' ').title()}: {v}\n")
        kg_area.configure(state=tk.DISABLED)

    def update_memory_view(self, memory_summary):
        mem_area = self.memory_system_text
        mem_area.configure(state=tk.NORMAL); mem_area.delete('1.0', tk.END)
        mem_area.insert(tk.END, "--- Memory System Summary ---\n")
        for k,v in memory_summary.items():
            if isinstance(v, list) and k == "working_mem_tasks":
                 mem_area.insert(tk.END, f"Working Memory (Active Tasks: {len(v)}):\n")
                 for task_id in v: mem_area.insert(tk.END, f"  - Task: {task_id}\n")
            else: mem_area.insert(tk.END, f"{k.replace('_',' ').title()}: {v}\n")
        mem_area.configure(state=tk.DISABLED)

    def update_fractal_timelines_display(self):
        if not self.agi or not self.agi.fractal_state_engine: return
        fse = self.agi.fractal_state_engine
        timeline_data = fse.list_timelines() # Get list of dicts

        for i in self.timeline_tree.get_children(): self.timeline_tree.delete(i) # Clear existing
        for tl in timeline_data:
            self.timeline_tree.insert("", tk.END, iid=tl["name"], values=(tl["name"], tl["history_length"], tl["max_length"], tl["last_saved_desc"]))

        if hasattr(self, 'current_timeline_label'): # Check if it exists
             self.current_timeline_label.configure(text=f"Timeline: {fse.current_timeline} ({len(fse.history)})")
        self.log_message("INFO", "Fractal Timelines display refreshed.")


    # --- GUI Action Handlers ---
    def _send_input_to_agi(self): # Same as provided
        # Ensure self.input_text is available if not commented out
        if hasattr(self, 'input_text'): # This check is important
            user_text = self.input_text.get("1.0", tk.END).strip()
            if user_text:
                self.log_message("CMD", f"User Input: {user_text}")
                self.input_text.delete("1.0", tk.END)
                source_name = BloodlineRootLaw.BLOODLINE.split('&')[0]
                if self.agi: self.agi.process_text_input(user_text, source=f"{source_name}_gui_direct")
            else: messagebox.showwarning("Empty Input", "Please enter a command or query for Victor.")
        else:
            self.log_message("WARNING", "Input text widget not available for sending input.")


    def _confirm_shutdown(self): # Same as provided
        if messagebox.askyesno("Confirm Shutdown", "Are you sure you want to shut down Victor AGI?"):
            self.log_message("CMD", "Shutdown initiated by user.")
            if self.agi: self.agi.shutdown(initiated_by="gui_user_command")

    def on_agi_shutdown(self): # Same as provided
        self.log_message("INFO", "AGI has confirmed shutdown. Closing Command Center.")
        self.after(1500, self.destroy)

    def _get_agi_status(self): # Modified to use the text area
        if not self.agi: self.log_message("ERROR", "AGI instance not available for status."); return
        status_report_str = self.agi.get_status_report(for_gui=False) # Get pretty string
        self.show_agi_output(status_report_str) # Display in Victor's output tab
        self.log_message("INFO", "AGI Status Report generated and displayed.")

    def _ethics_override_dialog(self): # Same as provided
        if not self.agi: return
        password = simpledialog.askstring("Ethics Override", "Enter Bloodline Override Password:", show='*')
        if password:
            if self.agi.ethics_processor.activate_override(password):
                messagebox.showinfo("Success", "Ethics Override ACTIVATED.")
                self.log_message("CRITICAL", "Ethics Override enabled via GUI by user.")
            else:
                messagebox.showerror("Failed", "Incorrect Password. Override denied.")
                self.log_message("WARNING", "Failed Ethics Override attempt via GUI.")
        elif VICTOR_CONFIG["creator_override_active"]:
            if messagebox.askyesno("Override Active", "Creator Override is currently active. Deactivate it?"):
                self.agi.ethics_processor.deactivate_override()
                messagebox.showinfo("Success", "Ethics Override DEACTIVATED.")
                self.log_message("INFO", "Ethics Override disabled via GUI by user.")

    def _save_fractal_state(self):
        if not self.agi or not self.agi.fractal_state_engine:
            messagebox.showerror("Error", "Fractal State Engine not available.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".vfs", filetypes=[("Victor Fractal State", "*.vfs"), ("All Files", "*.*")], title="Save Fractal State")
        if filepath:
            if self.agi.fractal_state_engine.export_state(filepath):
                messagebox.showinfo("Success", f"Fractal State saved to {filepath}")
                self.log_message("INFO", f"Fractal State exported to {filepath}")
            else:
                messagebox.showerror("Error", "Failed to save Fractal State.")

    def _load_fractal_state(self):
        if not self.agi or not self.agi.fractal_state_engine:
            messagebox.showerror("Error", "Fractal State Engine not available.")
            return
        filepath = filedialog.askopenfilename(defaultextension=".vfs", filetypes=[("Victor Fractal State", "*.vfs"), ("All Files", "*.*")], title="Load Fractal State")
        if filepath:
            if self.agi.fractal_state_engine.import_state(filepath):
                messagebox.showinfo("Success", f"Fractal State loaded from {filepath}")
                self.log_message("INFO", f"Fractal State imported from {filepath}")
                self.update_fractal_timelines_display() # Refresh display
                # Also refresh other relevant GUI parts based on loaded state
                self.update_emotions_display(self.agi.emotional_core.get_emotional_state(), self.agi.emotional_core.get_dominant_emotion())
                current_task = self.agi.task_manager.get_current_task()
                if current_task: self.update_current_task(current_task['id'], current_task['description'], current_task['status'])
                else: self.update_current_task(None, "None", "N/A")

            else:
                messagebox.showerror("Error", "Failed to load Fractal State.")

    def _switch_timeline(self):
        selected_items = self.timeline_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a timeline from the list to switch to.")
            return
        timeline_name = selected_items[0] # Treeview iid is the timeline name
        if self.agi.fractal_state_engine.switch_timeline(timeline_name):
            self.log_message("INFO", f"Successfully switched to timeline: {timeline_name}")
            self.update_fractal_timelines_display()
             # Refresh other GUI elements as state would have changed
            self.update_emotions_display(self.agi.emotional_core.get_emotional_state(), self.agi.emotional_core.get_dominant_emotion())
            current_task = self.agi.task_manager.get_current_task() # This might be None after state load
            if current_task: self.update_current_task(current_task['id'], current_task['description'], current_task['status'])
            else: self.update_current_task(None,"None","N/A")
        else:
            messagebox.showerror("Switch Failed", f"Failed to switch to timeline {timeline_name}.")

    def _fork_timeline(self):
        new_name = simpledialog.askstring("Fork Timeline", "Enter name for the new forked timeline:")
        if new_name:
            if self.agi.fractal_state_engine.fork_timeline(new_name):
                self.log_message("INFO", f"Current timeline forked to: {new_name}")
                self.update_fractal_timelines_display()
            else:
                messagebox.showerror("Fork Failed", f"Failed to fork timeline (name '{new_name}' might exist or source error).")

    def _replay_timeline_dialog(self):
        selected_items = self.timeline_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a timeline to replay.")
            return
        timeline_name = selected_items[0]

        depth_str = simpledialog.askstring("Replay Depth", "Enter replay depth percentage (e.g., 0.1 for 10%):", initialvalue="0.1")
        if not depth_str: return
        try: depth_percent = float(depth_str)
        except ValueError: messagebox.showerror("Invalid Input", "Depth must be a number."); return

        keywords_str = simpledialog.askstring("Filter Keywords", "Enter keywords to filter events (comma-separated, optional):")
        event_filter_keywords = [k.strip() for k in keywords_str.split(',')] if keywords_str else None

        replayed_data = self.agi.fractal_state_engine.fractal_memory_replay(timeline_name, depth_percent, event_filter_keywords)

        # Display replayed data (e.g., in Victor's Output tab or a new window)
        output_str = f"--- Replay of Timeline '{timeline_name}' (Depth: {depth_percent*100}%, Keywords: {event_filter_keywords}) ---\n"
        if not replayed_data:
            output_str += "No events matched the criteria or timeline empty.\n"
        else:
            for event in replayed_data:
                output_str += f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(event['timestamp']))}\n"
                output_str += f"  Desc: {event['description']}\n"
                output_str += f"  State Summary: {event['state_snapshot_summary']}\n---\n"
        self.show_agi_output(output_str)
        self.log_message("INFO", f"Fractal memory replay completed for timeline '{timeline_name}'.")


    def ask_confirmation_async(self, title, message, callback_on_yes, callback_on_no=None):
        """Shows a messagebox and calls callback based on user choice."""
        user_response = messagebox.askyesno(title, message)
        if user_response:
            if callback_on_yes: callback_on_yes()
        else:
            if callback_on_no: callback_on_no()


    def _on_closing(self): # Same as provided
        if self.agi and self.agi.system_status not in ["shutdown_complete", "shutting_down"]:
            if messagebox.askyesno("Confirm Exit", "Victor AGI is still running. Exiting might cause instability. Shut down AGI first?"):
                self._confirm_shutdown()
            else:
                self.log_message("WARNING", "GUI closed while AGI potentially running.")
                self.destroy()
        else:
            self.destroy()

# =============================================================
# 8. UTILITY IMPORTS (Already at top, this is just a section marker)
# =============================================================
