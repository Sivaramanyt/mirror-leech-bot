import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def get_readable_file_size(size_bytes: int) -> str:
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Simple filename sanitization"""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # Limit length
    if len(filename) > max_length:
        filename = filename[:max_length]
    
    return filename.strip()

def create_safe_slug(text: str, max_length: int = 50) -> str:
    """Create a safe slug from text - simplified version"""
    # Simple slug creation without external library
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug[:max_length].strip('-')
    
