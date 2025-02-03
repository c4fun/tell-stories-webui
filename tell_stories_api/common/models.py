from pydantic import BaseModel, Field
from typing import Optional, Dict, List

class Plot(BaseModel):
    """Common plot model used across the application"""
    nsfw: bool = Field(..., description="Whether the content is NSFW")
    explicit_sexual_content: bool = Field(..., description="Whether the content contains explicit sexual content")
    main_plot: str = Field(..., description="The main plot summary")
    detailed_main_plot: str = Field(..., description="Detailed description of the main plot")

class CharacterDetails(BaseModel):
    """Common character details model used across the application"""
    language: str = Field(..., description="Character's primary language")
    gender: str = Field(..., description="Character's gender")
    type: str = Field(..., description="narration OR action")
    age: str = Field(..., description="Character's age")
    pitch: str = Field(..., description="Voice pitch for the character")
    alternativeNames: Optional[List[str]] = Field(None, description="Alternative names for the character")

class CharactersDict(BaseModel):
    """Model for characters in a chapter"""
    count: int = Field(..., description="Number of characters in the chapter")
    dict: Dict[str, CharacterDetails] = Field(..., description="Map of character names to their details")

class CastEntry(BaseModel):
    """Model for character to voice actor mapping"""
    character: str = Field(..., description="Name of the character")
    va_name: str = Field(..., description="Name of the voice actor") 