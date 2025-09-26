import os
import logging

logger = logging.getLogger(__name__)

def get_readable_file_size(size_bytes):
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0B"
    size_name = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_name) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_name[i]}"

def is_supported_url(url):
    """Check if URL is supported"""
    supported_domains = [
        "terabox", "nephobox", "4funbox", "mirrobox", 
        "momerybox", "teraboxapp", "1024tera", "gibibox",
        "goaibox", "terasharelink", "teraboxlink",
        "freeterabox", "1024terabox", "teraboxshare"
    ]
    
    return any(domain in url.lower() for domain in supported_domains)

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename
    
