import aiohttp
import re
import logging
from typing import Optional, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class TeraboxDownloader:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.terabox.com/',
        }
    
    def extract_surl(self, url: str) -> Optional[str]:
        """Extract surl from Terabox URL"""
        patterns = [
            r'terabox\.com/s/([a-zA-Z0-9_-]+)',
            r'terasharelink\.com/s/([a-zA-Z0-9_-]+)',
            r'1024tera\.com/s/([a-zA-Z0-9_-]+)',
            r'nephobox\.com/s/([a-zA-Z0-9_-]+)',
            r'4funbox\.com/s/([a-zA-Z0-9_-]+)',
            r'mirrobox\.com/s/([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    async def get_file_info(self, url: str) -> Dict[str, Any]:
        """Get file information from Terabox"""
        try:
            surl = self.extract_surl(url)
            if not surl:
                return {"success": False, "error": "Invalid URL format"}
            
            async with aiohttp.ClientSession() as session:
                # Get file info from Terabox API
                api_url = f"https://www.terabox.com/api/shorturlinfo?shorturl={surl}&root=1"
                
                async with session.get(api_url, headers=self.headers) as response:
                    if response.status != 200:
                        return {"success": False, "error": f"HTTP {response.status}"}
                    
                    data = await response.json()
                    
                    if data.get("errno") != 0:
                        return {"success": False, "error": "File not found or private"}
                    
                    files = data.get("list", [])
                    if not files:
                        return {"success": False, "error": "No files found"}
                    
                    file_info = files[0]  # Get first file
                    
                    return {
                        "success": True,
                        "filename": file_info.get("server_filename", "unknown"),
                        "size": file_info.get("size", 0),
                        "download_url": file_info.get("dlink", ""),
                        "file_type": self.get_file_type(file_info.get("server_filename", "")),
                        "created_time": file_info.get("server_ctime", 0)
                    }
                    
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return {"success": False, "error": str(e)}
    
    def get_file_type(self, filename: str) -> str:
        """Get file type emoji"""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        
        if ext in ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv']:
            return "🎥 Video"
        elif ext in ['mp3', 'wav', 'flac', 'aac']:
            return "🎵 Audio"
        elif ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            return "🖼️ Image"
        elif ext in ['zip', 'rar', '7z', 'tar']:
            return "📦 Archive"
        elif ext in ['pdf', 'doc', 'docx', 'txt']:
            return "📄 Document"
        else:
            return "📁 File"
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.2f} {size_names[i]}"

# Global instance
terabox = TeraboxDownloader()
                    
