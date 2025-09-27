import logging
import yt_dlp
import requests
from typing import Dict, Any, Optional
from .helpers import sanitize_filename, get_readable_file_size
import os
import asyncio

logger = logging.getLogger(__name__)

class UniversalDownloader:
    def __init__(self):
        self.yt_dlp_options = {
            'format': 'best[height<=1080]',
            'outtmpl': 'downloads/%(uploader)s - %(title)s.%(ext)s',
            'writeinfojson': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
        }
    
    async def get_download_info(self, url: str) -> Dict[str, Any]:
        """Get information about downloadable content"""
        try:
            # Try yt-dlp first (supports 900+ sites)
            info = await self._get_ytdlp_info(url)
            if info['success']:
                return info
            
            # Try direct HTTP for other links
            info = await self._get_http_info(url)
            return info
            
        except Exception as e:
            logger.error(f"❌ Error getting download info: {e}")
            return {
                'success': False,
                'error': str(e),
                'title': None,
                'duration': None,
                'size': None,
                'formats': []
            }
    
    async def _get_ytdlp_info(self, url: str) -> Dict[str, Any]:
        """Get info using yt-dlp"""
        try:
            def extract_info():
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    return ydl.extract_info(url, download=False)
            
            # Run in thread to avoid blocking
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, extract_info)
            
            if info:
                formats = []
                if 'formats' in info:
                    for fmt in info['formats'][:5]:  # Top 5 formats
                        formats.append({
                            'format_id': fmt.get('format_id', ''),
                            'ext': fmt.get('ext', 'mp4'),
                            'quality': fmt.get('format_note', 'Unknown'),
                            'filesize': fmt.get('filesize', 0)
                        })
                
                return {
                    'success': True,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'formats': formats,
                    'thumbnail': info.get('thumbnail', ''),
                    'description': info.get('description', '')[:200] + '...' if info.get('description') else ''
                }
            
            return {'success': False, 'error': 'No info extracted'}
            
        except Exception as e:
            logger.error(f"❌ yt-dlp error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_http_info(self, url: str) -> Dict[str, Any]:
        """Get info for direct HTTP links"""
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)
            
            if response.status_code == 200:
                content_length = response.headers.get('content-length', 0)
                content_type = response.headers.get('content-type', 'application/octet-stream')
                filename = url.split('/')[-1].split('?')[0]
                
                return {
                    'success': True,
                    'title': filename,
                    'size': int(content_length) if content_length else 0,
                    'content_type': content_type,
                    'filename': filename,
                    'formats': [{
                        'format_id': 'direct',
                        'ext': filename.split('.')[-1] if '.' in filename else 'bin',
                        'quality': 'Direct',
                        'filesize': int(content_length) if content_length else 0
                    }]
                }
            
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
        except Exception as e:
            logger.error(f"❌ HTTP info error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def download_with_ytdlp(self, url: str, download_dir: str, format_id: str = None) -> Dict[str, Any]:
        """Download using yt-dlp"""
        try:
            options = self.yt_dlp_options.copy()
            options['outtmpl'] = os.path.join(download_dir, '%(title)s.%(ext)s')
            
            if format_id:
                options['format'] = format_id
            
            def download():
                with yt_dlp.YoutubeDL(options) as ydl:
                    info = ydl.extract_info(url, download=True)
                    return info
            
            # Run in thread
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, download)
            
            if info:
                filename = ydl.prepare_filename(info)
                return {
                    'success': True,
                    'filename': os.path.basename(filename),
                    'path': filename,
                    'title': info.get('title', 'Unknown'),
                    'size': os.path.getsize(filename) if os.path.exists(filename) else 0
                }
            
            return {'success': False, 'error': 'Download failed'}
            
        except Exception as e:
            logger.error(f"❌ yt-dlp download error: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_supported_sites(self) -> list:
        """Get list of supported sites"""
        try:
            return [
                "YouTube", "Instagram", "Twitter", "TikTok", "Facebook",
                "Vimeo", "Dailymotion", "Reddit", "Pinterest", "LinkedIn",
                "Twitch", "SoundCloud", "Bandcamp", "Archive.org",
                "And 900+ more sites via yt-dlp"
            ]
        except:
            return ["900+ sites via yt-dlp"]

# Global downloader instance
universal_downloader = UniversalDownloader()
