from fastapi import APIRouter, HTTPException, BackgroundTasks
from tell_stories_api.logs import logger

from tell_stories_api.script_handler.models import (
    ScriptRequest, ScriptResponse, PlotRequest, 
    CastRequest, LineRequest
)
from tell_stories_api.script_handler.service import ScriptService

router = APIRouter()

@router.post("/{process_id}/plot", response_model=ScriptResponse)
async def generate_plot(process_id: str, request: PlotRequest):
    try:
        if not request.story_path and not request.text_input:
            raise HTTPException(
                status_code=400, 
                detail="Either story_path or text_input must be provided"
            )
        result = await ScriptService.generate_plot(
            process_id, 
            request.story_path, 
            request.text_input,
            request.book_id
        )
        return ScriptResponse(**result)
    except Exception as e:
        logger.error(f"Error in generate_plot: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{process_id}/cast", response_model=ScriptResponse)
async def generate_cast(process_id: str, request: CastRequest):
    try:
        result = await ScriptService.generate_cast(process_id, request.book_id)
        return ScriptResponse(**result)
    except Exception as e:
        logger.error(f"Error in generate_cast: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{process_id}/lines", response_model=ScriptResponse)
async def generate_lines(
    process_id: str, 
    request: LineRequest, 
    background_tasks: BackgroundTasks
):
    try:
        # Initialize the process
        result = await ScriptService.initialize_lines_generation(process_id)
        
        # Schedule the background processing
        background_tasks.add_task(
            ScriptService.process_lines_background,
            process_id,
            request.split_dialogue,
            request.all_caps_to_proper
        )
        
        return ScriptResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in generate_lines: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{process_id}/lines/progress")
async def get_script_progress(process_id: str):
    try:
        result = await ScriptService.get_script_progress(process_id)
        return ScriptResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in get_script_progress: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{process_id}", response_model=ScriptResponse)
async def generate_script(
    process_id: str, 
    request: ScriptRequest,
    background_tasks: BackgroundTasks
):
    """Generate complete script by running all three steps(plot, cast, lines) in sequence"""
    try:
        if not request.story_path and not request.text_input:
            raise HTTPException(
                status_code=400, 
                detail="Either story_path or text_input must be provided"
            )
        result = await ScriptService.generate_complete_script(
            process_id,
            request.story_path,
            request.split_dialogue,
            request.all_caps_to_proper,
            request.text_input,
            request.book_id
        )
        
        # Schedule the background processing for lines
        background_tasks.add_task(
            ScriptService.process_lines_background,
            process_id,
            request.split_dialogue,
            request.all_caps_to_proper
        )
        
        return ScriptResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in generate_script: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
