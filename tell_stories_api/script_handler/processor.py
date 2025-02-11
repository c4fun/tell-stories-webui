import re
import json
import os
from typing import List, Dict
from tell_stories_api.logs import logger
from tell_stories_api.provider.deepseek_api import DeepSeekAPI
from tell_stories_api.provider.qwen_api import QwenAPI
from tell_stories_api.provider.openrouter_api import OpenRouterAPI
from tell_stories_api.script_handler.prompt import (
    get_va_match_prompt,
    get_va_and_main_plot_prompt,
    get_character_lines_prompt_with_attr,
    get_split_decision_prompt
)
from tqdm import tqdm

# Initialize all providers
deepseek = DeepSeekAPI()
qwen = QwenAPI(model="qwen-max")
openrouter = OpenRouterAPI()

# Add this constant at the top of the file
COMMONLY_CAPITALIZED_WORDS = {
    'CHAPTER', 'BOOK', 'VOLUME',  # Structure words
    'BANG', 'BOOM', 'CRASH', 'SLAM', 'THUD',  # Sound effects
    'FUCK', 'SHIT', 'DAMN', 'HELL',  # Expletives
    'HEY', 'OH', 'AH', 'OI', 'YO',  # Interjections
    'NO', 'YES', 'STOP', 'WAIT',  # Common emphatic words
    'HA', 'HAH', 'HAHA', 'AHAHA',  # Laughter
    "MH", "MHH", "MHHH", "MHHHH", "MHHHHH"  # Moaning
}

# Add model priority configuration
MODEL_CONFIG = {
    "primary": os.getenv("PRIMARY_MODEL", "deepseek").lower(),
    "fallback_order": os.getenv("MODEL_FALLBACK_ORDER", "deepseek,openrouter,qwen").lower().split(",")
}

def predict_with_fallback(prompt: str) -> tuple[str, int, str]:
    """
    Predict using the primary model with fallback logic
    """
    # Get initial model choice
    model_choice = MODEL_CONFIG["primary"]
    logger.info(f"Selected model: {model_choice}")
    
    # Try primary model first
    try:
        if model_choice == "qwen":
            return qwen.predict(prompt)
        elif model_choice == "openrouter":
            return openrouter.predict_v3(prompt)
        else:  # deepseek is default
            return deepseek.predict_v3(prompt)
            
    except Exception as e:
        logger.error(f"Error with {model_choice}: {str(e)}")
        
        # Try fallback models in order
        for fallback_model in MODEL_CONFIG["fallback_order"]:
            if fallback_model == model_choice:
                continue
                
            try:
                logger.info(f"Trying fallback model: {fallback_model}")
                if fallback_model == "qwen":
                    return qwen.predict(prompt)
                elif fallback_model == "openrouter":
                    return openrouter.predict_v3(prompt)
                else:  # deepseek
                    return deepseek.predict_v3(prompt)
            except Exception as fallback_e:
                logger.error(f"Error with fallback {fallback_model}: {str(fallback_e)}")
                continue
                
        # If all models fail, raise the original error
        raise e

async def generate_va_and_main_plot(story: str, book_id: str = ""):
    prompt = await get_va_and_main_plot_prompt(story, book_id)
    response, total_tokens, finish_reason = predict_with_fallback(prompt)
    logger.info(f"response.content: {response.content}")
    logger.info(f"prompt: {prompt}")
    logger.info(f"total_tokens: {total_tokens}")
    logger.info(f"finish_reason: {finish_reason}")
    return response.content, total_tokens, finish_reason

async def generate_va_match_from_script(characters: str, book_id: str = ""):
    prompt = await get_va_match_prompt(characters, book_id)
    response, total_tokens, finish_reason = predict_with_fallback(prompt)
    logger.info(f"response.content: {response.content}")
    logger.info(f"prompt: {prompt}")
    logger.info(f"total_tokens: {total_tokens}")
    logger.info(f"finish_reason: {finish_reason}")
    return response.content, total_tokens, finish_reason

def generate_character_lines_from_script(story, json_plot):
    prompt = get_character_lines_prompt_with_attr(json_plot, story)
    response, total_tokens, finish_reason = predict_with_fallback(prompt)
    logger.info(f"response.content: {response.content}")
    logger.info(f"prompt: {prompt}")
    logger.info(f"total_tokens: {total_tokens}")
    logger.info(f"finish_reason: {finish_reason}")
    return response.content, total_tokens, finish_reason

def clean_scripts_ticks(input_script: str) -> str:
    return input_script.replace("```json", "").replace("```", "")

def split_dialogue_and_narration(line_obj: Dict, all_caps_to_proper: bool = False) -> List[Dict]:
    """Split a line containing both dialogue and narration into separate lines"""
    logger.debug(f"line_obj: {line_obj}")
    line = line_obj["line"]
    character = line_obj["character"]
    if character.lower() == "narrator":
        return [line_obj]
    
    # Match various types of quotes including Chinese quotes
    quote_patterns = [
        r'\u201c([^\u201d]+)\u201d',  # Curly double quotes (")
        r'"([^"]+)"',      # Standard double quotes
        r'「([^」]+)」',    # Japanese/Chinese corner brackets
        r'『([^』]+)』',    # Japanese/Chinese white corner brackets
    ]

    secondary_quote_patterns = [
        r'\u2018([^\u2019]+)\u2019',  # Curly single quotes (')
        r"'((?:[^']|(?<=\w)'(?=(?:m|s|d|ll|re|ve|t)\b))+)'",  # Standard single quotes with contraction handling
    ]
    
    # Find all quoted text and their positions
    all_matches = []
    processed_positions = set()
    
    for pattern in quote_patterns:
        matches = list(re.finditer(pattern, line))
        for m in matches:
            start_pos = m.start()
            if start_pos not in processed_positions:
                quote_text = m.group(1) if pattern != r"'([^']+)'" else m.group(0)
                all_matches.append((start_pos, quote_text, m.group(0)))
                processed_positions.add(start_pos)
    
    if not all_matches:
        for pattern in secondary_quote_patterns:
            matches = list(re.finditer(pattern, line))
            for m in matches:
                start_pos = m.start()
                quote_text = m.group(1) if pattern != r"'([^']+)'" else m.group(0)
                all_matches.append((start_pos, quote_text, m.group(0)))
                processed_positions.add(start_pos)

    # Sort matches by position
    all_matches.sort(key=lambda x: x[0])
    
    # If no matches found or matches look incorrect, return the original line
    if not all_matches or any(len(m[1].strip()) < 2 for m in all_matches):
        return [line_obj]
    
    result = []
    last_pos = 0
    
    # Process text in order
    for start_pos, quote_text, full_quote in all_matches:
        # Check if there's narration before this quote
        pre_quote_text = line[last_pos:start_pos].strip()
        if pre_quote_text:
            # Split into multiple narration parts if needed
            narration_parts = re.split(r'([.!?]+\s+)', pre_quote_text)
            # Recombine parts properly
            narration_segments = []
            for j in range(0, len(narration_parts)-1, 2):
                if j+1 < len(narration_parts):
                    narration_segments.append(narration_parts[j] + narration_parts[j+1])
                else:
                    narration_segments.append(narration_parts[j])
            if narration_parts and len(narration_parts) % 2 == 1:
                narration_segments.append(narration_parts[-1])
            
            for narration in narration_segments:
                narration = narration.strip()
                if narration:
                    result.append({
                        "character": "Narrator",
                        "instruct": "normal",
                        "line": narration.strip(" ,.;")
                    })
        
        # Add this function inside split_dialogue_and_narration
        def process_capitalized_text(text: str) -> str:
            words = text.split()
            processed_words = []
            for word in words:
                # Check if word is in our common caps list
                if word in COMMONLY_CAPITALIZED_WORDS:
                    processed_words.append(word.capitalize())
                # For other words, keep them as is
                else:
                    processed_words.append(word)
            return ' '.join(processed_words)

        # Modify the capitalization check
        processed_quote = quote_text
        if all_caps_to_proper:
            if quote_text.isupper():
                # If entire text is uppercase, capitalize normally
                processed_quote = quote_text.capitalize()
            else:
                # Process individual commonly capitalized words
                processed_quote = process_capitalized_text(quote_text)
            
        result.append({
            "character": character,
            "instruct": line_obj["instruct"],
            "line": processed_quote
        })
        
        last_pos = start_pos + len(full_quote)
    
    # Check if there's any remaining narration after the last quote
    if last_pos < len(line):
        remaining_text = line[last_pos:].strip()
        if remaining_text:
            narration_parts = re.split(r'([.!?]+\s+)', remaining_text)
            narration_segments = []
            for j in range(0, len(narration_parts)-1, 2):
                if j+1 < len(narration_parts):
                    narration_segments.append(narration_parts[j] + narration_parts[j+1])
                else:
                    narration_segments.append(narration_parts[j])
            if narration_parts and len(narration_parts) % 2 == 1:
                narration_segments.append(narration_parts[-1])
            
            for narration in narration_segments:
                narration = narration.strip()
                if narration:
                    result.append({
                        "character": "Narrator",
                        "instruct": "normal",
                        "line": narration.strip(" ,.;")
                    })
    
    logger.debug(f"result: {result}")
    return result


def split_story_into_parts(story: str, main_plot: str, target_length: int = 60) -> List[str]:
    parts = []
    current_part = []
    batch_size = 40
    consecutive_no_splits = 0
    
    # Split into lines first
    lines = story.split('\n')
    logger.info(f"Total lines: {len(lines)}")
    i = 0
    
    # Create progress bar
    with tqdm(total=len(lines), desc="Splitting story") as pbar:
        while i < len(lines):
            current_part.extend(lines[i:i+batch_size])
            logger.info(f"Current part length: {len(current_part)}")
            
            # If we have enough lines to consider splitting
            if len(current_part) >= target_length:
                # Get the last 40 lines for context
                context_window = current_part[-batch_size:]
                context_text = '\n'.join(f"{idx+1}. {line}" for idx, line in enumerate(context_window))
                
                # Ask LLM for split decision
                prompt = get_split_decision_prompt(context_text, main_plot)
                response, _, _ = predict_with_fallback(prompt)
                logger.info(f"response.content: {response.content}")
                # Parse LLM response
                split_line = None
                if 'SPLIT:' in response.content:
                    split_text = response.content.split('SPLIT:')[1].split('\n')[0].strip()
                    if split_text.isdigit():
                        split_line = int(split_text)
                        logger.info(f"Found split point at line {split_line}")
                
                # Handle split decision
                if split_line and split_line < batch_size:
                    # Calculate actual position in current_part
                    split_position = len(current_part) - batch_size + split_line
                    # Split the story at this point
                    parts.append('\n'.join(current_part[:split_position]))
                    current_part = current_part[split_position:]
                    consecutive_no_splits = 0
                    logger.info(f"Split story at natural break point")
                else:
                    consecutive_no_splits += 1
                    logger.info(f"No good split point found. Attempt {consecutive_no_splits}/3")
                    
                    # Force split after 3 failed attempts
                    if consecutive_no_splits >= 3:
                        # Keep the last batch_size lines in current_part
                        split_position = len(current_part) - batch_size
                        parts.append('\n'.join(current_part[:split_position]))
                        current_part = current_part[split_position:]
                        consecutive_no_splits = 0
                        logger.info("Forced split after 3 failed attempts")
            
            # Update progress bar with batch_size or remaining lines
            progress = min(batch_size, len(lines) - i)
            pbar.update(progress)
            i += batch_size
    
    # Add any remaining content
    if current_part:
        parts.append('\n'.join(current_part))
    
    return parts

def process_story_part(part: str, json_plot: Dict) -> List[Dict]:
    raw_lines, part_3_tokens, part_3_finish_reason = generate_character_lines_from_script(part, json_plot)
    clean_lines = clean_scripts_ticks(raw_lines)
    json_lines = json.loads(clean_lines)
    return json_lines["lines"]