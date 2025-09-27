import os
import aiohttp
import asyncio
import logging
from typing import Optional, Callable
from urllib.parse import quote
import aiofiles
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

def sanitize_filename(filename: str) -> str:
    """Simple filename sanitization"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:250]

def get_readable_file_size(size_bytes: int) -> str:
    """Convert bytes to readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

class TeraboxDownloader:
    def __init__(self):
        self.session = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        self.api_url = "https://wdzone-terabox-api.vercel.app/api"
        # MAXIMUM SPEED: Huge chunks for parallel download
        self.chunk_size = 16 * 1024 * 1024  # 16MB chunks (2x larger!)
        self.max_parallel_chunks = 4  # Download 4 chunks simultaneously

    async def get_session(self):
        """Get HIGH-PERFORMANCE session with maximum connections"""
        if not self.session:
            # MAXIMUM PERFORMANCE: Aggressive connection settings
            connector = aiohttp.TCPConnector(
                limit=100,  # Maximum connections (was 50)
                limit_per_host=50,  # Maximum per host (was 20)
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True,
                keepalive_timeout=120,  # Longer keepalive
                force_close=False
            )
            
            # SPEED OPTIMIZED: Even faster timeouts
            timeout = aiohttp.ClientTimeout(
                total=1800,  # 30 minutes
                connect=5,   # Ultra-fast connect (was 15)
                sock_read=30  # Very fast read (was 60)
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept-Encoding": "identity",  # No compression for max speed
                    "Connection": "keep-alive",
                    "Cache-Control": "no-cache"
                }
            )
        return self.session

    async def extract_file_info(self, url: str) -> dict:
        """Extract file information - MAXIMUM SPEED"""
        try:
            logger.info(f"🚀 MAXIMUM SPEED extraction: {url[:50]}...")
            
            api_request_url = f"{self.api_url}?url={quote(url)}"
            session = await self.get_session()
            
            async with session.get(api_request_url) as response:
                if response.status != 200:
                    raise Exception(f"API failed: {response.status}")
                
                req = await response.json()
                
                if "✅ Status" not in req or "📜 Extracted Info" not in req:
                    raise Exception("Invalid API response")
                
                extracted_info = req["📜 Extracted Info"]
                if not extracted_info:
                    raise Exception("No files found")
                
                data = extracted_info[0]
                filename = data.get("📂 Title", "terabox_file")
                download_url = data.get("🔽 Direct Download Link", "")
                
                if not os.path.splitext(filename)[1]:
                    filename += ".mp4"
                
                logger.info(f"🚀 MAXIMUM SPEED file found: {filename}")
                return {
                    "success": True,
                    "filename": sanitize_filename(filename),
                    "download_url": download_url,
                    "title": filename
                }
                    
        except Exception as e:
            logger.error(f"❌ Extraction error: {e}")
            return {"success": False, "error": str(e)}

    async def download_chunk_parallel(self, session, url: str, start: int, end: int, chunk_id: int) -> bytes:
        """Download a single chunk in parallel - MAXIMUM SPEED"""
        headers = {
            "Range": f"bytes={start}-{end}",
            "Accept": "*/*",
            "Connection": "keep-alive"
        }
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status in [200, 206]:
                    data = await response.read()
                    logger.info(f"🚀 Chunk {chunk_id} complete: {len(data)} bytes")
                    return data
                else:
                    raise Exception(f"Chunk {chunk_id} failed: HTTP {response.status}")
        except Exception as e:
            logger.error(f"❌ Chunk {chunk_id} error: {e}")
            raise

    async def download_file_parallel(self, download_url: str, filename: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """MAXIMUM SPEED parallel download with multiple connections"""
        download_path = os.path.join("/tmp", filename)
        
        try:
            session = await self.get_session()
            
            # Get file size first
            async with session.head(download_url) as response:
                if response.status != 200:
                    raise Exception(f"HEAD request failed: {response.status}")
                
                total_size = int(response.headers.get('content-length', 0))
                if total_size == 0:
                    raise Exception("Cannot determine file size")
                
                # Check if server supports range requests
                accept_ranges = response.headers.get('accept-ranges', '').lower()
                supports_ranges = 'bytes' in accept_ranges
                
                logger.info(f"🚀 MAXIMUM SPEED mode: {filename}")
                logger.info(f"📦 Size: {get_readable_file_size(total_size)}")
                logger.info(f"⚡ Parallel chunks: {'YES' if supports_ranges else 'NO'}")
                
                if supports_ranges and total_size > self.chunk_size:
                    # PARALLEL DOWNLOAD - Multiple chunks simultaneously
                    return await self._parallel_download(session, download_url, filename, total_size, progress_callback)
                else:
                    # SINGLE THREAD - But optimized
                    return await self._single_thread_download(session, download_url, filename, total_size, progress_callback)
                    
        except Exception as e:
            logger.error(f"❌ Parallel download setup failed: {e}")
            return None

    async def _parallel_download(self, session, download_url: str, filename: str, total_size: int, progress_callback):
        """Multi-threaded parallel download - MAXIMUM SPEED"""
        download_path = os.path.join("/tmp", filename)
        
        # Calculate chunk ranges
        chunk_size = self.chunk_size
        chunks = []
        for i in range(0, total_size, chunk_size):
            start = i
            end = min(i + chunk_size - 1, total_size - 1)
            chunks.append((start, end, len(chunks)))
        
        logger.info(f"🚀 MAXIMUM SPEED: {len(chunks)} parallel chunks of {chunk_size // (1024*1024)}MB")
        
        downloaded_chunks = {}
        downloaded_size = 0
        start_time = asyncio.get_event_loop().time()
        
        # Progress tracking
        async def update_progress():
            if progress_callback and total_size > 0:
                try:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    speed_mbps = (downloaded_size / (1024 * 1024)) / (elapsed / 60) if elapsed > 0 else 0
                    await progress_callback(downloaded_size, total_size, speed_mbps)
                except:
                    pass
        
        # Download chunks in batches of max_parallel_chunks
        for i in range(0, len(chunks), self.max_parallel_chunks):
            batch = chunks[i:i+self.max_parallel_chunks]
            
            # Download batch in parallel
            tasks = []
            for start, end, chunk_id in batch:
                task = self.download_chunk_parallel(session, download_url, start, end, chunk_id)
                tasks.append((task, chunk_id, start, end))
            
            # Wait for batch completion
            results = await asyncio.gather(*[task[0] for task in tasks], return_exceptions=True)
            
            # Process results
            for result, (_, chunk_id, start, end) in zip(results, tasks):
                if isinstance(result, Exception):
                    raise result
                
                downloaded_chunks[chunk_id] = result
                downloaded_size += len(result)
                
                # Update progress every few chunks
                if len(downloaded_chunks) % 2 == 0:
                    await update_progress()
        
        # Write chunks to file in order
        async with aiofiles.open(download_path, 'wb') as f:
            for i in range(len(chunks)):
                if i in downloaded_chunks:
                    await f.write(downloaded_chunks[i])
                else:
                    raise Exception(f"Missing chunk {i}")
        
        # Final speed calculation
        elapsed = asyncio.get_event_loop().time() - start_time
        final_speed = (total_size / (1024 * 1024)) / (elapsed / 60) if elapsed > 0 else 0
        
        logger.info(f"🚀 MAXIMUM SPEED complete: {filename} - {final_speed:.1f} MB/min")
        return download_path

    async def _single_thread_download(self, session, download_url: str, filename: str, total_size: int, progress_callback):
        """Single-thread but MAXIMUM optimized download"""
        download_path = os.path.join("/tmp", filename)
        
        logger.info(f"⚡ OPTIMIZED single-thread: {filename}")
        
        async with session.get(download_url) as response:
            if response.status != 200:
                raise Exception(f"Download failed: HTTP {response.status}")
            
            downloaded = 0
            start_time = asyncio.get_event_loop().time()
            
            async with aiofiles.open(download_path, 'wb') as f:
                async for chunk in response.content.iter_chunked(self.chunk_size):
                    if not chunk:
                        break
                    
                    await f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Progress every 20MB
                    if progress_callback and downloaded % (20 * 1024 * 1024) < self.chunk_size:
                        try:
                            elapsed = asyncio.get_event_loop().time() - start_time
                            speed_mbps = (downloaded / (1024 * 1024)) / (elapsed / 60) if elapsed > 0 else 0
                            await progress_callback(downloaded, total_size, speed_mbps)
                        except:
                            pass
            
            elapsed = asyncio.get_event_loop().time() - start_time
            final_speed = (total_size / (1024 * 1024)) / (elapsed / 60) if elapsed > 0 else 0
            logger.info(f"⚡ OPTIMIZED download complete: {filename} - {final_speed:.1f} MB/min")
            
        return download_path

    async def download_file(self, url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """MAXIMUM SPEED download entry point"""
        try:
            logger.info(f"🚀 MAXIMUM SPEED download starting: {url[:50]}...")
            
            # Get file info
            file_info = await self.extract_file_info(url)
            if not file_info.get("success"):
                raise Exception(file_info.get("error", "File info failed"))
            
            download_url = file_info["download_url"]
            filename = file_info["filename"]
            
            if not download_url:
                raise Exception("No download URL")
            
            # MAXIMUM SPEED download
            result = await self.download_file_parallel(download_url, filename, progress_callback)
            return result
                    
        except Exception as e:
            logger.error(f"❌ MAXIMUM SPEED download error: {e}")
            return None

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None

# Global instance
terabox_downloader = TeraboxDownloader()
                    
