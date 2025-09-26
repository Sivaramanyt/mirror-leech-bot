import asyncio
import os
import logging
from typing import Optional, Callable, Dict
import yt_dlp
from utils.helpers import sanitize_filename, get_readable_file_size

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    def __init__(self):
        self.ydl_opts = {
            'format': 'best[height<=720][ext=mp4]/best[ext=mp4]/best',
            'outtmpl': '/tmp/downloads/%(title)s.%(ext)s',
            'noplaylist': True,
            'extractaudio': False,
            'audioformat': 'mp3',
            'embed_subs': True,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': True,
            'no_warnings': True,
            'quiet': True,
            'noprogress': True
        }

    async def get_video_info(self, url: str) -> Optional[Dict]:
        """Get video information"""
        try:
            loop = asyncio.get_event_loop()

            def extract_info():
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    return ydl.extract_info(url, download=False)

            info = await loop.run_in_executor(None, extract_info)

            if info:
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'size': info.get('filesize') or info.get('filesize_approx', 0)
                }
            return None

        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            return None

    async def download(self, url: str, progress_callback: Optional[Callable] = None, task_id: str = None) -> Optional[str]:
        """Download video using yt-dlp"""
        try:
            os.makedirs('/tmp/downloads', exist_ok=True)

            # Progress hook for yt-dlp
            def progress_hook(d):
                if d['status'] == 'downloading':
                    downloaded = d.get('downloaded_bytes', 0)
                    total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)

                    if progress_callback and task_id and total > 0:
                        asyncio.create_task(progress_callback(downloaded, total, task_id))

            ydl_opts = self.ydl_opts.copy()
            ydl_opts['progress_hooks'] = [progress_hook]

            loop = asyncio.get_event_loop()

            def download_video():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    if info:
                        return ydl.prepare_filename(info)
                return None

            filename = await loop.run_in_executor(None, download_video)

            if filename and os.path.exists(filename):
                return filename
            else:
                logger.error("Download failed or file not found")
                return None

        except Exception as e:
            logger.error(f"YouTube download error: {e}")
            return None
