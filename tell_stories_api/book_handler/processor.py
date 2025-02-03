from pathlib import Path
import json
from typing import Dict, Any
from tell_stories_api.logs import logger
# Constants
BOOK_DATA_DIR = Path("data/book")
PROCESS_DATA_DIR = Path("data/process")

def ensure_book_dir() -> None:
    """Ensure the main book data directory exists"""
    BOOK_DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_book_dir(book_id: str) -> Path:
    """Get the directory path for a specific book"""
    return BOOK_DATA_DIR / book_id

def get_book_path(book_id: str) -> Path:
    """Get the full path for a book's JSON file"""
    return get_book_dir(book_id) / "book.json"

def get_process_dir(project_id: str) -> Path:
    """Get the directory path for a specific project's process data"""
    return PROCESS_DATA_DIR / project_id

def read_plot_file(project_id: str) -> Dict[str, Any]:
    """Read plot data from plot.json"""
    plot_path = get_process_dir(project_id) / "plot.json"
    if not plot_path.exists():
        raise FileNotFoundError(f"Plot file not found for project {project_id}")
    with open(plot_path, 'r') as f:
        return json.load(f)

def read_cast_file(project_id: str) -> Dict[str, Any]:
    """Read cast data from cast.json"""
    cast_path = get_process_dir(project_id) / "cast.json"
    if not cast_path.exists():
        raise FileNotFoundError(f"Cast file not found for project {project_id}")
    with open(cast_path, 'r') as f:
        return json.load(f)

def ensure_book_folder(book_id: str) -> None:
    """Ensure the specific book's directory exists"""
    book_dir = get_book_dir(book_id)
    book_dir.mkdir(parents=True, exist_ok=True)

def read_book_file(book_id: str) -> Dict[str, Any]:
    """Read book data from file"""
    book_path = get_book_path(book_id)
    with open(book_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_book_file(book_id: str, book_data: Dict[str, Any]) -> None:
    """Write book data to file"""
    ensure_book_folder(book_id)  # Ensure the book's directory exists
    book_path = get_book_path(book_id)
    with open(book_path, 'w', encoding='utf-8') as f:
        json.dump(book_data, f, indent=4, ensure_ascii=False)

def delete_book_file(book_id: str) -> None:
    """Delete book file and its directory"""
    book_dir = get_book_dir(book_id)
    book_path = get_book_path(book_id)
    
    # First remove the book.json file
    if book_path.exists():
        book_path.unlink()
    
    # Then remove the book directory if it's empty
    if book_dir.exists() and not any(book_dir.iterdir()):
        book_dir.rmdir()

def book_exists(book_id: str) -> bool:
    """Check if book file exists"""
    return get_book_path(book_id).exists() 