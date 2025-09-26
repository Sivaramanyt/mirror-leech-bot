import os
import re
import asyncio
import logging
from typing import Union

logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    
    # Remove extra spaces and dots
    filename = re.sub(r'\s+', ' ', filename).strip()
    filename = filename.strip('.')
    
    # Ensure filename is not empty
    if not filename:
        filename = "untitled"
    
    # Limit filename length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    
    return filename

def get_readable_file_size(size_bytes: int) -> str:
    """Convert bytes to readable file size format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_progress_bar_string(percentage: float) -> str:
    """Generate a progress bar string with percentage"""
    try:
        # Ensure percentage is between 0 and 100
        percentage = max(0, min(100, float(percentage)))
        
        # Calculate filled blocks (10 total blocks)
        filled_blocks = int(percentage / 10)
        empty_blocks = 10 - filled_blocks
        
        # Create progress bar
        filled = "█" * filled_blocks
        empty = "░" * empty_blocks
        
        return f"[{filled}{empty}] {percentage:.1f}%"
        
    except Exception as e:
        logger.error(f"Progress bar error: {e}")
        return f"[░░░░░░░░░░] 0.0%"

def extract_filename_from_url(url: str) -> str:
    """Extract filename from URL"""
    try:
        # Extract filename from URL
        filename = url.split('/')[-1].split('?')[0]
        
        if not filename or '.' not in filename:
            filename = f"file_{hash(url) % 10000}"
            
        return sanitize_filename(filename)
        
    except Exception:
        return f"download_{hash(url) % 10000}"

async def run_command(command: list, timeout: int = 300) -> tuple:
    """Run shell command asynchronously"""
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(), 
            timeout=timeout
        )
        
        return process.returncode, stdout.decode(), stderr.decode()
        
    except asyncio.TimeoutError:
        return 1, "", "Command timeout"
    except Exception as e:
        return 1, "", str(e)

def format_duration(seconds: int) -> str:
    """Format duration in seconds to readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    
