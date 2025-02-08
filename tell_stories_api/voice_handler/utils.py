import requests
import torch
import torchaudio
import numpy as np
import subprocess
from tell_stories_api.logs import logger
from pathlib import Path
import json
from typing import List, Dict
from tell_stories_api.const import VA_DATABASE_PATHS

def to_absolute_path(relative_path: str) -> str:
    """Convert a relative path to absolute path."""
    workspace_root = Path(__file__).parent.parent.parent
    return str(workspace_root / relative_path)

def to_relative_path(absolute_path: str) -> str:
    """Convert an absolute path to relative path from workspace root."""
    workspace_root = Path(__file__).parent.parent.parent
    return str(Path(absolute_path).relative_to(workspace_root))

def generate_audio(url: str, text: str, prompt_text: str, prompt_wav: str, output_path: str) -> bool:
    payload = {
        'tts_text': text,
        'prompt_text': prompt_text
    }
    try:
        # Convert relative path to absolute path for file operations
        abs_prompt_wav = to_absolute_path(prompt_wav)
        files = [('prompt_wav', ('prompt_wav', open(abs_prompt_wav, 'rb'), 'application/octet-stream'))]
        response = requests.request("GET", url, data=payload, files=files, stream=True)
    except Exception as e:
        logger.error(e)
        return False
    
    try:
        tts_audio = b''
        for r in response.iter_content(chunk_size=16000):
            tts_audio += r
        tts_speech = torch.from_numpy(np.array(np.frombuffer(tts_audio, dtype=np.int16))).unsqueeze(dim=0)
        torchaudio.save(output_path, tts_speech, 22050)  # target_sr = 22050
        logger.info(f'Saved audio to {output_path}')
        return True
    except Exception as e:
        logger.error(e)
        return False

def generate_audio_instruct(url: str, text: str, instruct_text: str, prompt_wav: str, output_path: str) -> bool:
    payload = {
        'tts_text': text,
        'instruct_text': instruct_text
    }
    try:
        # Convert relative path to absolute path for file operations
        abs_prompt_wav = to_absolute_path(prompt_wav)
        files = [('prompt_wav', ('prompt_wav', open(abs_prompt_wav, 'rb'), 'application/octet-stream'))]
        response = requests.request("GET", url, data=payload, files=files, stream=True)
    except Exception as e:
        logger.error(e)
        return False
    
    try:
        tts_audio = b''
        for r in response.iter_content(chunk_size=16000):
            tts_audio += r
        tts_speech = torch.from_numpy(np.array(np.frombuffer(tts_audio, dtype=np.int16))).unsqueeze(dim=0)
        torchaudio.save(output_path, tts_speech, 22050)
        logger.info(f'(instruct mode) Saved audio to {output_path}')
        return True
    except Exception as e:
        logger.error(e)
        return False

def get_audio_duration(file_path: str) -> float:
    """Get duration of audio file using ffprobe"""
    result = subprocess.run([
        'ffprobe', 
        '-v', 'quiet',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        str(file_path)
    ], capture_output=True, text=True)
    return float(result.stdout.strip())

def load_va_database() -> List[Dict]:
    """Load and concatenate all meta.json files from VA directories."""
    va_database = []
    
    logger.info(f'VA_DATABASE_PATHS is: {VA_DATABASE_PATHS}')
    for va_base_path in VA_DATABASE_PATHS:
        try:
            # Iterate through all subdirectories in each VA path
            for va_dir in Path(va_base_path).iterdir():
                if not va_dir.is_dir():
                    continue
                    
                meta_path = va_dir / "meta.json"
                if not meta_path.exists():
                    logger.warning(f"No meta.json found in {va_dir}")
                    continue
                    
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        va_info = json.load(f)
                        # Add source path to help with debugging/tracking
                        # va_info['source_path'] = str(va_dir)
                        va_database.append(va_info)
                except Exception as e:
                    logger.error(f"Error loading meta.json from {va_dir}: {e}")
                    
        except Exception as e:
            logger.error(f"Error accessing VA directory {va_base_path}: {e}")
    
    return va_database 