import re
import logging
from typing import Optional, Dict, Any
import requests
import httpx
import ujson as json
import validators
from aiolimiter import AsyncLimiter
from .config import TERABOX_API_BASE, HEADERS

logger = logging.getLogger(__name__)

# Rate limiter for API requests
api_limiter = AsyncLimiter(max_rate=10, time_period=60)

async def extract_terabox_info(url: str) -> Optional[Dict[str, Any]]:
    """Enhanced async file info extraction"""
    try:
        async with api_limiter:
            # Validate URL first
            if not validators.url(url):
                logger.warning(f"Invalid URL format: {url}")
                return None
            
            # Extract shorturl patterns
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
            
            shorturl = None
            for pattern in patterns:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    shorturl = match.group(1)
                    logger.info(f"✅ Extracted shorturl: {shorturl}")
                    break
            
            if not shorturl:
                logger.error("❌ No shorturl found in URL")
                return None
            
            # Make async API request
            api_url = f"{TERABOX_API_BASE}?shorturl={shorturl}&root=1"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api_url, headers=HEADERS)
                response.raise_for_status()
                
                if response.status_code == 200:
                    data = json.loads(response.text)
                    
                    if data.get('errno') == 0 and data.get('list'):
                        file_info = data['list'][0]
                        
                        result = {
                            'filename': file_info.get('server_filename', 'Unknown'),
                            'size': file_info.get('size', 0),
                            'download_url': file_info.get('dlink', ''),
                            'thumbnail': file_info.get('thumbs', {}).get('url3', ''),
                            'category': file_info.get('category', 0),
                            'isdir': file_info.get('isdir', 0),
                            'fs_id': file_info.get('fs_id', ''),
                            'md5': file_info.get('md5', '')
                        }
                        
                        logger.info(f"✅ File info extracted: {result['filename']}")
                        return result
                    else:
                        logger.error(f"❌ API returned error: {data.get('errmsg', 'Unknown')}")
                        return None
                        
    except Exception as e:
        logger.error(f"❌ Error extracting Terabox info: {e}")
        return None

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

def get_file_type_emoji(filename: str) -> str:
    """Get appropriate emoji based on file type"""
    filename_lower = filename.lower()
    
    if any(ext in filename_lower for ext in ['.mp4', '.avi', '.mkv', '.mov']):
        return "🎥"
    elif any(ext in filename_lower for ext in ['.mp3', '.wav', '.flac']):
        return "🎵"
    elif any(ext in filename_lower for ext in ['.jpg', '.jpeg', '.png', '.gif']):
        return "🖼️"
    elif any(ext in filename_lower for ext in ['.zip', '.rar', '.7z']):
        return "📦"
    elif any(ext in filename_lower for ext in ['.pdf', '.doc', '.txt']):
        return "📄"
    else:
        return "📁"
