# Victor Prime - Control Panel

Welcome to the control panel for Victor, your private, persistent AI architecture. This application provides a user-friendly interface to interact with Victor, view its memory, and guide its real-time learning.

## What is this?
This is a dedicated Graphical User Interface (GUI) wrapper for the Victor core. It provides:
- **Chat Interface**: Talk to Victor directly.
- **SDR Memory Viewer**: View Victor's Sparse Distributed Representation memories where interactions, intents, and emotions are stored.
- **Dream Cycle**: Trigger background memory compression, contradiction cleanup, and identity reinforcement.
- **Training Approval Ledger**: Victor learns from your feedback safely. Interactions are added to a queue, and upgrade proposals are generated. You review and approve them before they are applied.

## How to Launch (1-Click)

### On Windows
1. Double click the file named `launch_windows.bat`.
2. A command prompt will open, install necessary software (the first time), and then launch the GUI in your web browser.

### On Mac or Linux
1. Open a terminal in this folder.
2. Run the script by typing: `./launch_linux_mac.sh`
3. It will install necessary software and open the GUI in your web browser.

## How to Use

- **Chat Tab**: Type messages to Victor. If you want to correct Victor, explicitly type "correction: [your correction]".
- **SDR Memory Tab**: Click "Refresh Memory" to see the recent intents and interactions Victor has logged.
- **REM Dream Cycle Tab**: Click "Run Dream Cycle" to manually trigger memory compression. This cleans up the memory log and reinforces the core identity.
- **Training & Upgrades Tab**:
  1. Click "Process Learning Queue -> Generate Proposals" to see if Victor has learned any corrections from your chat.
  2. Click "Refresh Ledger" to view pending proposals.
  3. Copy the ID of a proposal you like, paste it into the "Approve Proposal" box, and click "Approve & Apply".

## Troubleshooting

- **"Command not found: python"**: Make sure you have Python 3 installed on your computer and added to your system PATH.
- **The GUI doesn't open in the browser**: The browser might have been blocked. Open your browser manually and go to `http://127.0.0.1:7860`.
- **Self-Test Failed**: Go to the "System Controls" tab and click "Run System Self-Test". If it fails, make sure all files were downloaded correctly and you haven't moved files outside the folder structure.
