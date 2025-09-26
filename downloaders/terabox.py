import os
import re
import aiohttp
import asyncio
import logging
from typing import Optional, Callable
from urllib.parse import unquote
from utils.helpers import sanitize_filename, get_readable_file_size

logger = logging.getLogger(__name__)

class TeraboxDownloader:
    def __init__(self):
        self.session = None
        self.base_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(
                headers=self.base_headers,
                timeout=timeout
            )
        return self.session
    
    async def extract_file_info(self, url: str) -> dict:
        """Extract file information from Terabox URL"""
        try:
            # Clean the URL
            url = url.strip()
            if 'terasharelink.com' in url:
                return await self.get_direct_link_info(url)
            
            # For now, return basic info (you can enhance this)
            return {
                'filename': self.generate_video_filename(url),
                'download_url': url,
                'file_size': 0,
                'file_type': 'video'
            }
            
        except Exception as e:
            logger.error(f"Error extracting Terabox info: {e}")
            return {'error': str(e)}
    
    async def get_direct_link_info(self, url: str) -> dict:
        """Get info for direct terasharelink.com URLs"""
        try:
            session = await self.get_session()
            async with session.head(url, allow_redirects=True) as response:
                if response.status == 200:
                    # Extract filename from URL or headers
                    filename = self.extract_filename_from_headers(response, url)
                    
                    # Get file size
                    file_size = 0
                    if 'content-length' in response.headers:
                        file_size = int(response.headers['content-length'])
                    
                    return {
                        'filename': filename,
                        'download_url': url,
                        'file_size': file_size,
                        'file_type': self.get_file_type_from_name(filename)
                    }
                else:
                    raise Exception(f"Failed to access file: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error getting direct link info: {e}")
            return {'error': str(e)}
    
    def extract_filename_from_headers(self, response, url: str) -> str:
        """Extract filename from response headers or URL"""
        try:
            # Try Content-Disposition header first
            if 'content-disposition' in response.headers:
                content_disp = response.headers['content-disposition']
                filename_match = re.search(r'filename[*]?=([^;]+)', content_disp)
                if filename_match:
                    filename = filename_match.group(1).strip('"\'')
                    return sanitize_filename(unquote(filename))
            
            # Try to extract from URL path
            url_parts = url.split('/')
            if url_parts:
                potential_filename = url_parts[-1].split('?')[0]
                if '.' in potential_filename and len(potential_filename) > 3:
                    return sanitize_filename(unquote(potential_filename))
            
            # Generate a video filename with proper extension
            return self.generate_video_filename(url)
            
        except Exception as e:
            logger.error(f"Error extracting filename: {e}")
            return self.generate_video_filename(url)
    
    def generate_video_filename(self, url: str) -> str:
        """Generate a proper video filename with extension"""
        # Extract any ID from URL for uniqueness
        url_id = ""
        id_match = re.search(r'([A-Za-z0-9_-]{10,})', url)
        if id_match:
            url_id = id_match.group(1)[:12]  # Limit length
        else:
            url_id = str(hash(url) % 100000)
        
        return f"terabox_video_{url_id}.mp4"
    
    def get_file_type_from_name(self, filename: str) -> str:
        """Get file type from filename"""
        ext = os.path.splitext(filename)[1].lower()
        
        video_exts = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
        audio_exts = {'.mp3', '.m4a', '.flac', '.wav', '.aac', '.ogg'}
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        if ext in video_exts:
            return 'video'
        elif ext in audio_exts:
            return 'audio'  
        elif ext in image_exts:
            return 'image'
        else:
            return 'document'
    
    async def download(self, url: str, progress_callback: Optional[Callable] = None, task_id: str = None) -> Optional[str]:
        """Download file from Terabox URL"""
        try:
            logger.info(f"Starting Terabox download: {url}")
            
            # Get file information
            file_info = await self.extract_file_info(url)
            if 'error' in file_info:
                raise Exception(file_info['error'])
            
            filename = file_info['filename']
            download_url = file_info['download_url']
            
            # Ensure proper file extension for videos
            if not os.path.splitext(filename)[1]:
                filename += '.mp4'  # Default to mp4 for videos
            
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
                    raise Exception(f"Download failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"Terabox download error: {e}")
            raise e
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
                    
