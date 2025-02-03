from pathlib import Path
import json
from tell_stories_api.logs import logger
from tell_stories_api.voice_handler.utils import load_va_database

VA_DB = json.dumps([
    {k: v for k, v in va.items() if k not in ('prompt_text', 'prompt_wav')}
    for va in load_va_database()
], indent=2)

async def get_va_match_prompt(characters: str, book_id: str = "") -> str:
    example_output = [
    {
        "character": "Narrator",
        "va_name": "English_female_narration_young-adult_medium_Alissa"
    },
    {
        "character": "Mrs. McNeil",
        "va_name": "English_female_action_middle-aged_low_Vanessa"
    },
    {
        "character": "Bob",
        "va_name": "English_male_action_young-adult_medium_TomHiddleston"
    }
]
    previous_cast = ""
    if book_id:
        from tell_stories_api.book_handler.service import get_book
        try:
            book = await get_book(book_id)
            if book.cast and book.cast.cast:
                # Convert CastEntry objects to dictionaries using model_dump()
                cast_list = [entry.model_dump() for entry in book.cast.cast]
                previous_cast = f"""
Previous chapters cast:
{json.dumps(cast_list, indent=4, ensure_ascii=False)}
"""
        except Exception as e:
            logger.warning(f"Failed to get book context for book_id {book_id}: {str(e)}")
    logger.debug(f"previous_cast: {previous_cast}")

    prompt_template = f"""
{characters}
The above JSON are the character involved in current story. Now we got these characters, please choose the VAs for me according to these rules:

1. Must match in language, gender, type.
2. Strongly prefer to match in pitch and age.
3. Optionally match in accent.
4. Different characters must have different VAs.
5. We got these VAs in the DB as the following JSON.

{VA_DB}

6. If characters cast is provided below, for characters that already appear in the book's cast, you MUST reuse their exact VA assignments:
   - If a character exists in the book's cast, use the SAME va_name that was previously assigned
   - This ensures consistency across chapters
{previous_cast}

7. Output all things in JSON format as following. We need the character, va_name to be retrieved from the VAs in the DB. No extra props are needed. Do not output any extra explanations, just output the JSON itself.
{json.dumps(example_output, indent=4)}
"""
    return prompt_template.strip()


async def get_va_and_main_plot_prompt(story: str, book_id: str = "") -> str:
    example_output = {
	"plot": {
 	  "nsfw": False,
 	  "explicit_sexual_content": False,
 	  "main_plot": "A poor young girl who, unable to sell her matches on a freezing New Year's Eve, gradually freezes to death while striking matches that give her visions of warmth, comfort, and her loving grandmother. The story ends with her death, as she's found frozen the next morning, but with a peaceful smile on her face as her grandmother's spirit has taken her to heaven.",
      "detailed_main_plot": "On a bitterly cold New Year's Eve, a young girl tries to sell matches in the snowy streets. She has lost her slippers and wears threadbare clothes. Her father, harsh and unkind, expects her to return with money; otherwise, she might be punished. The mother is absent, presumably deceased, adding to the child's loneliness. Passersby either ignore her or fail to notice her plight, hurrying on to their own festive gatherings. Desperate for warmth, the girl lights the matches she is supposed to sell. With each tiny flame, she experiences brief visions: a warm stove, a lavish holiday feast, a magnificent Christmas tree. Most precious to her is the vision of her beloved grandmother, who passed away yet appears in the comforting glow of the matchlight. The girl lights all her remaining matches to keep her grandmother's image near, imagining they ascend together to a better place free from cold and hunger. By morning, the little match girl is found lifeless on the street. People discover the spent matches around her, realizing too late the harsh reality she faced."
	},
	"characters": {
	  "count": 2,
	  "dict": {
	    "Narrator": {
	      "language": "English",
	      "gender": "female",
	      "type": "narration",
	      "age": "middle-aged",
	      "pitch": "low"
	    },
	    "The little match girl": {
	      "language": "English",
	      "gender": "female",
	      "type": "action",
	      "age": "child",
	      "pitch": "high",
	      "alternativeNames": ["the girl"]
	    }
	  }
	}
}
    
    # Get previous chapters context if book_id is provided
    previous_chapters_context = ""
    if book_id:
        from tell_stories_api.book_handler.service import get_book
        try:
            book = await get_book(book_id)
            if book.plot and book.plot.detailed_main_plot:
                previous_chapters_context = f"""
Previous chapters context:
{book.plot.detailed_main_plot}
"""
            if book.characters and book.characters.dict:
                # Convert CharacterDetails objects to dictionaries
                characters_dict = {
                    char_name: char_details.model_dump()
                    for char_name, char_details in book.characters.dict.items()
                }
                previous_chapters_context += f"""
Previous chapters characters:
{json.dumps(characters_dict, indent=4, ensure_ascii=False)}
"""
        except Exception as e:
            logger.warning(f"Failed to get book context for book_id {book_id}: {str(e)}")
    logger.debug(f"previous_chapters_context: {previous_chapters_context}")

    prompt_template = f"""
{story}

Analyze this story above, and make a thorough dictionary of voice actors/actresses I need to read it. There are the rules:
1. Assign character for each VA. A character needs to say something to be assigned a VA; otherwise no VA is needed. You must include following properties according to the content:
  1.1 language(English, Mandarin, Cantonese, Spanish, Japanese),
  1.2 gender(male, female),
  1.3 type(narration, action),
  1.4 age(child, teen, young adult, middle-aged, senior, monster),
  1.5 pitch(very high, high, medium, low, very low)
2. For character that is typed action, list all alternative names(in its original language) in the story to the alternativeNames section. So lines from later parts can be matched the character accurately.
3. The narrator should be also counted as an individual character. But if the narrator clearly is one character in the story, then the narrator and character should use the same voice. 
4. We'd better use a female narrator unless the story is evidently told by a male.
5. If previous chapters plot is provided below, ensure character consistency with previous chapters:
  5.1 Use the exact same name for the same character.
  5.2 Keep track of any new characters introduced in this chapter.
  5.3 Consider the plot development and character relationships from previous chapters.
{previous_chapters_context}
6. Output all things in JSON format as following. Do not output any extra explanations, just output the JSON itself.
{json.dumps(example_output, indent=4)}
"""
    return prompt_template.strip()

def get_character_lines_prompt_with_attr(story_plot_and_va, story):
    example_json = {
        "lines": [
            {
                "character": "Narrator",
                "instruct": "normal", 
                "line": "It was late at night. The wind is howling fiercely."
            },
            {
                "character": "The little match girl",
                "instruct": "trembling",
                "line": "It's so cold!"
            },
            {
				"character": "Narrator",
				"instruct": "normal",
				"line": "Said the little match girl, trembling."
			}
        ]
    }

    return f"""
Analyze this story below, and assign each line with the character. These are the rules:
1. We already have the main plot of the story and character's cast as below.

{story_plot_and_va}

2. DO NOT dissect the narrator's line into smaller sections if they are sequential. Even if the narrator's line is long or has different instructs, it should be read as a whole.
3. For each line, output the character, instruct, and line. 
3.1 The character must match whom Rule 1 mentioned.
3.2 The instruct is how the actor should say the line, like "trembling", "surprisingly", "fearful".
3.3 Line rules:
    3.3.1 Do not omit any sentences in lines!
    3.3.2 Do not alter any words expect for all-caps words said by actors/actresses, change the all-caps words to lower case except the first letter of the sentence.
    3.3.3 Do not alter any punctuation marks.
    3.3.4 The attribution phrases like "he said/she said" MUST BE PRESERVED.
3.4 Output all things in JSON format as following. Do not output any extra explanations, just output the JSON itself.
{json.dumps(example_json, indent=2)}

Here's the story:
{story}
"""

def get_split_decision_prompt(context_lines: str, main_plot: str) -> str:
    return f"""Given these lines from a story and the main plot summary, find the best place to split the story if one exists.
Main plot: {main_plot}

Context (40 lines):
{context_lines}

Rules for splitting:
1. Don't split between parts of the same dialogue or action
2. Good split points are between scenes, paragraphs, or complete dialogue exchanges
3. The split should preserve context for both parts
4. Look for natural transitions between sections

Analyze these lines and respond in this format:
SPLIT: [line_number] (or "NO_SPLIT" if no good split point)
REASON: [brief explanation]"""