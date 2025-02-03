import gradio as gr
import uuid
from tell_stories_api.webui.components import create_script_tab, create_lines_editor_tab, create_voice_tab
from tell_stories_api.webui.components.voice_admin import create_voice_admin

def create_gradio_app(api_base_url: str = "http://localhost:8000/api"):
    """Create and configure the Gradio interface"""
    
    blocks = gr.Blocks(title="Story Generation UI")
    
    with blocks:
        gr.Markdown("# Story Generation Interface by TellStories.AI")
        
        # Shared Process ID at the top
        process_id = gr.Textbox(
            label="Process ID",
            value=str(uuid.uuid4()),
            interactive=True
        )
        
        # Create all tabs and get their components
        with gr.Tabs():
            script_tab = create_script_tab(api_base_url, process_id)
            voice_tab = create_voice_tab(api_base_url, process_id)
            lines_tab = create_lines_editor_tab(process_id)
            with gr.Tab("Voice Admin"):
                create_voice_admin(api_base_url)
    
    return blocks 