import gradio as gr
from pathlib import Path
import shutil
import json
from typing import Literal, Optional
import os
from tell_stories_api.const import VA_DATABASE_PATH
from tell_stories_api.voice_handler.utils import to_relative_path

# Use the base VA path for creating new voice actors
VA_FOLDER = Path(VA_DATABASE_PATH)

Language = Literal["English", "Mandarin", "Cantonese", "Japanese"]
Gender = Literal["Male", "Female"]
VoiceType = Literal["Action", "Narration"]
Age = Literal["Kid", "Teen", "Young Adult", "Middle-Aged", "Senior"]
VoicePitch = Literal["Very High", "High", "Medium", "Low", "Very Low"]

def create_voice_admin(api_base_url):
    def create_va_name(language: Language, gender: Gender, voice_type: VoiceType, 
                      age: Age, voice_pitch: VoicePitch, name: str) -> str:
        """Create VA name from properties"""
        # Convert spaces to hyphens and remove any special characters
        age_formatted = age.lower().replace(" ", "-")
        voice_pitch_formatted = voice_pitch.lower().replace(" ", "-")
        name_formatted = name.strip().replace(" ", "")
        
        return f"{language}_{gender.lower()}_{voice_type.lower()}_{age_formatted}_{voice_pitch_formatted}_{name_formatted}"

    def create_voice(
        prompt_text: str,
        prompt_audio: str,
        language: Language,
        gender: Gender,
        voice_type: VoiceType,
        age: Age,
        voice_pitch: VoicePitch,
        name: str
    ) -> str:
        try:
            # Input validation
            if not all([prompt_text, prompt_audio, language, gender, voice_type, age, voice_pitch, name]):
                return "Error: All fields are required"

            # Generate VA name
            va_name = create_va_name(language, gender, voice_type, age, voice_pitch, name)
            
            # Create VA directory
            va_dir = VA_FOLDER / va_name
            va_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy audio file
            audio_ext = Path(prompt_audio).suffix
            prompt_wav_name = f"{prompt_text}.wav"  # Force .wav extension
            prompt_wav_path = va_dir / prompt_wav_name
            
            # Convert audio to WAV format if needed
            if audio_ext.lower() != '.wav':
                import subprocess
                subprocess.run([
                    'ffmpeg', '-i', prompt_audio,
                    '-acodec', 'pcm_s16le',
                    '-ar', '22050',
                    str(prompt_wav_path)
                ])
            else:
                shutil.copy2(prompt_audio, prompt_wav_path)
            
            relative_prompt_wav_path = to_relative_path(str(prompt_wav_path))
            # Create meta.json
            meta_data = {
                "va_name": va_name,
                "prompt_text": prompt_text,
                "prompt_wav": relative_prompt_wav_path,
                "language": language,
                "gender": gender,
                "voice_type": voice_type,
                "age": age,
                "voice_pitch": voice_pitch
            }
            
            with open(va_dir / "meta.json", 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, indent=2, ensure_ascii=False)
            
            return f"Successfully created voice actor: {va_name}"
            
        except Exception as e:
            return f"Error creating voice: {str(e)}"

    def list_voices():
        try:
            va_base_path = VA_FOLDER
            voices = []
            
            for va_dir in va_base_path.iterdir():
                if not va_dir.is_dir():
                    continue
                    
                meta_path = va_dir / "meta.json"
                if not meta_path.exists():
                    continue
                    
                with open(meta_path, 'r', encoding='utf-8') as f:
                    va_info = json.load(f)
                voices.append(va_info)
            
            return {"voices": voices}
            
        except Exception as e:
            return {"error": str(e)}

    def preview_va_name(
        language: Language,
        gender: Gender,
        voice_type: VoiceType,
        age: Age,
        voice_pitch: VoicePitch,
        name: str
    ) -> str:
        return create_va_name(language, gender, voice_type, age, voice_pitch, name)

    with gr.Group():
        gr.Markdown("## Voice Actor Management")
        
        with gr.Row():
            with gr.Column():
                prompt_text = gr.Textbox(label="Prompt Text",
                    placeholder="Enter the text for the voice sample")
                gr.Markdown("""
                **Important Instructions:**
                1. The voice sample should be clear vocal without any background music or noise.
                2. The text should match exactly to the voice.
                """)
            prompt_audio = gr.Audio(label="Voice Sample", type="filepath")

        with gr.Row():
            language = gr.Dropdown(
                choices=["English", "Mandarin", "Cantonese", "Japanese"],
                label="Language"
            )
            gender = gr.Dropdown(
                choices=["Male", "Female"],
                label="Gender"
            )
            voice_type = gr.Dropdown(
                choices=["Action", "Narration"],
                label="Voice Type"
            )

        with gr.Row():
            age = gr.Dropdown(
                choices=["Kid", "Teen", "Young Adult", "Middle-Aged", "Senior"],
                label="Age",
                value="Young Adult"
            )
            voice_pitch = gr.Dropdown(
                choices=["Very High", "High", "Medium", "Low", "Very Low"],
                label="Voice Pitch"
            )
            name = gr.Textbox(label="Name", placeholder="Enter a unique identifier")

        preview_name = gr.Textbox(label="Preview VA Name", interactive=False)
        
        with gr.Row():
            create_btn = gr.Button("Create Voice Actor", variant="primary")
            list_btn = gr.Button("List Voice Actors", variant="primary")
        
        output_text = gr.Textbox(label="Status")
        voices_json = gr.JSON(label="Available Voice Actors")
        
        # Wire up the events
        create_btn.click(
            fn=create_voice,
            inputs=[prompt_text, prompt_audio, language, gender, voice_type, age, voice_pitch, name],
            outputs=output_text
        )
        
        list_btn.click(
            fn=list_voices,
            outputs=voices_json
        )

        # Preview VA name as user types
        for input_component in [language, gender, voice_type, age, voice_pitch, name]:
            input_component.change(
                fn=preview_va_name,
                inputs=[language, gender, voice_type, age, voice_pitch, name],
                outputs=preview_name
            )