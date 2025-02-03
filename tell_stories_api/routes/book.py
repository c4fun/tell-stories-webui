from fastapi import APIRouter, status
from tell_stories_api.book_handler.models import Book, BookCreate, BookUpdate, ChapterList, CastList
from tell_stories_api.common.models import CharactersDict
from tell_stories_api.book_handler import service

router = APIRouter()

# Main CRUD operations
@router.post("", response_model=Book, status_code=status.HTTP_201_CREATED)
async def create_book(book: BookCreate):
    """Create a new book with basic information"""
    return await service.create_book(book)

@router.get("/{book_id}", response_model=Book)
async def read_book(book_id: str):
    """Read all information about a book"""
    return await service.get_book(book_id)

@router.put("/{book_id}", response_model=Book)
async def update_book(book_id: str, book_update: BookUpdate):
    """Update book's fields including name, plot, chapters, characters, and cast"""
    return await service.update_book(book_id, book_update)

@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: str):
    """Delete a book by its ID"""
    await service.delete_book(book_id)
    return None

# Sub-resource operations
@router.put("/{book_id}/chapters", response_model=Book)
async def update_book_chapters(book_id: str, chapters: ChapterList):
    """Update only the chapters of a book"""
    return await service.update_chapters(book_id, chapters)

@router.put("/{book_id}/characters", response_model=Book)
async def update_book_characters(book_id: str, characters: CharactersDict):
    """Update only the characters of a book"""
    return await service.update_characters(book_id, characters)

@router.put("/{book_id}/cast", response_model=Book)
async def update_book_cast(book_id: str, cast: CastList):
    """Update only the cast of a book"""
    return await service.update_cast(book_id, cast)

# Processing operations
@router.post("/{book_id}/process-new-chapter/{project_id}", response_model=Book)
async def process_new_chapter(book_id: str, project_id: str):
    """Process a new chapter's data from plot.json and cast.json files and update the book accordingly.
    This will update chapters, characters, cast, and merge the plot."""
    return await service.process_new_chapter(book_id, project_id)
