import os
import re
import asyncio
import logging
import aiohttp
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

async def get_file_size_from_url(url: str) -> int:
    """Get file size from URL using HEAD request"""
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.head(url, allow_redirects=True) as response:
                if response.status == 200:
                    content_length = response.headers.get('content-length')
                    if content_length:
                        return int(content_length)
                    else:
                        # Fallback: try GET request with range
                        async with session.get(url, headers={'Range': 'bytes=0-1'}) as get_response:
                            content_range = get_response.headers.get('content-range')
                            if content_range and '/' in content_range:
                                total_size = content_range.split('/')[-1]
                                if total_size.isdigit():
                                    return int(total_size)
                return 0
    except Exception as e:
        logger.error(f"Error getting file size from {url}: {e}")
        return 0

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

def is_supported_file_type(filename: str) -> bool:
    """Check if file type is supported"""
    supported_extensions = {
        # Video
        '.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp',
        # Audio  
        '.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg',
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
        # Documents
        '.pdf', '.doc', '.docx', '.txt', '.zip', '.rar', '.7z'
    }
    
    ext = os.path.splitext(filename)[1].lower()
    return ext in supported_extensions

def get_file_type(filename: str) -> str:
    """Get file type category"""
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
    audio_extensions = {'.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg'}
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    ext = os.path.splitext(filename)[1].lower()
    
    if ext in video_extensions:
        return 'video'
    elif ext in audio_extensions:
        return 'audio'
    elif ext in image_extensions:
        return 'image'
    else:
        return 'document'
