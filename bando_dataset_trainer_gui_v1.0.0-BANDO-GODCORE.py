import tkinter as tk
from tkinter import filedialog, messagebox, ttk # Ensure ttk is imported
import threading # For running trainer in a separate thread

class TrainerGUI:
    def __init__(self, root):
        self.root = root
        root.title("Bando Dataset Trainer")
        self.trainer = None # Initialize trainer instance variable

        # --- Existing Placeholder Widgets (as per problem context) ---
        # Assume these are rows 0-3. For example:
        tk.Label(root, text="Dataset Path:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.dataset_path_var = tk.StringVar()
        tk.Entry(root, textvariable=self.dataset_path_var, width=40).grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        tk.Button(root, text="Browse", command=self.browse_dataset).grid(row=0, column=2, sticky='w', padx=5, pady=2)

        tk.Label(root, text="Model Config:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.model_config_var = tk.StringVar()
        tk.Entry(root, textvariable=self.model_config_var, width=40).grid(row=1, column=1, sticky='ew', padx=5, pady=2)
        tk.Button(root, text="Browse", command=self.browse_config).grid(row=1, column=2, sticky='w', padx=5, pady=2)


        tk.Label(root, text="Epochs:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.epochs_var = tk.IntVar(value=10) # Default 10 epochs
        tk.Entry(root, textvariable=self.epochs_var, width=10).grid(row=2, column=1, sticky='w', padx=5, pady=2)

        self.train_button = tk.Button(root, text="Start Training", command=self.start_training)
        self.train_button.grid(row=3, column=0, pady=10, padx=5, sticky='ew')

        self.stop_button = tk.Button(root, text="Stop Training", command=self.stop_training, state='disabled')
        self.stop_button.grid(row=3, column=1, pady=10, padx=5, sticky='ew')

        self.status_var = tk.StringVar(value="Status: Idle")
        tk.Label(root, textvariable=self.status_var).grid(row=3, column=2, sticky='w', padx=5, pady=2)


        # --- New GUI Elements for Live Training Dashboard ---
        # Row numbers adjusted due to new Epochs entry and Stop button

        # Epoch Display
        self.current_epoch_var = tk.StringVar(value="Epoch: 0")
        tk.Label(root, textvariable=self.current_epoch_var).grid(row=5, column=0, sticky='w', padx=5, pady=2)

        # Loss Display
        self.current_loss_var = tk.StringVar(value="Loss: N/A")
        tk.Label(root, textvariable=self.current_loss_var).grid(row=5, column=1, sticky='w', padx=5, pady=2)

        # Progress Bar
        self.progress_bar = ttk.Progressbar(root, orient='horizontal', length=200, mode='determinate')
        self.progress_bar.grid(row=6, column=0, columnspan=3, sticky='ew', padx=5, pady=5)

        # Log Window
        self.log_text = tk.Text(root, height=10, width=50, state='disabled')
        self.log_text.grid(row=7, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)

        log_scrollbar = tk.Scrollbar(root, command=self.log_text.yview)
        log_scrollbar.grid(row=7, column=3, sticky='ns')
        self.log_text['yscrollcommand'] = log_scrollbar.set

        # Configure row/column weights for resizability (good practice)
        root.grid_rowconfigure(7, weight=1) # Log window row
        root.grid_columnconfigure(1, weight=1) # Middle column where entries are, allow expansion

        # Instantiate Trainer with callbacks using root.after_idle for thread-safety
        self.trainer = Trainer(
            epoch_callback=lambda epoch_num: self.root.after_idle(self.update_epoch_display, epoch_num),
            loss_callback=lambda loss_val: self.root.after_idle(self.update_loss_display, loss_val),
            progress_callback=lambda current_epoch, total_epochs: self.root.after_idle(self.update_progress_bar, current_epoch, total_epochs),
            log_callback=lambda message: self.root.after_idle(self.add_log_message, message)
        )

    def browse_dataset(self):
        # Placeholder
        path = filedialog.askdirectory()
        if path:
            self.dataset_path_var.set(path)
        print("Browse dataset called")

    def browse_config(self):
        # Placeholder
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if path:
            self.model_config_var.set(path)
        print("Browse config called")

    def start_training(self):
        if not self.trainer:
            messagebox.showerror("Error", "Trainer not initialized.")
            return

        try:
            total_epochs = self.epochs_var.get()
            if total_epochs <= 0:
                messagebox.showerror("Error", "Number of epochs must be greater than 0.")
                return
        except tk.TclError:
            messagebox.showerror("Error", "Invalid number of epochs.")
            return

        # Reset GUI state
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')
        self.add_log_message("--- New training session started ---")

        self.update_epoch_display(0)
        self.update_loss_display(None)
        self.update_progress_bar(0, total_epochs)

        self.status_var.set("Status: Training...")
        self.train_button.config(state='disabled')
        self.stop_button.config(state='normal')

        # Placeholder: actual dataset and loader would be prepared here
        # For now, trainer.train_loop will use placeholder data or its own internal logic

        # Run training in a separate thread
        self.training_thread = threading.Thread(
            target=self._execute_training_loop,
            args=(total_epochs, None), # Pass None for loader for now
            daemon=True # Ensure thread exits when main app exits
        )
        self.training_thread.start()

    def _execute_training_loop(self, total_epochs, loader):
        try:
            self.trainer.train_loop(total_epochs, loader)
        except Exception as e:
            if self.trainer.log_callback: # Ensure log_callback exists
                 self.root.after_idle(self.add_log_message, f"ERROR in training loop: {e}")
            else: # Fallback to print if no log_callback (should not happen with current Trainer init)
                print(f"ERROR in training loop: {e}")
        finally:
            # Ensure GUI is updated from the main thread after training finishes or errors
            self.root.after_idle(self.on_training_complete)

    def on_training_complete(self):
        """Called when training loop finishes or is stopped, ensures GUI updates are main-thread."""
        if self.trainer.running: # If it was stopped by flag but loop technically completed iteration
            self.status_var.set("Status: Stopped.")
        elif self.trainer.epoch >= self.epochs_var.get(): # Check if all epochs were run
             self.status_var.set("Status: Completed.")
        else: # Stopped before completing all epochs
             self.status_var.set(f"Status: Stopped at epoch {self.trainer.epoch}.")

        self.train_button.config(state='normal')
        self.stop_button.config(state='disabled')
        # Reset progress bar if needed, or leave it at completion state
        # self.update_progress_bar(self.trainer.epoch, self.epochs_var.get())


    def stop_training(self):
        if self.trainer and self.trainer.running:
            self.trainer.stop_training() # Signal the trainer to stop
            self.add_log_message("--- Training stop requested by user ---")
            # Status update and button changes will be handled by on_training_complete
        else:
            self.add_log_message("--- No active training to stop ---")


    # --- GUI Update Callback Methods ---

    def update_epoch_display(self, epoch_num: int):
        """Updates the epoch display label."""
        try:
            # Assuming epoch_num might come as part of a larger string like "1/100"
            # For this method, we expect just the current epoch number.
            current_epoch = int(epoch_num)
            self.current_epoch_var.set(f"Epoch: {current_epoch}")
        except ValueError:
            self.current_epoch_var.set(f"Epoch: {epoch_num}") # Display as is if not a simple int

    def update_loss_display(self, loss_val: float | None):
        """Updates the loss display label, formatting the float."""
        if isinstance(loss_val, float):
            self.current_loss_var.set(f"Loss: {loss_val:.4f}")
        elif loss_val is None:
            self.current_loss_var.set("Loss: N/A")
        else:
            # Handle cases where loss_val might be a string already (e.g., "N/A" or "Calculating...")
            try:
                # Attempt to convert to float if it's a string representation of a number
                num_loss_val = float(loss_val)
                self.current_loss_var.set(f"Loss: {num_loss_val:.4f}")
            except ValueError:
                # If it's not a number string, display as is
                self.current_loss_var.set(f"Loss: {loss_val}")


    def update_progress_bar(self, current_value: int, max_value: int):
        """Updates the progress bar."""
        if max_value > 0 : # Ensure max_value is positive
            self.progress_bar['maximum'] = max_value
            # Ensure current_value does not exceed max_value for determinate mode
            self.progress_bar['value'] = min(int(current_value), max_value)
        else:
            # Handle cases like unknown duration (indeterminate) or error
            self.progress_bar['maximum'] = 100 # Default max
            self.progress_bar['value'] = 0     # Reset value
            # Or switch to indeterminate mode if appropriate: self.progress_bar.config(mode='indeterminate')

    def add_log_message(self, message: str):
        """Adds a message to the log text widget."""
        if not isinstance(message, str):
            message = str(message) # Ensure message is a string
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END) # Scroll to the end
        self.log_text.config(state='disabled')


if __name__ == '__main__':
    root = tk.Tk()
    app = TrainerGUI(root)
    root.mainloop()


# Placeholder for ML framework imports (e.g., torch, tensorflow)
# import torch
# import torch.nn as nn
# import torch.optim as optim

class Trainer:
    def __init__(self, epoch_callback=None, loss_callback=None, progress_callback=None, log_callback=None):
        self.model = None # Placeholder for actual model
        self.criterion = None # Placeholder for loss function
        self.optimizer = None # Placeholder for optimizer
        self.epoch = 0
        self.running = False # To control training loop externally

        # Store callbacks
        self.epoch_callback = epoch_callback
        self.loss_callback = loss_callback
        self.progress_callback = progress_callback
        self.log_callback = log_callback

        if self.log_callback:
            self.log_callback("Trainer initialized.")

    def _initialize_model_components(self, model_config=None, dataset_config=None):
        # Placeholder for model, criterion, optimizer setup
        # self.model = nn.Linear(10, 1) # Example
        # self.criterion = nn.MSELoss()
        # self.optimizer = optim.SGD(self.model.parameters(), lr=0.01)
        if self.log_callback:
            self.log_callback("Model components would be initialized here.")
        pass

    def train_epoch(self, loader):
        # Placeholder for a single epoch training logic
        # for data, target in loader:
        #     self.optimizer.zero_grad()
        #     output = self.model(data)
        #     loss = self.criterion(output, target)
        #     loss.backward()
        #     self.optimizer.step()
        # return loss.item()
        import time # For simulating work
        time.sleep(0.1) # Simulate work
        # Simulate varying loss
        current_loss = 0.5 / (self.epoch + 1) if self.epoch > 0 else 0.5
        return current_loss


    def train_loop(self, epochs, loader=None): # loader would be a DataLoader
        self.running = True
        if self.log_callback:
            self.log_callback(f"Training started for {epochs} epochs...")

        initial_epoch = self.epoch # Store initial epoch for progress calculation if resuming

        for i in range(epochs - initial_epoch): # Loop for remaining epochs
            if not self.running:
                if self.log_callback:
                    self.log_callback(f"Training stopped at epoch {self.epoch} by external request.")
                return

            self.epoch += 1
            # In a real scenario, train_epoch would use the data loader
            loss = self.train_epoch(loader)

            print(f"Epoch {self.epoch}/{epochs} Loss: {loss:.4f}") # Keep console log

            if self.epoch_callback:
                self.epoch_callback(self.epoch)
            if self.loss_callback:
                self.loss_callback(loss)
            if self.progress_callback:
                # Use self.epoch for current value, epochs for total_epochs
                self.progress_callback(self.epoch, epochs)
            if self.log_callback:
                self.log_callback(f"Epoch {self.epoch}/{epochs} Loss: {loss:.4f}")

            # Example: save checkpoint periodically
            if self.epoch % 10 == 0: # Every 10 epochs
                self.save_checkpoint(f"checkpoint_epoch_{self.epoch}.pth")

        self.running = False
        if self.epoch >= epochs: # Check if training completed fully
            if self.log_callback:
                self.log_callback(f"Training completed after {self.epoch} epochs.")
        # If loop exited due to self.running = False, it's handled at the start of the iteration.

    def stop_training(self):
        self.running = False
        if self.log_callback:
            self.log_callback("Stop training signal received.")

    def save_checkpoint(self, path: str):
        # Placeholder for saving checkpoint
        # state = {'epoch': self.epoch, 'model_state_dict': self.model.state_dict(), ...}
        # torch.save(state, path)
        print(f"Checkpoint would be saved to: {path}") # Console log
        if self.log_callback:
            self.log_callback(f"Checkpoint saved: {path}")

    def load_checkpoint(self, path: str):
        # Placeholder for loading checkpoint
        # checkpoint = torch.load(path)
        # self.model.load_state_dict(checkpoint['model_state_dict'])
        # self.epoch = checkpoint['epoch']
        self.epoch = 5 # Example: pretend we loaded a checkpoint from epoch 5
        print(f"Checkpoint would be loaded from: {path}. Resuming from epoch {self.epoch + 1}.") # Console log
        if self.log_callback:
            self.log_callback(f"Checkpoint loaded: {path}. Resuming from epoch {self.epoch + 1}.")
