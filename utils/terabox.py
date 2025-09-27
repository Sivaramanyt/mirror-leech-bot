import os
import aiohttp
import asyncio
import logging
from typing import Optional, Callable
from urllib.parse import quote
import aiofiles
import random

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
        self.api_url = "https://wdzone-terabox-api.vercel.app/api"
        # HIGH SPEED: Larger chunks to reduce overhead
        self.chunk_size = 8 * 1024 * 1024  # 8MB chunks
        
        # ANTI-THROTTLING: Multiple user agents
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0 Safari/537.36"
        ]

    async def get_session(self):
        """Get HIGH-SPEED anti-throttling session"""
        if not self.session:
            # ANTI-THROTTLING: Aggressive settings
            connector = aiohttp.TCPConnector(
                limit=100,  # Maximum connections
                limit_per_host=30,  # High per-host connections
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True,
                keepalive_timeout=30,  # Shorter keepalive to avoid throttling
                force_close=False
            )
            
            # SPEED: Shorter timeouts for faster failure detection
            timeout = aiohttp.ClientTimeout(
                total=1200,  # 20 minutes
                connect=15,   # Fast connect
                sock_read=60  # Fast read
            )
            
            # ANTI-THROTTLING: Random user agent
            user_agent = random.choice(self.user_agents)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                    # ANTI-THROTTLING: Mimic real browser
                    "Cache-Control": "max-age=0",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none"
                }
            )
        return self.session

    async def extract_file_info(self, url: str) -> dict:
        """Extract file information - HIGH SPEED"""
        try:
            logger.info(f"🚀 HIGH-SPEED extraction: {url[:50]}...")
            
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
                
                logger.info(f"🚀 HIGH-SPEED file found: {filename}")
                return {
                    "success": True,
                    "filename": sanitize_filename(filename),
                    "download_url": download_url,
                    "title": filename
                }
                    
        except Exception as e:
            logger.error(f"❌ Extraction error: {e}")
            return {"success": False, "error": str(e)}

    async def download_high_speed(self, download_url: str, filename: str, progress_callback: Optional[Callable] = None, max_retries: int = 3) -> Optional[str]:
        """HIGH-SPEED download with anti-throttling"""
        download_path = os.path.join("/tmp", filename)
        
        for attempt in range(max_retries):
            try:
                # NEW SESSION FOR EACH ATTEMPT to avoid throttling
                if self.session:
                    await self.session.close()
                    self.session = None
                
                session = await self.get_session()
                
                logger.info(f"🚀 HIGH-SPEED attempt {attempt + 1}/{max_retries}: {filename}")
                
                # ANTI-THROTTLING: Add random delay
                if attempt > 0:
                    delay = random.uniform(1, 3)
                    await asyncio.sleep(delay)
                
                # ANTI-THROTTLING: Random headers for each attempt
                extra_headers = {
                    "Referer": random.choice([
                        "https://www.google.com/",
                        "https://terabox.com/",
                        "https://www.bing.com/"
                    ]),
                    "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                    "X-Real-IP": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
                }
                
                async with session.get(download_url, headers=extra_headers) as response:
                    if response.status not in [200, 206]:
                        raise Exception(f"HTTP {response.status}")
                    
                    total_size = int(response.headers.get('content-length', 0))
                    
                    logger.info(f"🚀 HIGH-SPEED mode: {filename}")
                    logger.info(f"📦 Size: {get_readable_file_size(total_size)}")
                    logger.info(f"⚡ Using 8MB chunks for maximum speed")
                    
                    downloaded = 0
                    start_time = asyncio.get_event_loop().time()
                    
                    async with aiofiles.open(download_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            if not chunk:
                                break
                            
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Progress every 16MB for speed
                            if progress_callback and downloaded % (16 * 1024 * 1024) < self.chunk_size:
                                try:
                                    elapsed = asyncio.get_event_loop().time() - start_time
                                    speed_mbps = (downloaded / (1024 * 1024)) / (elapsed / 60) if elapsed > 0 else 0
                                    await progress_callback(downloaded, max(total_size, downloaded), speed_mbps)
                                except:
                                    pass
                    
                    # Verify download
                    if os.path.exists(download_path):
                        actual_size = os.path.getsize(download_path)
                        elapsed = asyncio.get_event_loop().time() - start_time
                        final_speed = (actual_size / (1024 * 1024)) / (elapsed / 60) if elapsed > 0 else 0
                        
                        logger.info(f"🚀 HIGH-SPEED complete: {filename} ({get_readable_file_size(actual_size)}) - Speed: {final_speed:.1f} MB/min")
                        return download_path
                    else:
                        raise Exception("File not created")
                        
            except Exception as e:
                logger.error(f"❌ HIGH-SPEED attempt {attempt + 1} failed: {e}")
                
                # Clean up partial file
                try:
                    if os.path.exists(download_path):
                        os.remove(download_path)
                except:
                    pass
                
                if attempt == max_retries - 1:
                    return None
                else:
                    # Exponential backoff with randomization
                    wait_time = (attempt + 1) * 2 + random.uniform(1, 3)
                    logger.info(f"⏳ Retrying in {wait_time:.1f}s...")
                    await asyncio.sleep(wait_time)
        
        return None

    async def download_file(self, url: str, progress_callback: Optional[Callable] = None) -> Optional[str]:
        """HIGH-SPEED download entry point"""
        try:
            logger.info(f"🚀 HIGH-SPEED download starting: {url[:50]}...")
            
            # Get file info
            file_info = await self.extract_file_info(url)
            if not file_info.get("success"):
                raise Exception(file_info.get("error", "File info failed"))
            
            download_url = file_info["download_url"]
            filename = file_info["filename"]
            
            if not download_url:
                raise Exception("No download URL")
            
            # HIGH-SPEED download with anti-throttling
            result = await self.download_high_speed(download_url, filename, progress_callback)
            return result
                    
        except Exception as e:
            logger.error(f"❌ HIGH-SPEED download error: {e}")
            return None

    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            self.session = None

# Global instance
terabox_downloader = TeraboxDownloader()
    
