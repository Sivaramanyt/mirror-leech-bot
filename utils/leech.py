import os
import asyncio
import logging
import aiohttp
import aiofiles
from typing import Optional, Dict, Any, Callable
from pyrogram.types import Message
from .helpers import get_readable_file_size, sanitize_filename
from .database import db
import time
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class LeechEngine:
    def __init__(self):
        self.active_downloads = {}
        self.executor = ThreadPoolExecutor(max_workers=3)
        
    async def leech_file(self, message: Message, url: str, filename: str = None, 
                        progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Main leech function for downloading files"""
        try:
            user_id = message.from_user.id
            
            # Create download directory
            download_dir = f"downloads/{user_id}"
            os.makedirs(download_dir, exist_ok=True)
            
            # Start download
            result = await self._download_file(url, download_dir, filename, user_id, progress_callback)
            
            if result['success']:
                # Log to database
                if db.enabled:
                    await db.log_download(user_id, result['filename'], result['size'], url)
                
                logger.info(f"✅ Leech completed for user {user_id}: {result['filename']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Leech error: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': None,
                'size': 0,
                'path': None
            }
    
    async def _download_file(self, url: str, download_dir: str, filename: str = None, 
                           user_id: int = 0, progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Download file with progress tracking"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return {
                            'success': False,
                            'error': f'HTTP {response.status}',
                            'filename': None,
                            'size': 0,
                            'path': None
                        }
                    
                    # Get filename and size
                    if not filename:
                        filename = self._extract_filename(response, url)
                    
                    filename = sanitize_filename(filename)
                    file_path = os.path.join(download_dir, filename)
                    
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    start_time = time.time()
                    
                    # Track download
                    self.active_downloads[user_id] = {
                        'filename': filename,
                        'total_size': total_size,
                        'downloaded': 0,
                        'start_time': start_time,
                        'speed': 0
                    }
                    
                    # Download with progress
                    async with aiofiles.open(file_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(8192):
                            await file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress
                            self.active_downloads[user_id]['downloaded'] = downloaded
                            
                            # Calculate speed
                            elapsed = time.time() - start_time
                            if elapsed > 0:
                                speed = downloaded / elapsed
                                self.active_downloads[user_id]['speed'] = speed
                            
                            # Progress callback
                            if progress_callback and downloaded % (1024 * 1024) == 0:  # Every MB
                                await progress_callback(downloaded, total_size, speed)
                    
                    # Remove from active downloads
                    if user_id in self.active_downloads:
                        del self.active_downloads[user_id]
                    
                    return {
                        'success': True,
                        'filename': filename,
                        'size': downloaded,
                        'path': file_path,
                        'download_time': time.time() - start_time
                    }
                    
        except Exception as e:
            # Remove from active downloads on error
            if user_id in self.active_downloads:
                del self.active_downloads[user_id]
            
            logger.error(f"❌ Download error: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': filename,
                'size': 0,
                'path': None
            }
    
    def _extract_filename(self, response, url: str) -> str:
        """Extract filename from response or URL"""
        # Try content-disposition header
        content_disposition = response.headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"\'')
            return filename
        
        # Extract from URL
        filename = url.split('/')[-1].split('?')[0]
        if filename and '.' in filename:
            return filename
        
        # Default filename
        return f"file_{int(time.time())}"
    
    def get_active_downloads(self) -> Dict[int, Dict[str, Any]]:
        """Get all active downloads"""
        return self.active_downloads.copy()
    
    def get_user_download(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get specific user's active download"""
        return self.active_downloads.get(user_id)
    
    async def cancel_download(self, user_id: int) -> bool:
        """Cancel user's active download"""
        if user_id in self.active_downloads:
            del self.active_downloads[user_id]
            logger.info(f"📛 Download cancelled for user {user_id}")
            return True
        return False

# Global leech engine instance
leech_engine = LeechEngine()
