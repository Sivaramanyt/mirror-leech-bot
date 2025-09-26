import asyncio
import aiohttp
import os
import logging
from typing import Optional, Callable
from utils.helpers import sanitize_filename, extract_filename_from_url, get_file_size_from_url

logger = logging.getLogger(__name__)

class DirectDownloader:
    def __init__(self):
        self.session = None

    async def create_session(self):
        """Create aiohttp session"""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=3600)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; bot/1.0)'}
            )

    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def download(self, url: str, progress_callback: Optional[Callable] = None, task_id: str = None) -> Optional[str]:
        """Download file from direct URL"""
        try:
            await self.create_session()

            # Get file info
            filename = extract_filename_from_url(url)
            filename = sanitize_filename(filename)

            # Get file size
            file_size = await get_file_size_from_url(url) or 0

            os.makedirs('/tmp/downloads', exist_ok=True)
            file_path = f'/tmp/downloads/{filename}'

            logger.info(f"Downloading {filename} from {url}")

            downloaded = 0

            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"HTTP {response.status} error")
                    return None

                # If no content-length, try to get from response
                if not file_size:
                    file_size = int(response.headers.get('Content-Length', 0))

                with open(file_path, 'wb') as file:
                    async for chunk in response.content.iter_chunked(8192):
                        file.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and task_id:
                            await progress_callback(downloaded, file_size, task_id)

            logger.info(f"Successfully downloaded: {filename}")
            return file_path

        except Exception as e:
            logger.error(f"Direct download error: {e}")
            return None
        finally:
            await self.close_session()
