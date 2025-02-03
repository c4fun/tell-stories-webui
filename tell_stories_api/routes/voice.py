from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pathlib import Path
from tell_stories_api.voice_handler.models import VoiceRequest, VoiceResponse, VoiceCastResponse, ProgressData
from tell_stories_api.voice_handler.service import VoiceService
from tell_stories_api.logs import logger

router = APIRouter()

def get_voice_service():
    return VoiceService()

@router.post("/{process_id}/casting", response_model=VoiceCastResponse)
async def voice_casting(process_id: str):
    """Perform voice casting for the given process"""
    try:
        return await get_voice_service().perform_voice_casting(process_id)
    except Exception as e:
        logger.error(f"Error in voice casting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{process_id}/generate", response_model=VoiceResponse)
async def generate_voice(process_id: str, request: VoiceRequest):
    """Start voice generation process"""
    try:
        return get_voice_service().start_voice_generation(process_id, request)
    except Exception as e:
        logger.error(f"Error in generate_voice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{process_id}/progress", response_model=ProgressData)
async def get_voice_progress(process_id: str):
    """Get progress of voice generation"""
    try:
        return await get_voice_service().get_progress(process_id)
    except Exception as e:
        logger.error(f"Error reading progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{process_id}")
async def process_voice(
    process_id: str,
    request: VoiceRequest,
    voice_service: VoiceService = Depends(get_voice_service)
):
    """Process complete voice generation including casting, generation, and post-processing"""
    try:
        response = await voice_service.process_voice(process_id, request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))