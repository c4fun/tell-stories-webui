from pydantic import BaseModel, Field
from typing import Optional

class ScriptRequest(BaseModel):
    """Model for script processing request"""
    story_path: Optional[str] = Field(
        None,
        description="The path to the story file",
        example="data/story/short_story/Hills Like White Elephants by Ernest Hemingway.txt"
    )
    text_input: Optional[str] = Field(
        None,
        description="The story text content",
        example="The hills across the valley of the Ebro were long and white..."
    )
    split_dialogue: bool = Field(
        True,
        description="Whether to split dialogue and narration into separate lines for lines assigned to voice actors"
    )
    all_caps_to_proper: bool = Field(
        True,
        description="Whether to convert all-caps lines to proper capitalization"
    )
    book_id: Optional[str] = Field(
        None,
        description="The ID of the book this chapter belongs to. If provided, previous chapters' plots will be considered.",
        example="mobydick"
    )

class ScriptResponse(BaseModel):
    """Model for script processing response"""
    status: str = Field(
        ...,
        description="The status of the operation",
        example="success"
    )
    process_id: str = Field(
        ...,
        description="The process ID",
        example="hem101"
    )
    message: Optional[str] = Field(
        None,
        description="Optional message providing additional information",
        example="Processing completed successfully"
    )
    output_path: Optional[str] = Field(
        None,
        description="The path to the output file",
        example="data/process/hem101/plot.json"
    )

class PlotRequest(BaseModel):
    """Model for plot generation request"""
    story_path: Optional[str] = Field(
        None,
        description="The path to the story file",
        example="data/story/short_story/Hills Like White Elephants by Ernest Hemingway.txt"
    )
    text_input: Optional[str] = Field(
        None,
        description="The story text content",
        example="The hills across the valley of the Ebro were long and white..."
    )
    book_id: Optional[str] = Field(
        None,
        description="The ID of the book this chapter belongs to. If provided, previous chapters' plots will be considered.",
        example="mobydick"
    )

class CastRequest(BaseModel):
    """Model for cast assignment request"""
    book_id: Optional[str] = Field(
        None,
        description="The ID of the book this chapter belongs to. If provided, previous chapters' cast will be considered.",
        example="mobydick"
    )

class LineRequest(BaseModel):
    """Model for line processing request"""
    split_dialogue: bool = Field(
        True,
        description="Whether to split dialogue and narration into separate lines for lines assigned to voice actors"
    )
    all_caps_to_proper: bool = Field(
        True,
        description="Whether to convert all-caps lines to proper capitalization"
    ) 