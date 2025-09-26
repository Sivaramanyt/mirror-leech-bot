import os
import aiohttp
import asyncio
import logging
from typing import Optional, Callable
from urllib.parse import quote
from utils.helpers import sanitize_filename, get_readable_file_size
import aiofiles
import math

logger = logging.getLogger(__name__)

class TeraboxDownloader:
    def __init__(self):
        self.session = None
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        self.api_url = "https://wdzone-terabox-api.vercel.app/api"
        self.max_connections = 6  # Parallel download connections
        self.chunk_size = 256 * 1024  # 256KB chunks (32x larger!)
    
    async def get_session(self):
        """Get or create ultra-optimized aiohttp session"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=20,           # Total connection pool size
                limit_per_host=8,   # Max connections per host
                ttl_dns_cache=300,  # DNS cache TTL
                use_dns_cache=True,
                tcp_nodelay=True,   # ⚡ Disable Nagle's algorithm for speed
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=600,      # 10 minutes total
                connect=30,     # 30s to connect  
                sock_read=60    # 1 minute read timeout
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive"
                }
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
            logger.info(f"🔍 Extracting info from URL: {url}")
            
            if "/file/" in url:
                logger.info("Direct file link detected")
                return {"single_url": url, "filename": "terabox_file.mp4"}
            
            api_request_url = f"{self.api_url}?url={quote(url)}"
            logger.info(f"📡 Calling API: {api_request_url}")
            
            session = await self.get_session()
            
            async with session.get(api_request_url) as response:
                logger.info(f"📊 API Response Status: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ API request failed with status {response.status}: {error_text}")
                    raise Exception(f"API request failed with status {response.status}: {error_text}")
                
                response_text = await response.text()
                logger.info(f"📋 API Response (first 200 chars): {response_text[:200]}...")
                
                req = await response.json()
                logger.info(f"🔍 API JSON keys: {list(req.keys())}")
            
            if "✅ Status" not in req:
                raise Exception(f"File not found in API response! API returned: {req}")
            
            if "📜 Extracted Info" not in req:
                raise Exception(f"No extracted info in API response! API returned: {req}")
                
            extracted_info = req["📜 Extracted Info"]
            logger.info(f"📊 Found {len(extracted_info)} files in API response")
            
            details = {"contents": [], "title": "", "total_size": 0}
            
            for i, data in enumerate(extracted_info):
                logger.info(f"🔍 Processing file {i+1}: {data.get('📂 Title', 'Unknown')}")
                
                original_filename = data.get("📂 Title", f"terabox_file_{i}")
                
                if not self.has_video_extension(original_filename):
                    original_filename += ".mp4"
                
                item = {
                    "path": "",
                    "filename": sanitize_filename(original_filename),
                    "url": data.get("🔽 Direct Download Link", ""),
                }
                details["contents"].append(item)
                logger.info(f"✅ Added file: {item['filename']} -> {item['url'][:50]}...")
            
            details["title"] = extracted_info[0].get("📂 Title", "Unknown")
            
            if len(details["contents"]) == 1:
                result = {
                    "single_url": details["contents"][0]["url"],
                    "filename": details["contents"][0]["filename"],
                    "title": details["title"]
                }
                logger.info(f"✅ Single file result: {result['filename']}")
                return result
            
            logger.info(f"✅ Multiple files result: {len(details['contents'])} files")
            return details
            
        except Exception as e:
            logger.error(f"❌ Error extracting Terabox info: {str(e)}")
            raise Exception(f"Terabox API error: {str(e)}")
    
    def has_video_extension(self, filename: str) -> bool:
        """Check if filename has video extension"""
        video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'}
        ext = os.path.splitext(filename.lower())[1]
        return ext in video_extensions
    
    async def get_file_size(self, url: str) -> int:
        """Get file size using HEAD request"""
        try:
            session = await self.get_session()
            async with session.head(url) as response:
                if response.status == 200:
                    return int(response.headers.get('content-length', 0))
                return 0
        except:
            return 0
    
    async def download_chunk(self, url: str, start: int, end: int, chunk_id: int, temp_dir: str):
        """Download a specific chunk of the file"""
        try:
            headers = {"Range": f"bytes={start}-{end}"}
            session = await self.get_session()
            
            async with session.get(url, headers=headers) as response:
                if response.status in [206, 200]:
                    chunk_data = await response.read()
                    
                    chunk_file = os.path.join(temp_dir, f"chunk_{chunk_id}")
                    async with aiofiles.open(chunk_file, 'wb') as f:
                        await f.write(chunk_data)
                    
                    return len(chunk_data)
                else:
                    logger.error(f"❌ Chunk {chunk_id} failed: HTTP {response.status}")
                    return 0
        except Exception as e:
            logger.error(f"❌ Chunk {chunk_id} error: {e}")
            return 0
    
    async def download_multi_connection(self, url: str, file_path: str, progress_callback: Optional[Callable] = None, task_id: str = None):
        """🚀 ULTRA-FAST multi-connection download"""
        try:
            total_size = await self.get_file_size(url)
            if total_size == 0:
                logger.warning("⚠️ Could not get file size, falling back to single connection")
                return await self.download_single_connection(url, file_path, progress_callback, task_id)
            
            logger.info(f"📦 File size: {get_readable_file_size(total_size)}")
            logger.info(f"🚀 Using {self.max_connections} PARALLEL connections for ULTRA-SPEED!")
            
            temp_dir = f"/tmp/chunks_{task_id}"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Calculate chunk ranges for parallel download
            chunk_size_bytes = total_size // self.max_connections
            chunk_ranges = []
            
            for i in range(self.max_connections):
                start = i * chunk_size_bytes
                if i == self.max_connections - 1:
                    end = total_size - 1
                else:
                    end = start + chunk_size_bytes - 1
                chunk_ranges.append((start, end, i))
            
            logger.info(f"📊 Created {len(chunk_ranges)} parallel chunks")
            
            # Download all chunks simultaneously
            download_tasks = []
            for start, end, chunk_id in chunk_ranges:
                task = self.download_chunk(url, start, end, chunk_id, temp_dir)
                download_tasks.append(task)
            
            # Progress tracking for parallel downloads
            async def track_progress():
                while True:
                    completed_files = [f for f in os.listdir(temp_dir) if f.startswith('chunk_')]
                    estimated_progress = len(completed_files) / len(chunk_ranges) * total_size
                    
                    if progress_callback and task_id:
                        try:
                            await progress_callback(int(estimated_progress), total_size, task_id)
                        except:
                            pass
                    
                    if len(completed_files) >= len(chunk_ranges):
                        break
                    await asyncio.sleep(2)
            
            # Start progress tracking
            progress_task = asyncio.create_task(track_progress())
            
            # Execute all downloads in parallel
            chunk_results = await asyncio.gather(*download_tasks, return_exceptions=True)
            progress_task.cancel()
            
            # Combine chunks into final file
            logger.info("🔗 Combining chunks at ULTRA-SPEED...")
            async with aiofiles.open(file_path, 'wb') as final_file:
                for i in range(len(chunk_ranges)):
                    chunk_file = os.path.join(temp_dir, f"chunk_{i}")
                    if os.path.exists(chunk_file):
                        async with aiofiles.open(chunk_file, 'rb') as cf:
                            chunk_data = await cf.read()
                            await final_file.write(chunk_data)
                        os.remove(chunk_file)
            
            # Clean up
            try:
                os.rmdir(temp_dir)
            except:
                pass
            
            final_size = os.path.getsize(file_path)
            logger.info(f"🚀 ULTRA-SPEED download complete: {get_readable_file_size(final_size)}")
            return file_path
                
        except Exception as e:
            logger.error(f"❌ Multi-connection download failed: {e}")
            return await self.download_single_connection(url, file_path, progress_callback, task_id)
    
    async def download_single_connection(self, url: str, file_path: str, progress_callback: Optional[Callable] = None, task_id: str = None):
        """Optimized single connection download with large chunks"""
        try:
            session = await self.get_session()
            logger.info(f"🌐 Starting OPTIMIZED single-connection download")
            
            async with session.get(url) as response:
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    logger.info(f"📦 File size: {get_readable_file_size(total_size)}")
                    
                    # 1MB buffer for maximum efficiency
                    buffer_size = 1024 * 1024
                    buffer_data = bytearray()
                    
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            buffer_data.extend(chunk)
                            downloaded += len(chunk)
                            
                            # Write buffer when full for efficiency
                            if len(buffer_data) >= buffer_size:
                                await f.write(buffer_data)
                                buffer_data.clear()
                            
                            if progress_callback and total_size > 0:
                                try:
                                    await progress_callback(downloaded, total_size, task_id)
                                except:
                                    pass
                        
                        # Write remaining buffer
                        if buffer_data:
                            await f.write(buffer_data)
                    
                    logger.info(f"✅ OPTIMIZED download complete: {get_readable_file_size(downloaded)}")
                    return file_path
                else:
                    raise Exception(f"Download failed: HTTP {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ Single-connection download error: {e}")
            raise e
    
    async def download(self, url: str, progress_callback: Optional[Callable] = None, task_id: str = None) -> Optional[str]:
        """🚀 ULTRA-HIGH-SPEED download with multi-connection support"""
        try:
            logger.info(f"🚀 Starting ULTRA-HIGH-SPEED Terabox download: {url}")
            
            file_info = await self.extract_file_info(url)
            
            if "single_url" in file_info:
                download_url = file_info["single_url"]
                filename = file_info["filename"]
            else:
                if not file_info["contents"]:
                    raise Exception("No files found")
                download_url = file_info["contents"][0]["url"]
                filename = file_info["contents"][0]["filename"]
            
            if not os.path.splitext(filename)[1]:
                filename += '.mp4'
            
            download_path = os.path.join('/tmp', filename)
            
            # Try multi-connection first for maximum speed
            try:
                return await self.download_multi_connection(download_url, download_path, progress_callback, task_id)
            except Exception as e:
                logger.warning(f"⚠️ Multi-connection failed, trying optimized single: {e}")
                return await self.download_single_connection(download_url, download_path, progress_callback, task_id)
                
        except Exception as e:
            logger.error(f"❌ Download error: {e}")
            raise e
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
            
