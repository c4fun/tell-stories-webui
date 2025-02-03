from pydantic import BaseModel, Field
from typing import List, Optional
from tell_stories_api.common.models import Plot, CharactersDict, CastEntry

class Chapter(BaseModel):
    """Model for a book chapter"""
    plot: Plot = Field(..., description="Chapter plot details")
    characters: CharactersDict = Field(..., description="Characters in the chapter")

class ChapterList(BaseModel):
    """Model for list of chapters"""
    count: int = Field(..., description="Number of chapters")
    chapters: List[Chapter] = Field(..., description="List of chapters")

class CastList(BaseModel):
    """Model for list of cast entries"""
    count: int = Field(..., description="Number of cast entries")
    cast: List[CastEntry] = Field(..., description="List of character to voice actor mappings")


class BookCreate(BaseModel):
    """Model for creating a new book"""
    name: str = Field(..., description="Name of the book")
    book_id: str = Field(..., description="Unique identifier for the book")

class BookUpdate(BaseModel):
    """Model for updating a book"""
    name: Optional[str] = Field(None, description="Updated name of the book")
    plot: Optional[Plot] = Field(None, description="Updated plot of the book")
    chapters: Optional[ChapterList] = Field(None, description="Updated chapters list")
    characters: Optional[CharactersDict] = Field(None, description="Updated characters list")
    cast: Optional[CastList] = Field(None, description="Updated cast list")

class Book(BaseModel):
    """Model for a complete book"""
    book_id: str = Field(..., description="Unique identifier for the book")
    name: str = Field(..., description="Name of the book")
    plot: Optional[Plot] = Field(None, description="Book plot")
    chapters: Optional[ChapterList] = Field(None, description="List of chapters")
    characters: Optional[CharactersDict] = Field(None, description="List of characters")
    cast: Optional[CastList] = Field(None, description="List of cast entries") 