import gradio as gr
import requests
import subprocess
import os
import json
from pathlib import Path
from typing import List, Dict, Tuple
from tell_stories_api.voice_handler.utils import load_va_database, generate_audio_instruct
from tell_stories_api.logs import logger
from dotenv import load_dotenv
load_dotenv()

def format_status_message(response):
    status_emoji = "❌"
    if response["status"] == "success" or response["status"] == "completed":
        status_emoji = "✅"
    elif response["status"] == "processing":
        status_emoji = "⏳"
    else:
        status_emoji = "❌"
    
    message = f"{status_emoji} Status: {response['status']}\n"
    if response.get("output_path"):
        message += f"📁 Output: {response['output_path']}"
    return message

def create_voice_tab(api_base_url, process_id):
    def open_folder(path):
        try:
            # For Windows
            if os.name == 'nt':
                os.startfile(path)
            # For macOS
            elif os.name == 'posix' and os.uname().sysname == 'Darwin':
                subprocess.run(['open', path])
            # For Linux/Unix
            elif os.name == 'posix':
                subprocess.run(['xdg-open', path])
            return "Folder opened successfully!"
        except Exception as e:
            return f"Error opening folder: {str(e)}"

    def voice_casting(process_id):
        try:
            response = requests.post(f"{api_base_url}/voice/{process_id}/casting")
            result = response.json()
            return format_status_message(result), result
        except Exception as e:
            error_result = {"error": str(e)}
            return format_status_message(error_result), error_result

    def generate_voice(process_id):
        request_data = {
            "host": os.getenv("COSYVOICE2_HOST"),
            "port": os.getenv("COSYVOICE2_PORT"),
            "save_mp4_with_subtitles": False
        }
        try:
            response = requests.post(
                f"{api_base_url}/voice/{process_id}/generate",
                json=request_data
            )
            result = response.json()
            return format_status_message(result), result
        except Exception as e:
            error_result = {"error": str(e)}
            return format_status_message(error_result), error_result

    def get_voice_progress(process_id):
        try:
            response = requests.get(f"{api_base_url}/voice/{process_id}/progress")
            result = response.json()
            return format_status_message(result), result
        except Exception as e:
            error_result = {"error": str(e)}
            return format_status_message(error_result), error_result

    def update_folder_visibility(response):
        path = response.get("output_path", "")
        status_message = format_status_message(response)
        if path:
            status_message += f"\n📁 Output: {path}"
            return (
                status_message,
                response,
                gr.update(visible=True),
                path,
                ""
            )
        return (
            status_message,
            response,
            gr.update(visible=False),
            "",
            ""
        )
    
    def load_cast_file(process_id: str) -> Tuple[List[List[str]], List[Dict]]:
        """Load the cast.json file for the given process ID."""
        cast_path = Path(f"data/process/{process_id}/cast.json")
        try:
            if cast_path.exists():
                with open(cast_path, 'r') as f:
                    cast_data = json.load(f)
                    logger.info(f'Loaded cast data: {cast_data}')
                    # Convert to table format for display
                    table_data = [[c["character"], c["va_name"]] for c in cast_data]
                    return table_data, cast_data
            logger.warning(f"Cast file not found: {cast_path}")
            return [], []
        except Exception as e:
            logger.error(f"Error loading cast file: {e}")
            return [], []

    def save_cast_file(process_id: str, cast_data: List[Dict]) -> Dict:
        """Save the cast data to cast.json file."""
        try:
            if not process_id or isinstance(process_id, gr.components.Textbox):
                logger.error(f"Invalid process_id: {process_id}")
                return {"status": "error", "message": "Invalid process ID"}
                
            cast_path = Path(f"data/process/{process_id}/cast.json")
            cast_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cast_path, 'w') as f:
                json.dump(cast_data, f, indent=4)
            logger.info(f"Successfully saved cast file to {cast_path}")
            return {"status": "success", "message": f"Cast saved to {cast_path}"}
        except Exception as e:
            logger.error(f"Error saving cast file: {e}")
            return {"status": "error", "message": str(e)}

    def update_va_selection(evt: gr.SelectData, cast_data: List[Dict], va_database: List[Dict]) -> Tuple[gr.Dropdown, List[Dict], int]:
        """Update the VA selection when a character's VA is clicked."""
        # logger.info(f'update_va_selection - cast_data: {cast_data}, evt.index: {evt.index}')
        if not va_database or not cast_data:
            return gr.Dropdown(visible=False), cast_data, -1
        
        # Get all available VA names and sort them
        va_choices = sorted([va["va_name"] for va in va_database])
        # logger.info(f'va_choices: {va_choices}')
        
        # Handle index - take the first index if it's a list
        row_idx = evt.index[0] if isinstance(evt.index, list) else evt.index
        
        # Create and return a dropdown for VA selection
        return gr.Dropdown(
            choices=va_choices,
            value=cast_data[row_idx]["va_name"],
            label=f"Select VA for {cast_data[row_idx]['character']}",
            visible=True
        ), cast_data, row_idx

    def apply_va_selection(va_name: str, cast_data: List[Dict], selected_idx: int) -> Tuple[gr.Dataframe, List[Dict]]:
        """Apply the selected VA to the cast data."""
        logger.info(f'apply_va_selection - cast_data: {cast_data}, va_name: {va_name}, selected_idx: {selected_idx}')
        
        if selected_idx >= 0 and selected_idx < len(cast_data):
            cast_data[selected_idx]["va_name"] = va_name
            
        table_data = [[c["character"], c["va_name"]] for c in cast_data]
        return (
            gr.Dataframe(value=table_data, headers=["Character", "Voice Actor"]),
            cast_data
        )

    def generate_voice_preview(va_name: str, character: str, preview_text: str, va_database: List[Dict]) -> Tuple[str, str]:
        """Generate a preview audio for the selected voice actor."""
        try:
            # Find VA metadata
            va_meta = next((va for va in va_database if va["va_name"] == va_name), None)
            if not va_meta:
                return None, f"❌ Error: Voice actor metadata not found for {va_name}"
            
            url = f"http://{os.getenv('COSYVOICE2_HOST')}:{os.getenv('COSYVOICE2_PORT')}/inference_instruct2"
            
            # Create preview directory if not exists
            preview_dir = Path("data/preview")
            preview_dir.mkdir(parents=True, exist_ok=True)
            output_path = preview_dir / f"{character}_{va_name}_preview.wav"
            
            # Use the existing generate_audio function
            success = generate_audio_instruct(
                url=url,
                text=preview_text,
                instruct_text="normal",
                prompt_wav=va_meta['prompt_wav'],
                output_path=str(output_path)
            )
            
            if success:
                logger.info(f"Generated preview audio: {output_path}")
                return str(output_path), f"✅ Preview generated for {character}"
            else:
                return None, f"❌ Failed to generate preview for {character}"
                
        except Exception as e:
            logger.error(f"Error in voice preview: {e}")
            return None, f"❌ Error: {str(e)}"

    def preview_current_va(cast_data: List[Dict], selected_idx: int, preview_text: str, va_database: List[Dict]) -> Tuple[str, str]:
        """Generate preview for currently selected VA."""
        if selected_idx < 0 or selected_idx >= len(cast_data):
            return None, "❌ Please select a character first"
            
        character = cast_data[selected_idx]["character"]
        va_name = cast_data[selected_idx]["va_name"]
        
        # Replace {character} placeholder with actual character name
        preview_text = preview_text.replace("{character}", character)
        
        audio_path, status = generate_voice_preview(va_name, character, preview_text, va_database)
        if audio_path:
            return audio_path, status
        return None, status

    with gr.Tab("Voice Generation"):
        with gr.Column():
            # Manual Cast Selection Section
            with gr.Group():
                gr.Markdown("### 0. Manual Cast Selection(Optional)")
                
                # Load initial data
                initial_cast = load_cast_file(process_id)
                va_database = load_va_database()
                # logger.info(f'va_database is: {va_database}')

                # Cast management buttons
                with gr.Row():
                    load_cast_btn = gr.Button("Load Cast", variant="primary")
                    save_cast_btn = gr.Button("Save Cast", variant="primary")
                
                # Cast display and editing
                with gr.Row():
                    cast_table = gr.Dataframe(
                        value=initial_cast[0],
                        headers=["Character", "Voice Actor"],
                        interactive=False,
                        elem_id="cast_table"
                    )
                
                # VA selection dropdown and preview section
                with gr.Column():
                    va_dropdown = gr.Dropdown(visible=False, label="Select Voice Actor")
                    with gr.Row(visible=False) as preview_row:
                        with gr.Column():
                            preview_btn = gr.Button("🔊 Generate Sample Voice", variant="huggingface")
                            preview_text = gr.Textbox(
                                label="Preview Text (Use {character} as placeholder for character name)",
                                value="My name is {character}. This is generated by tell stories dot AI.",
                                lines=2,
                                show_label=True
                            )
                            preview_status = gr.Markdown("")
                        preview_audio = gr.Audio(
                            label="Voice Preview",
                            type="filepath",
                            interactive=False,
                            show_label=True
                        )
                
                # Status message for save/load operations
                status_message = gr.Markdown("")
                
                # Store current cast data and selected index
                current_cast = gr.State(value=initial_cast[1])
                selected_index = gr.State(value=-1)
                
                # Event handlers
                cast_table.select(
                    fn=update_va_selection,
                    inputs=[current_cast, gr.State(va_database)],
                    outputs=[va_dropdown, current_cast, selected_index]
                ).then(
                    lambda: gr.update(visible=True),
                    outputs=[preview_row]
                )
                
                va_dropdown.change(
                    fn=apply_va_selection,
                    inputs=[va_dropdown, current_cast, selected_index],
                    outputs=[cast_table, current_cast]
                )
                
                preview_btn.click(
                    fn=preview_current_va,
                    inputs=[current_cast, selected_index, preview_text, gr.State(va_database)],
                    outputs=[preview_audio, preview_status]
                )
                
                load_cast_btn.click(
                    fn=lambda pid: load_cast_file(pid),
                    inputs=[process_id],
                    outputs=[cast_table, current_cast]
                )
                
                def save_cast_wrapper(cast_data: List[Dict], pid: str) -> str:
                    result = save_cast_file(pid, cast_data)
                    return f"💾 {result['message']}"
                
                save_cast_btn.click(
                    fn=save_cast_wrapper,
                    inputs=[current_cast, process_id],
                    outputs=[status_message]
                )

            # Voice Casting Section
            with gr.Group():
                gr.Markdown("### 1. Voice Casting")
                cast_btn = gr.Button("Generate Voice Cast", variant="primary", scale=3, min_width=120)
                with gr.Group():
                    voice_cast_status_md = gr.Markdown(label="Status", value="")
                    with gr.Accordion("Details", open=True):
                        voice_cast_status = gr.JSON(label="Voice Cast Status")

            # Voice Generation Section
            with gr.Group():
                gr.Markdown("### 2. Voice Generation")
                with gr.Row():
                    with gr.Column():
                        generate_btn = gr.Button("Generate Voice", variant="primary", scale=3, min_width=120)
                        with gr.Group():
                            voice_status_md = gr.Markdown(label="Status", value="")
                            with gr.Accordion("Details", open=True):
                                voice_status = gr.JSON(label="Voice Status")
                            output_path = gr.State(value="")
                            with gr.Row(visible=False) as folder_row:
                                folder_btn = gr.Button("📁 Open Output Folder", variant="secondary", scale=1)
                                folder_status = gr.Markdown(value="")
                    with gr.Column():
                        voice_progress_btn = gr.Button("Get Voice Progress", variant="huggingface", scale=3, min_width=120)
                        with gr.Group():
                            voice_progress_status_md = gr.Markdown(label="Status", value="")
                            with gr.Accordion("Details", open=True):
                                voice_progress_status = gr.JSON(label="Progress Status")

        # Wire up all events within the component
        cast_btn.click(
            fn=lambda p: voice_casting(p),
            inputs=[process_id],
            outputs=[voice_cast_status_md, voice_cast_status]
        )

        generate_btn.click(
            fn=lambda p: update_folder_visibility(generate_voice(p)[1]),
            inputs=[process_id],
            outputs=[voice_status_md, voice_status, folder_row, output_path, folder_status]
        )

        voice_progress_btn.click(
            fn=lambda p: update_folder_visibility(get_voice_progress(p)[1]),
            inputs=[process_id],
            outputs=[voice_progress_status_md, voice_progress_status, folder_row, output_path, folder_status]
        )

        folder_btn.click(
            fn=open_folder,
            inputs=[output_path],
            outputs=[folder_status]
        )

        return {
            "components": [
                cast_btn, generate_btn, voice_progress_btn,
                voice_cast_status_md, voice_cast_status,
                voice_status_md, voice_status,
                voice_progress_status_md, voice_progress_status,
                folder_row, output_path, folder_status
            ]
        } 