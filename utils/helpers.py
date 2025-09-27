import re
import logging
from typing import Optional, List, Tuple
from urllib.parse import urlparse
import validators
from python_slugify import slugify
import time

logger = logging.getLogger(__name__)

def get_readable_file_size(size_bytes: int) -> str:
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB", "EB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    if i <= 1:  # B, KB
        return f"{size_bytes:.0f} {size_names[i]}"
    else:  # MB, GB, TB, etc.
        return f"{size_bytes:.2f} {size_names[i]}"

def is_supported_url(url: str) -> bool:
    """Enhanced URL validation for supported platforms"""
    if not validators.url(url):
        return False
    
    supported_domains = [
        "terabox", "nephobox", "4funbox", "mirrobox", 
        "momerybox", "teraboxapp", "1024tera", "gibibox",
        "goaibox", "terasharelink", "teraboxlink",
        "freeterabox", "1024terabox", "teraboxshare"
    ]
    
    url_lower = url.lower()
    return any(domain in url_lower for domain in supported_domains)

def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Enhanced filename sanitization"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = max_length - len(ext) - 1 if ext else max_length
        filename = name[:max_name_length] + ('.' + ext if ext else '')
    
    return filename.strip()

def extract_shorturl_from_url(url: str) -> Optional[str]:
    """Extract shorturl from Terabox URL"""
    patterns = [
        r'terabox\.com/s/([a-zA-Z0-9_-]+)',
        r'nephobox\.com/s/([a-zA-Z0-9_-]+)',
        r'4funbox\.com/s/([a-zA-Z0-9_-]+)',
        r'mirrobox\.com/s/([a-zA-Z0-9_-]+)',
        r'momerybox\.com/s/([a-zA-Z0-9_-]+)',
        r'teraboxapp\.com/s/([a-zA-Z0-9_-]+)',
        r'1024tera\.com/s/([a-zA-Z0-9_-]+)',
        r'gibibox\.com/s/([a-zA-Z0-9_-]+)',
        r'goaibox\.com/s/([a-zA-Z0-9_-]+)',
        r'terasharelink\.com/s/([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None

def get_file_type_info(filename: str, category: int = 0) -> Tuple[str, str]:
    """Get file type emoji and category name"""
    filename_lower = filename.lower()
    
    file_types = {
        'video': (['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'], "🎥", "Video"),
        'audio': (['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'], "🎵", "Audio"),
        'image': (['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'], "🖼️", "Image"),
        'document': (['.pdf', '.doc', '.docx', '.txt', '.rtf'], "📄", "Document"),
        'archive': (['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'], "📦", "Archive"),
        'executable': (['.exe', '.apk', '.deb', '.rpm', '.dmg'], "⚙️", "Executable"),
    }
    
    for type_name, (extensions, emoji, category_name) in file_types.items():
        if any(ext in filename_lower for ext in extensions):
            return emoji, category_name
    
    return "📁", "File"

def validate_terabox_url(url: str) -> Tuple[bool, str]:
    """Validate Terabox URL with detailed error messages"""
    if not url:
        return False, "URL is empty"
    
    if not validators.url(url):
        return False, "Invalid URL format"
    
    if not is_supported_url(url):
        return False, "Unsupported platform. Please use a Terabox variant URL."
    
    shorturl = extract_shorturl_from_url(url)
    if not shorturl:
        return False, "Could not extract shorturl from URL"
    
    if len(shorturl) < 5:
        return False, "Shorturl seems too short to be valid"
    
    return True, "Valid Terabox URL"

def format_duration(seconds: int) -> str:
    """Format duration in human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def create_safe_slug(text: str, max_length: int = 50) -> str:
    """Create a safe slug from text"""
    return slugify(text, max_length=max_length, word_boundary=True)

class ProgressTracker:
    """Progress tracking utility"""
    
    def __init__(self):
        self.active_downloads = {}
    
    def start_download(self, user_id: int, filename: str, total_size: int):
        """Start tracking a download"""
        self.active_downloads[user_id] = {
            'filename': filename,
            'total_size': total_size,
            'downloaded': 0,
            'start_time': time.time(),
            'last_update': time.time()
        }
    
    def update_progress(self, user_id: int, downloaded: int):
        """Update download progress"""
        if user_id in self.active_downloads:
            self.active_downloads[user_id]['downloaded'] = downloaded
            self.active_downloads[user_id]['last_update'] = time.time()
    
    def get_progress(self, user_id: int) -> Optional[dict]:
        """Get current progress for a user"""
        return self.active_downloads.get(user_id)
    
    def complete_download(self, user_id: int):
        """Mark download as complete"""
        if user_id in self.active_downloads:
            del self.active_downloads[user_id]
    
    def get_all_active(self) -> dict:
        """Get all active downloads"""
        return self.active_downloads.copy()
