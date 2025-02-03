from fastapi import HTTPException, status
from . import processor
from tell_stories_api.book_handler.models import Book, BookCreate, BookUpdate, ChapterList, CastList, Chapter
from tell_stories_api.common.models import Plot, CharactersDict, CastEntry, CharacterDetails
from tell_stories_api.logs import logger

async def create_book(book: BookCreate) -> Book:
    """Create a new book with basic information"""
    processor.ensure_book_dir()
    
    if processor.book_exists(book.book_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book with ID {book.book_id} already exists"
        )
    
    # Initialize with empty lists and default values
    book_data = {
        "book_id": book.book_id,
        "name": book.name,
        "plot": {
            "main_plot": "",
            "detailed_main_plot": "",
            "nsfw": False,
            "explicit_sexual_content": False
        },
        "chapters": {
            "count": 0,
            "chapters": []
        },
        "characters": {
            "count": 0,
            "dict": {}
        },
        "cast": {
            "count": 0,
            "cast": []
        }
    }
    
    processor.write_book_file(book.book_id, book_data)
    return Book(**book_data)

async def delete_book(book_id: str) -> None:
    """Delete a book by its ID"""
    if not processor.book_exists(book_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    processor.delete_book_file(book_id)

async def get_book(book_id: str) -> Book:
    """Get book by ID"""
    if not processor.book_exists(book_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    book_data = processor.read_book_file(book_id)
    return Book(**book_data)

async def update_book(book_id: str, book_update: BookUpdate) -> Book:
    """Update book's fields including name, plot, chapters, characters, and cast"""
    if not processor.book_exists(book_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    book_data = processor.read_book_file(book_id)
    
    # Update basic fields if provided
    if book_update.name is not None:
        book_data["name"] = book_update.name
    if book_update.plot is not None:
        book_data["plot"] = book_update.plot.model_dump()
        
    # Update chapters if provided
    if book_update.chapters is not None:
        book_data["chapters"] = {
            "count": book_update.chapters.count,
            "chapters": [chapter.model_dump() for chapter in book_update.chapters.chapters]
        }
        
    # Update characters if provided
    if book_update.characters is not None:
        book_data["characters"] = {
            "count": book_update.characters.count,
            "dict": {name: details.model_dump() for name, details in book_update.characters.dict.items()}
        }
        
    # Update cast if provided
    if book_update.cast is not None:
        book_data["cast"] = {
            "count": book_update.cast.count,
            "cast": [cast_entry.model_dump() for cast_entry in book_update.cast.cast]
        }
    
    processor.write_book_file(book_id, book_data)
    return Book(**book_data)

async def update_chapters(book_id: str, chapters: ChapterList) -> Book:
    """Update only the chapters of a book"""
    if not processor.book_exists(book_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    book_data = processor.read_book_file(book_id)
    book_data["chapters"] = {
        "count": chapters.count,
        "chapters": [chapter.model_dump() for chapter in chapters.chapters]
    }
    
    processor.write_book_file(book_id, book_data)
    return Book(**book_data)

async def update_characters(book_id: str, characters: CharactersDict) -> Book:
    """Update only the characters of a book"""
    if not processor.book_exists(book_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    book_data = processor.read_book_file(book_id)
    book_data["characters"] = {
        "count": characters.count,
        "dict": {name: details.model_dump() for name, details in characters.dict.items()}
    }
    
    processor.write_book_file(book_id, book_data)
    return Book(**book_data)

async def update_cast(book_id: str, cast: CastList) -> Book:
    """Update only the cast of a book"""
    if not processor.book_exists(book_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    book_data = processor.read_book_file(book_id)
    book_data["cast"] = {
        "count": cast.count,
        "cast": [cast_entry.model_dump() for cast_entry in cast.cast]
    }
    
    processor.write_book_file(book_id, book_data)
    return Book(**book_data)

async def process_new_chapter(book_id: str, project_id: str) -> Book:
    """Process a new chapter's data from plot.json and cast.json files and update the book accordingly"""
    if not processor.book_exists(book_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )
    
    try:
        plot_data = processor.read_plot_file(project_id)
        cast_data = processor.read_cast_file(project_id)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    # Read current book data
    book_data = processor.read_book_file(book_id)
    
    # 1. Update chapters
    logger.info(f'plot_data["characters"]: {plot_data["characters"]}')
    characters_dict = {
        name: CharacterDetails(**details) 
        for name, details in plot_data["characters"]["dict"].items()
    }
    
    new_chapter = Chapter(
        plot=Plot(**plot_data["plot"]),
        characters={
            "count": plot_data["characters"]["count"],
            "dict": characters_dict
        }
    )
    logger.info(f'new_chapter: {new_chapter}')
    
    if "chapters" not in book_data:
        book_data["chapters"] = {"count": 0, "chapters": []}
    
    book_data["chapters"]["chapters"].append(new_chapter.model_dump())
    book_data["chapters"]["count"] = len(book_data["chapters"]["chapters"])
    
    # 2. Update characters dictionary
    if "characters" not in book_data:
        book_data["characters"] = {"count": 0, "dict": {}}
    
    new_characters = plot_data.get("characters", {}).get("dict", {})
    for name, details in new_characters.items():
        if name not in book_data["characters"]["dict"]:
            # Directly assign the character details without extra nesting
            book_data["characters"]["dict"][name] = details
    book_data["characters"]["count"] = len(book_data["characters"]["dict"])
    
    # 3. Update cast list
    logger.info(f'cast_data: {cast_data}')
    if "cast" not in book_data:
        book_data["cast"] = {"count": 0, "cast": []}
    
    new_cast = [CastEntry(**entry) for entry in cast_data]
    existing_cast_chars = {entry["character"] for entry in book_data["cast"]["cast"]}
    
    for cast_entry in new_cast:
        if cast_entry.character not in existing_cast_chars:
            book_data["cast"]["cast"].append(cast_entry.model_dump())
            existing_cast_chars.add(cast_entry.character)
    
    book_data["cast"]["count"] = len(book_data["cast"]["cast"])
    
    # 4. Update plot by merging with the new detailed plot
    if "plot" not in book_data or book_data["plot"] is None:
        book_data["plot"] = {
            "main_plot": plot_data["plot"]["main_plot"],
            "detailed_main_plot": plot_data["plot"]["detailed_main_plot"],
            "nsfw": plot_data["plot"]["nsfw"],
            "explicit_sexual_content": plot_data["plot"]["explicit_sexual_content"]
        }
    else:
        # Update main_plot if it's empty
        if not book_data["plot"]["main_plot"]:
            book_data["plot"]["main_plot"] = plot_data["plot"]["main_plot"]
        
        # Update nsfw and explicit_sexual_content - only change to True if new chapter has True
        book_data["plot"]["nsfw"] = (
            book_data["plot"]["nsfw"] or plot_data["plot"]["nsfw"]
        )
        book_data["plot"]["explicit_sexual_content"] = (
            book_data["plot"]["explicit_sexual_content"] or 
            plot_data["plot"]["explicit_sexual_content"]
        )
        
        # Append new detailed plot
        new_detailed_plot = plot_data["plot"]["detailed_main_plot"]
        if book_data["plot"]["detailed_main_plot"]:
            book_data["plot"]["detailed_main_plot"] += "\n\n" + new_detailed_plot
        else:
            book_data["plot"]["detailed_main_plot"] = new_detailed_plot
    
    logger.info(f'book_data["plot"]: {book_data["plot"]}')
    
    # Save updated book data
    processor.write_book_file(book_id, book_data)
    return Book(**book_data) 