from pydantic import BaseModel
from typing import Dict, Optional, Any
import os
from dotenv import load_dotenv
load_dotenv()

class VoiceRequest(BaseModel):
    host: str = os.getenv("COSYVOICE2_HOST")
    port: int = os.getenv("COSYVOICE2_PORT")
    save_mp4_with_subtitles: bool = False

class VoiceResponse(BaseModel):
    status: str
    process_id: str
    message: Optional[str] = None
    output_path: Optional[str] = None
    error: Optional[str] = None

class ProgressData(BaseModel):
    total_lines: int
    processed_lines: int
    success_count: int
    failed_count: int
    narrator_success_count: int
    narrator_failed_count: int
    status: str  # 'processing', 'completed', 'failed'
    output_path: Optional[str] = None
    error: Optional[str] = None

class VoiceCastResponse(BaseModel):
    status: str
    process_id: str
    cast: Dict[str, Any] 