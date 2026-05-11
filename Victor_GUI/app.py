import os
import sys
import gradio as gr
from pathlib import Path

# Setup paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from victor_engine import VictorEngine

# Initialize the engine
engine = VictorEngine()

def chat_interface(user_message, history):
    # Pass message to VictorEngine
    bot_response = engine.chat(user_message)
    # Return formatted response
    return bot_response

def run_dream_cycle():
    result = engine.trigger_dream_cycle()
    return result

def load_memories():
    records = engine.get_memories()
    if not records:
        return "No memories found."
    # Formatting for a text box or dataframe
    formatted = []
    for r in reversed(records[-50:]): # Last 50
        time_str = "Unknown time"
        if "timestamp" in r:
            from datetime import datetime
            time_str = datetime.fromtimestamp(r["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
        formatted.append(f"[{time_str}] {r.get('intent', 'N/A').upper()} ({r.get('emotion', 'N/A')}): {r.get('text', '')}")
    return "\n".join(formatted)

def load_training_proposals():
    proposals = engine.get_ledger()
    if not proposals:
        return "No proposals found."
    formatted = []
    for p in reversed(proposals):
        time_str = "Unknown time"
        if "timestamp" in p:
            from datetime import datetime
            time_str = datetime.fromtimestamp(p["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
        formatted.append(f"[{time_str}] Status: {p.get('status', 'N/A')}\nSource: {p.get('source_text', '')}\nProposed: {p.get('proposed_adjustment', '')}\nID: {p.get('timestamp')}\n")
    return "\n---\n".join(formatted)

def approve_proposal(timestamp_str):
    if not timestamp_str:
        return "Please provide a valid timestamp ID."
    try:
        ts = float(timestamp_str)
        result = engine.approve_proposal(ts)
        return result
    except ValueError:
        return "Invalid ID format. Must be a timestamp."

def run_self_test():
    return engine.run_self_test()

def generate_proposals():
    return engine.generate_training_proposals()


with gr.Blocks(title="Victor AGI Control Panel") as demo:
    gr.Markdown("# Victor AGI - Control Panel")
    gr.Markdown("Welcome to the Victor cognitive architecture. Use this dashboard to interact, monitor memory, and control the training lifecycle.")

    with gr.Tabs():
        with gr.TabItem("Chat"):
            gr.ChatInterface(
                fn=chat_interface,
                chatbot=gr.Chatbot(height=400),
                title="Victor Chat",
                description="Interact directly with Victor's core.",
            )

        with gr.TabItem("SDR Memory"):
            gr.Markdown("### Memory Viewer")
            refresh_btn = gr.Button("Refresh Memory")
            memory_view = gr.TextArea(lines=15, interactive=False)
            refresh_btn.click(fn=load_memories, inputs=None, outputs=memory_view)

        with gr.TabItem("REM Dream Cycle"):
            gr.Markdown("### Trigger REM Cycle")
            gr.Markdown("Run a dream cycle to compress memories, extract patterns, and reinforce the 'I am Victor' directive.")
            dream_btn = gr.Button("Run Dream Cycle")
            dream_output = gr.Textbox(label="Result")
            dream_btn.click(fn=run_dream_cycle, inputs=None, outputs=dream_output)

        with gr.TabItem("Training & Upgrades"):
            gr.Markdown("### Training Approval Ledger")
            gr.Markdown("Proposals are generated from interactions in the learning queue.")
            generate_btn = gr.Button("Process Learning Queue -> Generate Proposals")
            generate_out = gr.Textbox(label="Result")
            generate_btn.click(fn=generate_proposals, inputs=None, outputs=generate_out)

            gr.Markdown("---")
            refresh_ledger_btn = gr.Button("Refresh Ledger")
            ledger_view = gr.TextArea(lines=10, interactive=False)
            refresh_ledger_btn.click(fn=load_training_proposals, inputs=None, outputs=ledger_view)

            gr.Markdown("---")
            gr.Markdown("### Approve Proposal")
            approve_id = gr.Textbox(label="Paste Timestamp ID here to approve")
            approve_btn = gr.Button("Approve & Apply")
            approve_out = gr.Textbox(label="Result")
            approve_btn.click(fn=approve_proposal, inputs=approve_id, outputs=approve_out)

        with gr.TabItem("System Controls"):
            gr.Markdown("### Diagnostics")
            test_btn = gr.Button("Run System Self-Test")
            test_output = gr.Textbox(label="Self-Test Status")
            test_btn.click(fn=run_self_test, inputs=None, outputs=test_output)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
