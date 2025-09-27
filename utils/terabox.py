import os
import aiohttp
import asyncio
import logging
from typing import Optional, Callable
from urllib.parse import quote
import aiofiles

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
        # BULLETPROOF: Smaller chunks for reliability
        self.chunk_size = 4 * 1024 * 1024  # 4MB chunks (more reliable)

    async def get_session(self):
        """Get BULLETPROOF session"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=20,  # Fewer connections for stability
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True,
                keepalive_timeout=60,
                force_close=False
            )
            
            # BULLETPROOF: Longer timeouts
            timeout = aiohttp.ClientTimeout(
                total=1800,  # 30 minutes
                connect=30,   # Longer connect
                sock_read=120  # Longer read per chunk
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "*/*",
                    "Connection": "keep-alive"
                }
            )
        return self.session

    async def extract_file_info(self, url: str) -> dict:
        """Extract file information"""
        try:
            logger.info(f"🔍 Extracting info: {url[:50]}...")
            
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
                
                logger.info(f"✅ File found: {filename}")
                return {
                    "success": True,
                    "filename": sanitize_filename(filename),
                    "download_url": download_url,
                    "title": filename
                }
                    
        except Exception as e:
            logger.error(f"❌ Extraction error: {e}")
            return {"success": False, "error": str(e)}

    async def download_with_resume(self, download_url: str, filename: str, progress_callback: Optional[Callable] = None, max_retries: int = 5) -> Optional[str]:
        """BULLETPROOF download with resume capability"""
        download_path = os.path.join("/tmp", filename)
        
        for attempt in range(max_retries):
            try:
                session = await self.get_session()
                
                # Check if partial file exists
                resume_pos = 0
                if os.path.exists(download_path):
                    resume_pos = os.path.getsize(download_path)
                    logger.info(f"🔄 Resume from {get_readable_file_size(resume_pos)}")
                
                # Set range header for resume
                headers = {}
                if resume_pos > 0:
                    headers["Range"] = f"bytes={resume_pos}-"
                
                logger.info(f"🚀 BULLETPROOF attempt {attempt + 1}/{max_retries}: {filename}")
                
                async with session.get(download_url, headers=headers) as response:
                    if response.status not in [200, 206]:  # 206 for partial content
                        if resume_pos > 0 and response.status == 416:  # Range not satisfiable
                            logger.info("✅ File already complete!")
                            return download_path
                        raise Exception(f"HTTP {response.status}")
                    
                    # Get total size
                    if response.status == 200:
                        total_size = int(response.headers.get('content-length', 0))
                    else:  # 206 partial content
                        content_range = response.headers.get('content-range', '')
                        if '/' in content_range:
                            total_size = int(content_range.split('/')[-1])
                        else:
                            total_size = resume_pos + int(response.headers.get('content-length', 0))
                    
                    logger.info(f"📦 Total size: {get_readable_file_size(total_size)}")
                    logger.info(f"⚡ Using 4MB chunks for reliability")
                    
                    downloaded = resume_pos
                    start_time = asyncio.get_event_loop().time()
                    
                    # Open file in append mode if resuming, write mode if new
                    file_mode = 'ab' if resume_pos > 0 else 'wb'
                    
                    async with aiofiles.open(download_path, file_mode) as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            if not chunk:
                                break
                            
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Progress every 8MB
                            if progress_callback and downloaded % (8 * 1024 * 1024) < self.chunk_size:
                                try:
                                    elapsed = asyncio.get_event_loop().time() - start_time
                                    speed_mbps = ((downloaded - resume_pos) / (1024 * 1024)) / (elapsed / 60) if elapsed > 0 else 0
                                    await progress_callback(downloaded, total_size, speed_mbps)
                                except:
                                    pass
                    
                    # Verify download
                    if os.path.exists(download_path):
                        actual_size = os.path.getsize(download_path)
                        if total_size > 0 and actual_size >= total_size * 0.98:  # 98% tolerance
                            elapsed = asyncio.get_event_loop().time() - start_time
                            final_speed = ((downloaded - resume_pos) / (1024 * 1024)) / (elapsed / 60) if elapsed > 0 else 0
                            logger.info(f"✅ BULLETPROOF complete: {filename} - Speed: {final_speed:.1f} MB/min")
                            return download_path
                        else:
                            logger.warning(f"⚠️ Partial download: {actual_size}/{total_size}")
                            continue  # Retry
                    else:
                        raise Exception("File not created")
                        
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} failed: {e}")
                
                if attempt == max_retries - 1:
                    # Last attempt - clean up partial file
                    try:
                        if os.path.exists(download_path):
                            os.remove(download_path)
                    except:
                        pass
                    return None
                else:
                    # Wait before retry (exponential backoff)
                    wait_time = (attempt + 1) * 3  # 3, 6, 9, 12 seconds
                    logger.info(f"⏳ Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        
        return None

    async def download_file(self, url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """BULLETPROOF download entry point"""
        try:
            logger.info(f"🚀 BULLETPROOF download starting: {url[:50]}...")
            
            # Get file info
            file_info = await self.extract_file_info(url)
            if not file_info.get("success"):
                raise Exception(file_info.get("error", "File info failed"))
            
            download_url = file_info["download_url"]
            filename = file_info["filename"]
            
            if not download_url:
                raise Exception("No download URL")
            
            # BULLETPROOF download with resume
            result = await self.download_with_resume(download_url, filename, progress_callback)
            return result
                    
        except Exception as e:
            logger.error(f"❌ BULLETPROOF download error: {e}")
            return None

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None

# Global instance
terabox_downloader = TeraboxDownloader()
                
