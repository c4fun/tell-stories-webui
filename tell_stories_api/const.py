import os
from typing import List
from dotenv import load_dotenv
load_dotenv()

TELL_STORIES_API_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Base Voice Actor database path
VA_DATABASE_PATH = os.path.join(TELL_STORIES_API_ROOT, "data", "va")

def get_all_va_paths() -> List[str]:
    """Get all VA database paths from environment variables and base path."""
    va_paths = [VA_DATABASE_PATH]  # Always include the base path
    
    # Collect additional VA folders from environment variables
    env_vars = [key for key in os.environ.keys() if key.startswith('VA_FOLDER_')]
    for env_var in sorted(env_vars):  # Sort to ensure consistent order
        extra_path = os.environ.get(env_var)
        if extra_path:
            # If path is relative, make it absolute relative to TELL_STORIES_API_ROOT
            if not os.path.isabs(extra_path):
                extra_path = os.path.join(TELL_STORIES_API_ROOT, extra_path)
            va_paths.append(extra_path)
    
    return va_paths

# List of all VA database paths
VA_DATABASE_PATHS = get_all_va_paths()
