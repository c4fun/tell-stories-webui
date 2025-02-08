from pathlib import Path
from .models import VoiceRequest, VoiceResponse, VoiceCastResponse, ProgressData
from .processor import VoiceProcessor
from tell_stories_api.logs import logger
import json
from threading import Thread

class VoiceProcessError(Exception):
    """Base exception for voice processing errors"""
    pass

class FileNotFoundError(VoiceProcessError):
    """Raised when required files are not found"""
    pass

class ProcessingError(VoiceProcessError):
    """Raised when processing fails"""
    pass

class VoiceService:
    def __init__(self):
        self.processor = VoiceProcessor()

    async def perform_voice_casting(self, process_id: str) -> VoiceCastResponse:
        process_dir = Path("data/process") / process_id
        cast_output = process_dir / "voice_cast.json"
        
        if not (process_dir / "cast.json").exists():
            raise FileNotFoundError("cast.json not found. Please run script generation first.")
        
        cast_dict = self.processor.process_cast_file(process_dir)
        
        with open(cast_output, 'w', encoding='utf-8') as f:
            json.dump(cast_dict, f, indent=2, ensure_ascii=False)
        
        return VoiceCastResponse(
            status="completed",
            process_id=process_id,
            cast=cast_dict
        )

    def start_voice_generation(
        self, 
        process_id: str, 
        request: VoiceRequest,
    ) -> VoiceResponse:
        process_dir = Path("data/process") / process_id
        
        # Validate required files
        required_files = ["plot.json", "cast.json", "lines.json"]
        for file in required_files:
            if not (process_dir / file).exists():
                raise FileNotFoundError(f"Required file {file} not found. Please run script generation first.")
            
        if not (process_dir / "voice_cast.json").exists():
            raise FileNotFoundError("voice_cast.json not found. Please run voice casting first.")
        
        # Start processing in background using Thread
        # BUG: 这里使用threading有一个开发时的运行时bug：就是如果我reload了程序，那么这个线程就会消失，这样生成就会断掉
        # TODO: 不过这个后续可以通过断点续传来做
        Thread(
            target=self.processor.process_voice_generation,
            args=(request, process_dir),
            daemon=True
        ).start()
        
        return VoiceResponse(
            status="processing",
            process_id=process_id,
            message="Voice generation started. Use /voice/{process_id}/progress to check voice generation status."
        )

    async def get_progress(self, process_id: str) -> ProgressData:
        process_dir = Path("data/process") / process_id
        progress_file = process_dir / "voice_progress.json"
        
        if not progress_file.exists():
            raise FileNotFoundError("Progress file not found. Voice generation may not have started.")
        
        with open(progress_file, 'r') as f:
            progress_data = json.load(f)
            
        return ProgressData(**progress_data)

    async def process_voice(
        self,
        process_id: str,
        request: VoiceRequest,
    ) -> VoiceResponse:
        # First, perform voice casting
        cast_response = await self.perform_voice_casting(process_id)
        if cast_response.status != "completed":
            raise ProcessingError("Voice casting failed")
        
        # Then, start voice generation
        self.start_voice_generation(process_id, request)

        return VoiceResponse(
            status="success",
            process_id=process_id,
            message="Voice generation started. Use /voice/{process_id}/progress to check voice generation status."
        )
