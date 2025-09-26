# downloaders/terabox.py - BASED ON OFFICIAL anasty17 IMPLEMENTATION

import os
import aiohttp
import asyncio
import logging
from typing import Optional, Callable
from urllib.parse import quote
from utils.helpers import sanitize_filename, get_readable_file_size

logger = logging.getLogger(__name__)

class TeraboxDownloader:
    def __init__(self):
        self.session = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        self.api_url = "https://wdzone-terabox-api.vercel.app/api"
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": self.user_agent},
                timeout=timeout
            )
        return self.session
    
    def is_supported_domain(self, url: str) -> bool:
        """Check if URL is from supported Terabox domains"""
        supported_domains = [
            "terabox.com", "nephobox.com", "4funbox.com", "mirrobox.com",
            "momerybox.com", "teraboxapp.com", "1024tera.com", "terabox.app",
            "gibibox.com", "goaibox.com", "terasharelink.com", "teraboxlink.com",
            "freeterabox.com", "1024terabox.com", "teraboxshare.com", 
            "terafileshare.com", "terabox.club"
        ]
        return any(domain in url for domain in supported_domains)
    
    async def extract_file_info(self, url: str) -> dict:
        """Extract file information from Terabox URL using official API"""
        try:
            # If already a direct file link, return as-is
            if "/file/" in url:
                return {"single_url": url, "filename": "terabox_file.mp4"}
            
            # Use official API (same as anasty17)
            api_request_url = f"{self.api_url}?url={quote(url)}"
            session = await self.get_session()
            
            async with session.get(api_request_url) as response:
                if response.status != 200:
                    raise Exception(f"API request failed with status {response.status}")
                
                req = await response.json()
            
            # Process API response (same logic as official)
            details = {"contents": [], "title": "", "total_size": 0}
            
            if "✅ Status" not in req:
                raise Exception("File not found in API response!")
            
            # Extract files from API response
            for data in req["📜 Extracted Info"]:
                # Preserve original filename from API
                original_filename = data["📂 Title"]
                
                # Ensure video files have proper extension
                if not self.has_video_extension(original_filename):
                    original_filename += ".mp4"
                
                item = {
                    "path": "",
                    "filename": sanitize_filename(original_filename),
                    "url": data["🔽 Direct Download Link"],
                }
                details["contents"].append(item)
                
                # Handle file size
                size_str = (data["📏 Size"]).replace(" ", "")
                try:
                    size = self.parse_file_size(size_str)
                    details["total_size"] += size
                except:
                    details["total_size"] += 0
            
            # Set folder/file title
            details["title"] = req["📜 Extracted Info"][0]["📂 Title"]
            
            # Return single URL for single files, full details for folders
            if len(details["contents"]) == 1:
                return {
                    "single_url": details["contents"][0]["url"],
                    "filename": details["contents"][0]["filename"],
                    "title": details["title"]
                }
            return details
            
        except Exception as e:
            logger.error(f"Error extracting Terabox info: {e}")
            raise Exception(f"Terabox API error: {str(e)}")
    
    def has_video_extension(self, filename: str) -> bool:
        """Check if filename has video extension"""
        video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
        ext = os.path.splitext(filename.lower())[1]
        return ext in video_extensions
    
    def parse_file_size(self, size_str: str) -> int:
        """Parse file size string to bytes"""
        size_str = size_str.upper().replace(" ", "")
        
        if "KB" in size_str:
            return int(float(size_str.replace("KB", "")) * 1024)
        elif "MB" in size_str:
            return int(float(size_str.replace("MB", "")) * 1024 * 1024)
        elif "GB" in size_str:
            return int(float(size_str.replace("GB", "")) * 1024 * 1024 * 1024)
        elif "TB" in size_str:
            return int(float(size_str.replace("TB", "")) * 1024 * 1024 * 1024 * 1024)
        else:
            return int(size_str.replace("B", "")) if size_str.replace("B", "").isdigit() else 0
    
    async def download(self, url: str, progress_callback: Optional[Callable] = None, task_id: str = None) -> Optional[str]:
        """Download file from Terabox URL"""
        try:
            logger.info(f"Starting Terabox download: {url}")
            
            # Validate URL
            if not self.is_supported_domain(url):
                raise Exception("Unsupported Terabox domain")
            
            # Get file information using official API method
            file_info = await self.extract_file_info(url)
            
            if "single_url" in file_info:
                # Single file download
                download_url = file_info["single_url"]
                filename = file_info["filename"]
            else:
                # Multiple files - download first one for now
                if not file_info["contents"]:
                    raise Exception("No files found in folder")
                
                download_url = file_info["contents"][0]["url"]
                filename = file_info["contents"][0]["filename"]
            
            # Ensure filename has extension
            if not os.path.splitext(filename)[1]:
                filename += '.mp4'
            
            # Create download path
            download_path = os.path.join('/tmp', filename)
            
            # Download the file
            session = await self.get_session()
            async with session.get(download_url) as response:
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    with open(download_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Progress callback
                            if progress_callback and total_size > 0:
                                try:
                                    await progress_callback(downloaded, total_size, task_id)
                                except:
                                    pass
                    
                    logger.info(f"✅ Downloaded: {filename} ({get_readable_file_size(downloaded)})")
                    return download_path
                else:
                    raise Exception(f"Download failed: HTTP {response.status}")
                    
        except Exception as e:
            logger.error(f"Terabox download error: {e}")
            raise e
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
    
