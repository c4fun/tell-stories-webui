from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List
from tell_stories_api.logs import logger
from tqdm import tqdm
from .processor import (
    clean_scripts_ticks,
    generate_va_and_main_plot,
    generate_va_match_from_script,
    split_story_into_parts,
    process_story_part,
    split_dialogue_and_narration
)


class ScriptService:
    @staticmethod
    async def generate_plot(process_id: str, story_path: str = None, text_input: str = None, book_id: str = None) -> Dict:
        process_dir = Path("data/process") / process_id
        process_dir.mkdir(parents=True, exist_ok=True)
        
        # Get story content either from file or text input
        if story_path:
            story = Path(story_path).read_text(encoding='utf-8')
        elif text_input:
            story = text_input
        else:
            raise ValueError("Either story_path or text_input must be provided")
        
        # Generate main plot and characters
        raw_plot, _, _ = await generate_va_and_main_plot(story, book_id)
        clean_plot = clean_scripts_ticks(raw_plot)
        json_plot = json.loads(clean_plot)
        
        # Save plot data
        plot_path = process_dir / "plot.json"
        with open(plot_path, "w", encoding='utf-8') as f:
            json.dump(json_plot, f, indent=4, ensure_ascii=False)
        
        # Save story for later use
        with open(process_dir / "story.txt", "w", encoding='utf-8') as f:
            f.write(story)
            
        return {
            "status": "success",
            "process_id": process_id,
            "output_path": str(plot_path)
        }

    @staticmethod
    async def generate_cast(process_id: str, book_id: str = "") -> Dict:
        process_dir = Path("data/process") / process_id
        
        # Check if plot.json exists
        plot_path = process_dir / "plot.json"
        if not plot_path.exists():
            raise Exception("plot.json not found. Please run generate_plot first.")
        
        # Load plot data
        with open(plot_path, encoding='utf-8') as f:
            json_plot = json.load(f)
        
        # Generate cast
        characters_str = json.dumps(json_plot["characters"], indent=4, ensure_ascii=False)
        raw_va_match, _, _ = await generate_va_match_from_script(characters_str, book_id)
        clean_va_match = clean_scripts_ticks(raw_va_match)
        va_match = json.loads(clean_va_match)
        
        # Save cast data
        cast_path = process_dir / "cast.json"
        with open(cast_path, "w", encoding='utf-8') as f:
            json.dump(va_match, f, indent=4, ensure_ascii=False)
            
        return {
            "status": "success",
            "process_id": process_id,
            "output_path": str(cast_path)
        }

    @staticmethod
    async def initialize_lines_generation(process_id: str) -> Dict:
        """Initialize the lines generation process"""
        process_dir = Path("data/process") / process_id
        
        # Check if required files exist
        required_files = ["plot.json", "story.txt"]
        for file in required_files:
            if not (process_dir / file).exists():
                raise Exception(f"{file} not found. Please run previous steps first.")
        
        # Initialize progress file
        progress_path = process_dir / "script_progress.json"
        with open(progress_path, "w", encoding='utf-8') as f:
            json.dump({"state": "init"}, f)
        
        return {
            "status": "success",
            "process_id": process_id,
            "message": "Processing started. Use /script/{process_id}/lines/progress to check status."
        }

    @staticmethod
    def process_lines_background(process_id: str, split_dialogue: bool, all_caps_to_proper: bool):
        """Process the lines in background"""
        try:
            process_dir = Path("data/process") / process_id
            progress_path = process_dir / "script_progress.json"
            story_parts_path = process_dir / "story_parts.json"
            
            # Update progress - splitting story
            with open(progress_path, "w", encoding='utf-8') as f:
                json.dump({
                    "state": "splitting_story",
                    "process_id": process_id
                }, f)
                
            # Load required data
            with open(process_dir / "plot.json", encoding='utf-8') as f:
                json_plot = json.load(f)
            
            story_parts: List[str] = []  # Initialize as empty list instead of dict
            # Check if story parts already exist
            if story_parts_path.exists():
                with open(story_parts_path, encoding='utf-8') as f:
                    story_parts = json.load(f)["parts"]
            else:
                # Load story and split into parts
                with open(process_dir / "story.txt", encoding='utf-8') as f:
                    story = f.read()
                story_parts = split_story_into_parts(story, json_plot["plot"]["main_plot"])
                # Cache story parts
                with open(story_parts_path, "w", encoding='utf-8') as f:
                    json.dump({"parts": story_parts}, f, indent=4, ensure_ascii=False)
            
            # Update progress - processing lines
            with open(progress_path, "w", encoding='utf-8') as f:
                json.dump({
                    "state": "processing_lines",
                    "process_id": process_id
                }, f)
                
            # Process parts in parallel
            with ThreadPoolExecutor(max_workers=16) as executor:
                future_to_index = {
                    executor.submit(process_story_part, part, json_plot): idx 
                    for idx, part in enumerate(story_parts)
                }
                
                results = [None] * len(story_parts)
                with tqdm(total=len(story_parts), desc="Processing story parts") as pbar:
                    for future in as_completed(future_to_index):
                        idx = future_to_index[future]
                        results[idx] = future.result()
                        pbar.update(1)
            
            # Process results
            processed_lines = []
            for part_lines in results:
                if split_dialogue:
                    for line in part_lines:
                        processed_lines.extend(split_dialogue_and_narration(
                            line, 
                            all_caps_to_proper=all_caps_to_proper
                        ))
                else:
                    processed_lines.extend(part_lines)
            
            # Save lines data
            lines_path = process_dir / "lines.json"
            with open(lines_path, "w", encoding='utf-8') as f:
                json.dump({"lines": processed_lines}, f, indent=4, ensure_ascii=False)
                
            # Update progress - completed
            with open(progress_path, "w", encoding='utf-8') as f:
                json.dump({
                    "state": "completed",
                    "process_id": process_id,
                    "output_path": str(lines_path)
                }, f)
                
        except Exception as e:
            # Update progress - error
            with open(progress_path, "w", encoding='utf-8') as f:
                json.dump({
                    "state": "error",
                    "process_id": process_id,
                    "error": str(e)
                }, f)
            logger.error(f"Error in process_lines_background: {str(e)}")
            raise

    @staticmethod
    async def get_script_progress(process_id: str) -> Dict:
        process_dir = Path("data/process") / process_id
        progress_path = process_dir / "script_progress.json"
        
        if not progress_path.exists():
            raise Exception("Progress file not found. Please start processing first.")
            
        with open(progress_path, encoding='utf-8') as f:
            progress = json.load(f)
            
        # Convert progress data to match ScriptResponse format
        return {
            "status": progress.get("state", "unknown"),
            "process_id": process_id,
            "message": progress.get("error") if progress.get("state") == "error" else None,
            "output_path": progress.get("output_path")
        }

    @staticmethod
    async def generate_complete_script(process_id: str, story_path: str = None, split_dialogue: bool = True, all_caps_to_proper: bool = True, text_input: str = None, book_id: str = None) -> Dict:
        """Generate complete script by running all three steps(plot, cast, lines) in sequence"""
        try:
            # Generate plot
            await ScriptService.generate_plot(process_id, story_path, text_input, book_id)
            
            # Generate cast
            await ScriptService.generate_cast(process_id)
            
            # Generate lines
            result = await ScriptService.initialize_lines_generation(process_id)
            
            return {
                "status": "success",
                "process_id": process_id,
                "message": "Script generation started. Use /script/{process_id}/lines/progress to check lines processing status."
            }
            
        except Exception as e:
            logger.error(f"Error in generate_complete_script: {str(e)}")
            raise