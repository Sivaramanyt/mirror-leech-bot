import re
import time
import math
import asyncio
import aiohttp
import mimetypes
from typing import Tuple, Optional, Union
from urllib.parse import urlparse, unquote
from pathlib import Path

def get_readable_file_size(size_bytes: int) -> str:
    """Convert bytes to readable file size"""
    if size_bytes == 0:
        return "0B"

    size_name = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def get_readable_time(seconds: int) -> str:
    """Convert seconds to readable time format"""
    periods = [
        ('year', 60*60*24*365),
        ('month', 60*60*24*30),
        ('day', 60*60*24),
        ('hour', 60*60),
        ('minute', 60),
        ('second', 1)
    ]

    strings = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            if period_value == 1:
                strings.append(f"{period_value} {period_name}")
            else:
                strings.append(f"{period_value} {period_name}s")

    return ", ".join(strings[:2]) if strings else "0 seconds"

def get_progress_bar_string(current: int, total: int, bar_length: int = 10) -> str:
    """Generate progress bar string"""
    if total == 0:
        return "[" + "█" * bar_length + "]"

    percentage = current / total
    filled_length = int(bar_length * percentage)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    return f"[{bar}] {percentage:.1%}"

def format_progress_text(
    filename: str,
    current: int,
    total: int,
    start_time: float,
    status: str = "Downloading"
) -> str:
    """Format progress message text"""
    elapsed_time = time.time() - start_time

    if current > 0 and elapsed_time > 0:
        speed = current / elapsed_time
        eta = (total - current) / speed if speed > 0 else 0
    else:
        speed = 0
        eta = 0

    progress_bar = get_progress_bar_string(current, total)

    text = f"""
📁 <b>{filename[:50]}{'...' if len(filename) > 50 else ''}</b>

{progress_bar}

📊 <b>Progress:</b> {get_readable_file_size(current)} / {get_readable_file_size(total)}
⚡ <b>Speed:</b> {get_readable_file_size(int(speed))}/s
⏱️ <b>ETA:</b> {get_readable_time(int(eta))}
📈 <b>Status:</b> {status}
    """.strip()

    return text

def extract_filename_from_url(url: str) -> str:
    """Extract filename from URL"""
    parsed_url = urlparse(url)

    # Try to get filename from path
    filename = Path(unquote(parsed_url.path)).name

    if filename and filename != "/":
        return filename

    # Fallback to generic name
    return "unknown_file"

def get_mime_type(file_path: str) -> str:
    """Get MIME type of file"""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"

def is_supported_file(file_path: str, excluded_extensions: list = None) -> bool:
    """Check if file is supported (not in excluded extensions)"""
    if not excluded_extensions:
        return True

    file_extension = Path(file_path).suffix.lower()
    return file_extension not in excluded_extensions

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for file system"""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Ensure filename is not empty
    if not filename:
        filename = "unnamed_file"

    return filename

async def get_file_size_from_url(url: str, timeout: int = 10) -> Optional[int]:
    """Get file size from URL using HEAD request"""
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as session:
            async with session.head(url) as response:
                if response.status == 200:
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        return int(content_length)
    except Exception:
        pass

    return None

def extract_links_from_text(text: str) -> list:
    """Extract URLs from text"""
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    return url_pattern.findall(text)

def is_terabox_link(url: str) -> bool:
    """Check if URL is a Terabox link"""
    terabox_domains = [
        'terabox.com', 'nephobox.com', '4funbox.com', 'mirrobox.com',
        'momerybox.com', 'teraboxapp.com', '1024tera.com'
    ]

    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()

    return any(tb_domain in domain for tb_domain in terabox_domains)

def is_youtube_link(url: str) -> bool:
    """Check if URL is a YouTube link"""
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(?:https?://)?youtu\.be/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/channel/[\w-]+',
        r'(?:https?://)?(?:www\.)?youtube\.com/@[\w-]+',
    ]

    return any(re.match(pattern, url, re.IGNORECASE) for pattern in youtube_patterns)

def is_google_drive_link(url: str) -> bool:
    """Check if URL is a Google Drive link"""
    gd_patterns = [
        r'https://drive\.google\.com/file/d/([a-zA-Z0-9-_]+)',
        r'https://drive\.google\.com/open\?id=([a-zA-Z0-9-_]+)',
        r'https://drive\.google\.com/drive/folders/([a-zA-Z0-9-_]+)',
        r'https://drive\.google\.com/drive/u/\d+/folders/([a-zA-Z0-9-_]+)'
    ]

    return any(re.match(pattern, url, re.IGNORECASE) for pattern in gd_patterns)

def is_mega_link(url: str) -> bool:
    """Check if URL is a Mega link"""
    return bool(re.match(r'https://mega\.nz/', url, re.IGNORECASE))

def is_torrent_link(url: str) -> bool:
    """Check if URL is a torrent or magnet link"""
    return url.lower().startswith('magnet:') or url.lower().endswith('.torrent')

def extract_gd_id(url: str) -> Optional[str]:
    """Extract Google Drive file/folder ID from URL"""
    patterns = [
        r'https://drive\.google\.com/file/d/([a-zA-Z0-9-_]+)',
        r'https://drive\.google\.com/open\?id=([a-zA-Z0-9-_]+)',
        r'https://drive\.google\.com/drive/folders/([a-zA-Z0-9-_]+)',
        r'https://drive\.google\.com/drive/u/\d+/folders/([a-zA-Z0-9-_]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None

async def run_subprocess(command: list, timeout: int = 3600) -> Tuple[int, str, str]:
    """Run subprocess command asynchronously"""
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
        try:
            process.terminate()
            await process.wait()
        except:
            pass
        return -1, "", "Process timed out"

    except Exception as e:
        return -1, "", str(e)

def split_file_size(total_size: int, max_size: int) -> list:
    """Calculate file split sizes"""
    if total_size <= max_size:
        return [total_size]

    parts = math.ceil(total_size / max_size)
    part_size = total_size // parts
    sizes = [part_size] * (parts - 1)
    sizes.append(total_size - sum(sizes))

    return sizes

def format_task_info(task_info: dict) -> str:
    """Format task information for display"""
    name = task_info.get('name', 'Unknown')
    status = task_info.get('status', 'Unknown')
    progress = task_info.get('progress', 0)
    speed = task_info.get('speed', 0)
    eta = task_info.get('eta', 0)

    progress_bar = get_progress_bar_string(progress, 100)

    return f"""
📁 <b>{name[:30]}{'...' if len(name) > 30 else ''}</b>
{progress_bar}
📊 {progress}% • ⚡ {get_readable_file_size(int(speed))}/s
⏱️ ETA: {get_readable_time(int(eta))} • 📈 {status}
    """.strip()
