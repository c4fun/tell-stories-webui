import tiktoken
from typing import List
from tell_stories_api.logs import logger
import time

text = """
This is an example text.
"""

def count_tokens(text: str) -> int:
    """
    Count the number of tokens in a text using tiktoken's cl100k_base encoder.
    
    Args:
        text (str): The input text to count tokens for
        
    Returns:
        int: The number of tokens in the text
    """
    # Use cl100k_base encoder (used by Claude and GPT-4)
    encoding = tiktoken.get_encoding("cl100k_base")
    
    # Count tokens
    token_count = len(encoding.encode(text))
    
    return token_count

def log_execution_time(func):
    """
    Decorator to log execution time of functions.
    
    Args:
        func: The function to be timed
        
    Returns:
        wrapper: The wrapped function with timing
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # Get the size of the first argument (assuming it's the text)
            input_size = len(args[0]) if args else 0
            # Get the number of chunks in the result (assuming it returns a list)
            num_chunks = len(result) if isinstance(result, list) else 0
            
            logger.warning(
                f"{func.__name__} took {execution_time:.2f} seconds to process "
                f"{input_size} characters into {num_chunks} chunks"
            )
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.warning(f"{func.__name__} failed after {execution_time:.2f} seconds: {str(e)}")
            raise
    return wrapper

@log_execution_time
def split_text_by_tokens(text: str, max_tokens: int) -> List[str]:
    """
    Split text into chunks that don't exceed max_tokens.
    
    Args:
        text (str): Text to split
        max_tokens (int): Maximum tokens per chunk
        
    Returns:
        List[str]: List of text chunks
    """
    token_count = count_tokens(text)
    if token_count <= max_tokens:
        return [text]
        
    # Calculate number of splits needed
    num_splits = (token_count // max_tokens) + 1
    
    # Split text into roughly equal chunks by newlines
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    for paragraph in paragraphs:
        para_tokens = count_tokens(paragraph)
        if current_tokens + para_tokens > max_tokens:
            # Save current chunk and start new one
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
            current_chunk = [paragraph]
            current_tokens = para_tokens
        else:
            current_chunk.append(paragraph)
            current_tokens += para_tokens
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
        
    return chunks

if __name__ == "__main__":
    token_count = count_tokens(text)
    print(f"Token count: {token_count}")